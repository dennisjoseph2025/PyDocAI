import os
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session

from ..services.groq import call_groq
from ..services.markdown import sanitize_markdown
from ..services.prompts import get_item_docs_prompt
from ..services.docs_builder import build_structure_tree, build_api_docs
from ..rag import embed_and_store_chunks, retrieve_context, store_generated_doc


def retrieve_project_context(project_id: str, project_name: str, db: Session) -> str:
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


def mock_docs(parsed: dict, file_path: str, _framework_info: Optional[dict] = None) -> str:
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

> This is mock documentation. Configure GROQ_API_KEY to generate real AI-powered docs.
"""


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

    structure_tree = build_structure_tree(ordered_items)

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
    overview_docs = call_groq(overview_prompt, max_tokens=2048, key_start=0)

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
            docs = call_groq(item_prompt, max_tokens=2048, key_start=(i + 1) % 2)
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
