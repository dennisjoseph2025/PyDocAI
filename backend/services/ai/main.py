import os
import re
import uuid
import json
import tempfile
import shutil
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, engine, Base, create_tables
from models import Project, ProjectFile
from rag import embed_and_store_chunks, retrieve_context, store_generated_doc

create_tables()

app = FastAPI(title="PyDocAI AI Generator Service", version="0.2.0")

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
api_key_header = APIKeyHeader(name="X-Internal-Api-Key", auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_internal_key(key: str = Depends(api_key_header)):
    if INTERNAL_API_KEY and key != INTERNAL_API_KEY:
        raise HTTPException(401, "Invalid or missing internal API key")
    return key

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2")


class GenerateRequest(BaseModel):
    project_id: str
    file_path: Optional[str] = None
    use_ai: bool = True


class GenerateResponse(BaseModel):
    project_id: str
    status: str
    generated_docs: Optional[str] = None
    readme_docs: Optional[str] = None
    api_docs: Optional[str] = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai",
        "groq_configured": bool(GROQ_API_KEY),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
    }


def _sanitize_markdown(text: str) -> str:
    if not text:
        return text
    text = re.sub(r'(^|\n)mermaid\s*\n', r'\1```mermaid\n', text)
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```mermaid"):
            result.append(line)
            i += 1
            while i < len(lines):
                if lines[i].strip() == "```":
                    result.append(lines[i])
                    i += 1
                    break
                elif lines[i].startswith("```mermaid"):
                    result.append("```")
                    break
                elif lines[i].startswith("##") or lines[i].startswith("# "):
                    result.append("```")
                    result.append(lines[i])
                    i += 1
                    break
                else:
                    result.append(lines[i])
                    i += 1
            else:
                result.append("```")
        else:
            result.append(lines[i])
            i += 1
    text = "\n".join(result)
    text = re.sub(r'\bcode\s*\n\s*Copy\s*\n\s*python\s*\n', '```python\n', text)
    text = re.sub(r'\bcode\s*\n\s*Copy\s*\n\s*(\w+)\s*\n', r'```\1\n', text)
    text = re.sub(r'\bcode\s*\n\s*Copy\s*\n', '```\n', text)
    text = re.sub(r'\n\s*```\s*\n\s*```\s*\n', '\n```\n', text)
    text = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', text)
    text = re.sub(r'(#{1,6} .+)\n([^\n#])', r'\1\n\n\2', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _call_groq(prompt: str, max_tokens: int = 2048, key_start: int = 0, model: str = "llama-3.1-8b-instant") -> str:
    import time
    from groq import Groq
    key_pool = []
    if GROQ_API_KEY:
        key_pool.append(("key1", GROQ_API_KEY))
    if GROQ_API_KEY_2:
        key_pool.append(("key2", GROQ_API_KEY_2))
    if not key_pool:
        raise HTTPException(503, "No Groq API keys configured")
    keys_to_try = key_pool[key_start:] + key_pool[:key_start]
    print(f"[_call_groq] Keys available: {len(key_pool)}, start={key_start}, order={[k[0] for k in keys_to_try]}", flush=True)
    for name, key in keys_to_try:
        for attempt in range(3):
            try:
                client = Groq(api_key=key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                result = response.choices[0].message.content.strip()
                if result.startswith("```"):
                    result = result.split("```", 2)[-1].strip()
                    if result.endswith("```"):
                        result = result[:-3].strip()
                print(f"[_call_groq] {name}: OK ({len(result)} chars)", flush=True)
                return result
            except Exception as e:
                status_code = getattr(e, 'status_code', 0) or getattr(e, 'status', 0)
                body = getattr(e, 'body', '') or (str(e.args) if e.args else str(e))[:200]
                if status_code in (401, 403):
                    print(f"[_call_groq] {name}: auth error ({status_code}) {body}, skipping key", flush=True)
                    break
                if status_code == 429:
                    print(f"[_call_groq] {name}: rate limited (429) {body}, trying next key", flush=True)
                    break
                wait = 2 ** attempt
                print(f"[_call_groq] {name}: attempt {attempt+1} FAILED (HTTP {status_code}) {body}, retrying in {wait}s", flush=True)
                time.sleep(wait)
                continue
    raise HTTPException(503, "All Groq API keys failed")


def _build_structure_tree(ordered_items: list) -> str:
    lines = []
    for item in ordered_items:
        typ = item["type"]
        data = item["data"]
        prefix = "├── " if item != ordered_items[-1] else "└── "
        if typ == "import":
            lines.append(f"{prefix}[Import] {data.get('display', '')}")
        elif typ == "function":
            args = ", ".join(a["name"] for a in data.get("args", []))
            lines.append(f"{prefix}[Function] {data['name']}({args}) -> {data.get('returns', 'None')}")
        elif typ == "class":
            bases = ", ".join(data.get("bases", []))
            base_str = f"({bases})" if bases else ""
            lines.append(f"{prefix}[Class] {data['name']}{base_str}")
            for i, m in enumerate(data.get("methods", [])):
                m_prefix = "    ├── " if i < len(data["methods"]) - 1 else "    └── "
                m_args = ", ".join(a["name"] for a in m.get("args", []))
                lines.append(f"{m_prefix}{m['name']}({m_args})")
    return "\n".join(lines)


def get_item_docs_prompt(item_type: str, data: dict, file_path: str, is_pattern: bool = False) -> str:
    if item_type == "function":
        args_table = "| Parameter | Type | Description | Default | Constraints |\n|---|---|---|---|---|\n"
        for a in data.get("args", []):
            args_table += f"| {a['name']} | {a['type'] or 'Any'} | ... | ... | ... |\n"
        connections = data.get("connections", [])
        conn_str = ", ".join(connections) if connections else "None"

        if is_pattern:
            return f"""This function follows the same pattern as other functions in this project.
Write a SHORT, differential doc focusing only on what makes THIS one unique.

Function: `{data['name']}`
File: `{file_path}`
Line: {data.get('line', '?')}
Async: {data.get('is_async', False)}
Decorators: {', '.join(data.get('decorators', [])) or 'None'}
Parameters:
{args_table}
Returns: `{data.get('returns', 'None')}`
Calls/References: {conn_str}

Provide ONLY:
- ### Purpose (1 sentence)
- ### Unique behavior (what differs from the pattern)
- ### Parameters table (just name and type)
- ### Returns (1 line)

Output in clean markdown with headings. Keep it short."""
        return f"""Document the following Python function in detail using markdown.

Function: `{data['name']}`
File: `{file_path}`
Line: {data.get('line', '?')}
Async: {data.get('is_async', False)}
Decorators: {', '.join(data.get('decorators', [])) or 'None'}
Parameters:
{args_table}
Returns: `{data.get('returns', 'None')}`
Calls/References: {conn_str}

Provide:
- ### Purpose (2-3 sentences)
- ### Behavior (step-by-step)
- ### Parameters table (Parameter | Type | Description | Default | Constraints)
- ### Returns (type, description, possible values)
- ### Raises (all exceptions that can be raised)
- ### Relationships (Calls, Called By, Uses)
- ### Example Usage (Input/Output)
- ### Edge Cases
- ### Complexity (Big O)

Output in clean markdown with headings."""
    elif item_type == "class":
        methods_str = ""
        for m in data.get("methods", []):
            m_args = ", ".join(a["name"] for a in m.get("args", []))
            methods_str += f"- `{m['name']}({m_args}) -> {m.get('returns', 'None')}` (line {m.get('line', '?')})\n"
        connections = data.get("connections", [])
        conn_str = ", ".join(connections) if connections else "None"

        if is_pattern:
            return f"""This class follows the same pattern as other classes in this project.
Write a SHORT, differential doc focusing only on what makes THIS one unique.

Class: `{data['name']}`
File: `{file_path}`
Line: {data.get('line', '?')}
Bases: {', '.join(data.get('bases', [])) or 'None'}
Methods:
{methods_str}
Uses/References: {conn_str}

Provide ONLY:
- ### Purpose (1 sentence)
- ### Unique behavior (what differs from the pattern)
- ### Attributes table (just name and type)
- ### Methods (1 line summary per method)

Output in clean markdown with headings. Keep it short."""
        return f"""Document the following Python class in detail using markdown.

Class: `{data['name']}`
File: `{file_path}`
Line: {data.get('line', '?')}
Bases: {', '.join(data.get('bases', [])) or 'None'}
Methods:
{methods_str}
Uses/References: {conn_str}

Provide:
- ### Purpose (2-3 sentences)
- ### Attributes table (Attribute | Type | Description | Default)
- ### Methods (for each: purpose, parameters, returns, example)
- ### Inherits from (bases, inherited methods)
- ### Usage Example
- ### Relationships to other classes

Output in clean markdown with headings."""
    return ""


def generate_file_docs(parsed: dict, file_path: str, framework_info: Optional[dict] = None, db: Session = None, project_id: str = None) -> str:
    ordered_items = parsed.get("ordered_items", [])
    module_doc = parsed.get("module_docstring") or "No module docstring"
    imports = parsed.get("imports", [])

    import_displays = []
    for imp in imports:
        if isinstance(imp, dict):
            import_displays.append(imp.get("display", str(imp)))
        else:
            import_displays.append(str(imp))

    structure_tree = _build_structure_tree(ordered_items)

    fw_header = ""
    fw_instructions = ""
    if framework_info and framework_info.get("primary_framework"):
        fw = framework_info["primary_framework"]
        fw_header = f"\nFramework: {fw}\n"
        fw_type = framework_info.get("primary_type", "")
        if fw_type == "web":
            fw_instructions = "\nSpecial instructions: When documenting Python web framework code, include details about routes, middleware, request/response handling, and dependency injection where applicable."
        elif fw_type == "task_queue":
            fw_instructions = "\nSpecial instructions: When documenting task queue code, include details about task signatures, queues, retries, and result backends where applicable."
        elif fw_type == "orm":
            fw_instructions = "\nSpecial instructions: When documenting ORM code, include details about model definitions, relationships, sessions, and query patterns where applicable."
        elif fw_type == "ai":
            fw_instructions = "\nSpecial instructions: When documenting AI/LLM code, include details about model configuration, prompts, streaming, and error handling where applicable."



    rag_context = ""
    if db and project_id:
        try:
            rag_context, _ = retrieve_context(project_id, f"Module overview of {file_path}: {module_doc}", top_k=3, db=db)
        except Exception:
            pass

    rag_block = f"\n\nRelevant code context from project:\n{rag_context}\n\n---\n" if rag_context else ""

    overview_prompt = f"""{rag_block}
Generate the beginning sections for the Python file {file_path}.{fw_header}
Module docstring: {module_doc}
Imports: {', '.join(import_displays)}

Output ONLY the following sections in markdown (nothing else):

# {file_path}

## Overview
3-5 detailed paragraphs on what this module does, its purpose, architecture, and key components. Include a mermaid flowchart showing the module architecture and data flow.

## Code Structure (Source Order)
Paste the structure tree below EXACTLY as shown:

{structure_tree}

## Imports
For each import, provide a DETAILED table row with ALL columns:
| Import | Purpose | Where Used | Notes |
|--------|---------|----------|-------|
| ... | ... | ... | ... |

## Notes
Any additional observations about the module.
"""
    overview_docs = _call_groq(overview_prompt, max_tokens=2048, key_start=0)

    item_docs = []
    for i, item in enumerate(ordered_items):
        typ = item["type"]
        data = item["data"]
        if typ == "import":
            continue
        elif typ in ("function", "class"):
            item_prompt = get_item_docs_prompt(typ, data, file_path)
            if db and project_id:
                try:
                    item_rag, is_pattern = retrieve_context(
                        project_id, f"{typ}: {data.get('name', '')} in {file_path}", top_k=3, db=db
                    )
                    if item_rag:
                        item_prompt = get_item_docs_prompt(typ, data, file_path, is_pattern=is_pattern)
                        item_prompt = f"Relevant code context from project:\n{item_rag}\n\n---\n\n" + item_prompt
                except Exception:
                    pass
            docs = _call_groq(item_prompt, max_tokens=2048, key_start=(i + 1) % 2)
            item_docs.append(docs)
            if db and project_id and docs:
                try:
                    store_generated_doc(project_id, typ, data["name"], file_path, docs, db)
                except Exception:
                    pass

    result = overview_docs + "\n\n"
    result += "## Detailed Documentation (IN SOURCE ORDER)\n\n"
    result += "\n\n---\n\n".join(item_docs)
    result += "\n\n## End of Documentation"

    return result.strip()


def _mock_docs(parsed: dict, file_path: str, _framework_info: Optional[dict] = None) -> str:
    imports = parsed.get("imports", [])
    ordered = parsed.get("ordered_items", [])

    import_lines = []
    for imp in imports:
        if isinstance(imp, dict):
            import_lines.append(f'- `{imp.get("display", str(imp))}` (line {imp.get("line", "?")})')
        else:
            import_lines.append(f"- `{imp}`")

    doc_sections = []
    for item in ordered:
        typ = item["type"]
        data = item["data"]
        if typ == "import":
            pass
        elif typ == "function":
            args = ", ".join(a["name"] for a in data.get("args", []))
            returns = data.get("returns") or "None"
            line = data.get("line", "?")
            connections = data.get("connections", [])
            conn_str = f" (calls: {', '.join(connections)})" if connections else ""
            doc_sections.append(
                f'### `{data["name"]}({args}) -> {returns}`\n'
                f'- **Line:** {line}{conn_str}\n'
                f'- **Purpose:** Mock documentation'
            )
        elif typ == "class":
            line = data.get("line", "?")
            bases = ", ".join(data.get("bases", []))
            base_str = f"({bases})" if bases else ""
            connections = data.get("connections", [])
            conn_str = f" (uses: {', '.join(connections)})" if connections else ""
            doc_sections.append(
                f'### `{data["name"]}{base_str}`\n'
                f'- **Line:** {line}{conn_str}\n'
                f'- **Methods:** {", ".join(m["name"] for m in data.get("methods", []))}'
            )

    return f"""# {file_path}

## Overview
Mock documentation generated for development purposes. This shows how the documentation will be structured with source order preserved.

## Imports
{chr(10).join(import_lines) or 'No imports'}

## Detailed Documentation (IN SOURCE ORDER)

{chr(10).join(doc_sections) or 'No functions or classes'}

> ⚠️ This is mock documentation. Configure GROQ_API_KEY to generate real AI-powered docs.
"""


def _retrieve_project_context(project_id: str, project_name: str, db: Session) -> str:
    try:
        rag_text, _ = retrieve_context(
            project_id,
            f"Project {project_name}: architecture, components, data flow, dependencies",
            top_k=5,
            db=db,
        )
        if rag_text:
            return rag_text
        return "No additional code context available."
    except Exception:
        return "No additional code context available."


def generate_project_summary(project_path: str, project_name: str = None) -> dict:
    summary = {
        "name": project_name or os.path.basename(project_path),
        "framework": "python",
        "architecture": "monolith",
        "apps": [],
        "dependencies": [],
        "file_count": 0,
        "project_tree": "",
        "package_manager": "pip",
    }

    # Detect package manager from project root files
    root_contents = set(os.listdir(project_path))
    if "uv.lock" in root_contents or "uv.toml" in root_contents:
        summary["package_manager"] = "uv"
    elif "poetry.lock" in root_contents:
        summary["package_manager"] = "poetry"
    elif "Pipfile" in root_contents:
        summary["package_manager"] = "pipenv"
    elif "pyproject.toml" in root_contents:
        summary["package_manager"] = "pip"
    else:
        summary["package_manager"] = "pip"

    dir_map = {}
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in {
            "venv", ".venv", "__pycache__", "node_modules",
            "migrations", ".git", "build", "dist", ".egg-info"
        }]
        rel_dir = os.path.relpath(root, project_path)
        if rel_dir == ".":
            rel_dir = ""
        for f in files:
            if f.endswith(".py"):
                dir_map.setdefault(rel_dir, []).append(f)

    summary["file_count"] = sum(len(v) for v in dir_map.values())

    # Build a proper nested tree from directory map
    def _build_tree(dir_map):
        root = {}
        for dir_path, files in dir_map.items():
            if not dir_path:
                continue
            parts = dir_path.replace("\\", "/").split("/")
            node = root
            for p in parts:
                node = node.setdefault(p, {})
            node["__files__"] = files
        return root

    def _render_tree(node, prefix="", is_last=True):
        lines = []
        items = list(node.items())
        items.sort(key=lambda x: (x[0] == "__files__", x[0]))
        for i, (key, val) in enumerate(items):
            if key == "__files__":
                files = sorted(val)
                for fi, f in enumerate(files):
                    conn = "└── " if fi == len(files) - 1 else "├── "
                    lines.append(f"{prefix}{conn}{f}")
            else:
                conn = "└── " if i == len(items) - 1 else "├── "
                lines.append(f"{prefix}{conn}{key}/")
                ext = "    " if i == len(items) - 1 else "│   "
                sub_lines = _render_tree(val, prefix + ext, i == len(items) - 1)
                lines.extend(sub_lines)
        return lines

    tree = _build_tree(dir_map)
    tree_lines = []
    # Only use top-level dirs as roots (skip files at repo root)
    top_dirs = sorted(k for k in tree if k != "__files__")
    for ti, td in enumerate(top_dirs):
        tree_lines.append(f"{td}/")
        sub = _render_tree(tree[td], "", ti == len(top_dirs) - 1)
        tree_lines.extend(sub)
    summary["project_tree"] = "\n".join(tree_lines)

    for root, dirs, files in os.walk(project_path):
        rel = os.path.relpath(root, project_path)
        if rel == ".":
            continue
        if "apps.py" in files or "models.py" in files:
            summary["apps"].append(rel.replace(os.sep, "."))

    req_files = ["requirements.txt", "pyproject.toml", "Pipfile"]
    for rf in req_files:
        rpath = os.path.join(project_path, rf)
        if os.path.exists(rpath):
            with open(rpath) as f:
                summary["dependencies"] = f.read().splitlines()
            break

    return summary


def _postman_body_example(route: str) -> str:
    examples = {
        "register": '\n\n{\n  "username": "johndoe",\n  "email": "john@example.com",\n  "password": "********"\n}',
        "login": '\n\n{\n  "username": "johndoe",\n  "password": "********"\n}',
        "change-password": '\n\n{\n  "old_password": "********",\n  "new_password": "********"\n}',
        "password-reset": '\n\n{\n  "email": "john@example.com"\n}',
        "password-reset/confirm": '\n\n{\n  "token": "...",\n  "new_password": "********"\n}',
        "import": '\n\n{\n  "repo_url": "https://github.com/user/repo"\n}',
        "folder": '\n\n{\n  "folder_path": "src/"\n}',
        "file": '\n\n{\n  "file_path": "src/main.py",\n  "content": "# code here"\n}',
        "auth/github": '\n\n{\n  "code": "github_oauth_code"\n}',
    }
    for key, body in examples.items():
        if key in route:
            return body
    return '\n\n{\n  \n}'


def _build_api_docs(files: list) -> str:
    import re as _re
    view_routes = {}
    url_prefixes = {}  # file → prefix from include()

    # First pass: collect include() prefixes
    for f in files:
        if f.file_path.endswith("urls.py") and f.content:
            for m in _re.finditer(
                r"(?:path|re_path)\(\s*(['\"])(.+?)\1\s*,\s*include\((['\"])(.+?)\3\)",
                f.content,
            ):
                route, included = m.group(2), m.group(4)
                included_path = included.replace(".urls", "").replace(".", "/")
                url_prefixes[included_path] = route

    # Second pass: extract view → route mappings
    for f in files:
        if f.file_path.endswith("urls.py") and f.content:
            # Determine prefix from include() parent
            file_key = f.file_path.replace("\\", "/")
            parts = file_key.split("/")
            prefix = ""
            for p in range(len(parts)):
                candidate = "/".join(parts[p:]).replace("/urls.py", "").replace(".", "/")
                if candidate in url_prefixes:
                    prefix = url_prefixes[candidate]
                    break

            for m in _re.finditer(
                r"(?:path|re_path)\(\s*(['\"])(.+?)\1\s*,\s*([^)]+)",
                f.content,
            ):
                route = m.group(2)
                view_expr = m.group(3).strip()
                if view_expr.startswith("include") or view_expr.startswith("("):
                    continue
                name_match = _re.search(r'(\w+)\.as_view\(', view_expr)
                if name_match:
                    view_name = name_match.group(1)
                else:
                    name_match = _re.search(r'(\w+)$', view_expr)
                    if name_match:
                        view_name = name_match.group(1)
                    else:
                        continue
                full_route = f"{prefix.strip('/')}/{route.strip('/')}"
                view_routes[view_name] = full_route

    app_docs = {}
    for f in files:
        if not f.parsed_data:
            continue
        # Only process views.py and admin.py for API docs
        if not (f.file_path.endswith("views.py") or f.file_path.endswith("admin.py")):
            continue
        parts = f.file_path.replace("\\", "/").split("/")
        app_name = "other"
        for i, p in enumerate(parts):
            if p == "apps" and i + 1 < len(parts):
                app_name = parts[i + 1]
                break
            if p == "config":
                app_name = "config"
                break
        if app_name not in app_docs:
            app_docs[app_name] = []

        for item in f.parsed_data.get("ordered_items", []):
            if item["type"] not in ("function", "class"):
                continue
            data = item["data"]
            name = data["name"]
            docstring = (data.get("docstring") or "")[:150]
            route = view_routes.get(name, "")
            methods = []
            if item["type"] == "class":
                for m in data.get("methods", []):
                    mname = m["name"]
                    if mname in ("get", "post", "put", "patch", "delete", "head", "options"):
                        methods.append(mname.upper())
                    else:
                        methods.append(mname)
            desc = docstring.replace("\n", " ") if docstring else ""
            # Only include items that have a route OR are view classes with HTTP methods
            if not route and not methods:
                continue
            dedup_methods = list(dict.fromkeys(methods))  # dedup preserving order
            http_verbs = [m for m in dedup_methods if m in ("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
            custom_methods = [m for m in dedup_methods if m not in ("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
            app_docs[app_name].append({
                "name": name, "type": item["type"], "route": route,
                "http_verbs": http_verbs, "custom_methods": custom_methods,
                "description": desc, "file": f.file_path,
            })

    if not app_docs:
        return "# API Documentation\n\nNo API endpoints found."

    lines = ["# API Documentation\n"]
    for app_name in sorted(app_docs.keys()):
        entries = app_docs[app_name]
        if not entries:
            continue
        lines.append(f"## {app_name}\n")
        for e in entries:
            name = e["name"]
            desc = e["description"] if e["description"] else "—"
            file_path = e["file"]

            if e["route"]:
                clean_route = f"/{e['route'].strip('/')}"
                methods_line = "`, `".join(e["http_verbs"]) if e["http_verbs"] else "—"
                lines.append(f"### {name}\n")
                lines.append(f"`{methods_line}` `{clean_route}`\n")
                lines.append(f"{desc}\n")
                if e["custom_methods"]:
                    lines.append(f"**Custom methods:** `{', '.join(e['custom_methods'])}`\n")
                methods_lower = set(m.lower() for m in e["http_verbs"])
                body = _postman_body_example(clean_route) if any(v in methods_lower for v in ("post","put","patch")) else ""
                if "post" in methods_lower:
                    lines.append(f"**Postman:**\n```\nPOST http://localhost:8000{clean_route}\nAuthorization: Bearer <token>\nContent-Type: application/json{body}\n```\n")
                elif "put" in methods_lower:
                    lines.append(f"**Postman:**\n```\nPUT http://localhost:8000{clean_route}\nAuthorization: Bearer <token>\nContent-Type: application/json{body}\n```\n")
                elif "patch" in methods_lower:
                    lines.append(f"**Postman:**\n```\nPATCH http://localhost:8000{clean_route}\nAuthorization: Bearer <token>\nContent-Type: application/json{body}\n```\n")
                elif "delete" in methods_lower:
                    lines.append(f"**Postman:**\n```\nDELETE http://localhost:8000{clean_route}\nAuthorization: Bearer <token>\n```\n")
                elif "get" in methods_lower:
                    lines.append(f"**Postman:**\n```\nGET http://localhost:8000{clean_route}\nAuthorization: Bearer <token>\n```\n")
            else:
                methods_str = ", ".join(e["http_verbs"] + e["custom_methods"]) if (e["http_verbs"] or e["custom_methods"]) else "—"
                lines.append(f"### {name}\n")
                lines.append(f"**Methods:** `{methods_str}`\n")
                lines.append(f"{desc}\n")

            lines.append(f"**File:** `{file_path}`\n")
            lines.append("---\n")
    return "\n".join(lines)


@app.post("/api/ai/generate/", response_model=GenerateResponse)
def generate_docs(req: GenerateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _auth: str = Depends(verify_internal_key)):
    project = db.query(Project).filter(Project.id == uuid.UUID(req.project_id)).first()
    if not project:
        raise HTTPException(404, "Project not found")

    project.status = "processing"
    project.updated_at = datetime.utcnow()
    db.commit()

    files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project.id
    ).all()

    if not files:
        raise HTTPException(400, "No parsed files found. Run parser first.")

    try:
        fw_info = project.framework_info or {}

        if project.source_type == "file" and len(files) == 1:
            f = files[0]
            if req.use_ai and GROQ_API_KEY:
                try:
                    embed_and_store_chunks(str(project.id), files, db)
                except Exception as e:
                    logger = logging.getLogger("ai.generate_docs")
                    logger.warning("Embedding failed (continuing without RAG): %s", e)
                docs = generate_file_docs(f.parsed_data or {}, f.file_name, fw_info, db, str(project.id))
            else:
                docs = _mock_docs(f.parsed_data or {}, f.file_name, fw_info)

            project.generated_docs = _sanitize_markdown(docs)
            f.generated_docs = project.generated_docs
            db.commit()
        else:
            temp_dir = tempfile.mkdtemp()
            try:
                for f in files:
                    if f.content:
                        fp = os.path.join(temp_dir, f.file_path)
                        os.makedirs(os.path.dirname(fp), exist_ok=True)
                        with open(fp, "w") as fh:
                            fh.write(f.content)

                summary = generate_project_summary(temp_dir, project.name)
                project.project_info = summary

                if req.use_ai and GROQ_API_KEY:
                    try:
                        embed_and_store_chunks(str(project.id), files, db)
                    except Exception as e:
                        logger = logging.getLogger("ai.generate_docs")
                        logger.warning("Embedding failed (continuing without RAG): %s", e)

                    parsed_list = []
                    for f in files:
                        if f.parsed_data:
                            parsed_list.append({"file_path": f.file_path, "parsed": f.parsed_data})

                    fw_name = fw_info.get("primary_framework", summary.get("framework", "python"))
                    fw_summary = fw_info.get("summary", "")
                    fw_block = f"\nDetected Frameworks: {fw_summary}\n" if fw_summary else ""

                    tree_lines = (summary.get("project_tree") or "").splitlines()
                    if len(tree_lines) > 30:
                        tree_lines = tree_lines[:28] + ["... (truncated)"]
                    tree_trunc = "\n".join(tree_lines)

                    deps = summary.get("dependencies", [])
                    if len(deps) > 20:
                        deps = deps[:18] + ["... (truncated)"]
                    clone_url = (project.github_url or "").strip()
                    clone_hint = ""
                    repo_dir = project.name
                    if clone_url:
                        clone_hint = f"\nClone URL: {clone_url}"
                        repo_dir = clone_url.rstrip("/").split("/")[-1].replace(".git", "") or project.name

                    pm_map = {
                        "uv": "`uv sync`",
                        "poetry": "`poetry install`",
                        "pipenv": "`pipenv install`",
                        "pip": "`pip install -r requirements.txt`",
                    }
                    pm_cmd = pm_map.get(summary.get("package_manager", "pip"), "`pip install -r requirements.txt`")

                    project_context = (
                        f"Project Name: {project.name}\n"
                        f"Description: {project.description or 'No description provided'}\n"
                        f"Framework: {fw_name}\n"
                        f"Architecture: {summary.get('architecture', 'monolith')}\n"
                        f"Total Files: {summary['file_count']}{fw_block}\n\n"
                        f"Project Structure:\n{tree_trunc}\n\n"
                        f"Dependencies:\n{chr(10).join(deps)}\n\n"
                        f"Apps/Modules: {', '.join(summary.get('apps', [])) or 'None detected'}\n"
                        f"Package Manager: {summary.get('package_manager', 'pip')}\n"
                        f"Relevant Code Context:\n{_retrieve_project_context(str(project.id), project.name, db)}\n"
                        f"{clone_hint}\n"
                    )

                    def _call_ai_section(prompt_body: str, key_offset: int, label: str, max_tokens: int = 4096) -> str:
                        plen = len(prompt_body)
                        if plen > 12000:
                            prompt_body = prompt_body[:12000] + "\n... (truncated)"
                            print(f"[{label}] Prompt truncated from {plen} to 12000 chars", flush=True)
                        print(f"[{label}] Prompt size: {len(prompt_body)} chars, calling _call_groq", flush=True)
                        return _call_groq(prompt_body, max_tokens=max_tokens, model="llama-3.3-70b-versatile", key_start=key_offset)

                    import time as _time

                    # Build API docs programmatically from urls.py + parsed data
                    project.api_docs = _build_api_docs(files)

                    _time.sleep(3)

                    # Determine correct cd directory from project structure
                    has_root_req = any(f.file_path == "requirements.txt" for f in files)
                    has_root_manage = any(f.file_path == "manage.py" for f in files)
                    cd_dir = "." if (has_root_req or has_root_manage) else (repo_dir or ".")

                    # Build dynamic mermaid flowchart from actual apps
                    detected_apps = summary.get("apps", [])
                    app_labels = [a.split(".")[-1].replace("_", " ").title() for a in detected_apps]
                    mermaid_lines = ["flowchart TD", "    A[Client] --> B[Backend]"]
                    for i, label in enumerate(app_labels):
                        node = chr(67 + i) if i < 24 else f"N{i}"
                        mermaid_lines.append(f"    B --> {node}[{label}]")
                    mermaid_block = "\n".join(mermaid_lines)
                    app_list_str = ", ".join(f"`{a}`" for a in detected_apps) if detected_apps else "the detected modules"

                    summary_prompt = f"""{project_context}

Generate a project summary with two parts.

Part 1 — Overview: 2-3 paragraphs on the project's purpose, architecture, data flow. Include exactly ONE detailed mermaid flowchart based on the actual apps above (do NOT add a second simplified version):

```mermaid
{mermaid_block}
```

Part 2 — App-by-App Breakdown: For EACH app/module detected in this project, write one paragraph explaining what that app does, its key files, and how it fits the architecture. Include ALL of: {app_list_str}. Do NOT skip any.

Output ONLY the summary content."""
                    summary_result = _call_ai_section(summary_prompt, 1, "SUMMARY", max_tokens=2048)
                    tree_block = "\n\n---\n\n## Project Structure\n\n```\n" + summary.get("project_tree", "") + "\n```\n"
                    if summary_result:
                        project.generated_docs = _sanitize_markdown(summary_result + tree_block)
                    else:
                        project.generated_docs = tree_block.strip()

                    _time.sleep(3)

                    readme_prompt = f"""{project_context}

Write a README with:

## Title & Description
What the project is and who it's for (3-4 sentences).

## Key Features
5-7 bullet features from the app modules.

## Quick Start
```bash
git clone {clone_url or '<CLONE_URL>'}
cd {cd_dir}
{pm_cmd}
```
Then run: `python manage.py migrate && python manage.py runserver` (or equivalent for the framework).

## Architecture & Project Structure
Describe the monolithic layout, the apps under `backend/apps/`, and the data flow (2-3 paragraphs).

Output ONLY the README content."""
                    readme_result = _call_ai_section(readme_prompt, 0, "README", max_tokens=2048)
                    project.readme_docs = _sanitize_markdown(readme_result) if readme_result else "# " + project.name + "\n\nNo README generated."
                else:
                    fallback = f"""# {project.name}

## Overview
Mock project documentation for {project.name}.

## Project Structure
{summary['project_tree']}

## Dependencies
{' '.join(summary.get('dependencies', [])) or 'Not detected'}

> ⚠️ Configure GROQ_API_KEY to generate AI-powered documentation."""
                    project.readme_docs = _sanitize_markdown(fallback)
                    project.generated_docs = _sanitize_markdown(fallback)

            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        project.status = "done"
        project.updated_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        import traceback
        logger = logging.getLogger("ai.generate_docs")
        logger.error("Generation failed: %s\n%s", str(e), traceback.format_exc())
        project.status = "failed"
        project.error_message = str(e)
        db.commit()
        return GenerateResponse(
            project_id=str(project.id),
            status="failed",
        )

    return GenerateResponse(
        project_id=str(project.id),
        status="done",
        generated_docs=project.generated_docs,
        readme_docs=project.readme_docs,
        api_docs=project.api_docs,
    )


@app.get("/api/ai/status/{project_id}")
def ai_status(project_id: str, db: Session = Depends(get_db), _auth: str = Depends(verify_internal_key)):
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return {
        "project_id": str(project.id),
        "status": project.status,
        "has_docs": bool(project.generated_docs),
    }
