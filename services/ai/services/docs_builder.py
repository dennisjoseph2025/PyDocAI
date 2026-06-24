def _ensure_dict(f):
    """Normalize file data to dict (works with SQLAlchemy objects or API dicts)."""
    if isinstance(f, dict):
        return f
    return {
        "file_path": f.file_path,
        "content": getattr(f, "content", ""),
        "parsed_data": getattr(f, "parsed_data", {}),
        "file_name": getattr(f, "file_name", ""),
        "file_size": getattr(f, "file_size", 0),
    }


def build_structure_tree(ordered_items: list) -> str:
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


def postman_body_example(route: str) -> str:
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


def build_api_docs(files: list) -> str:
    import re as _re
    view_routes = {}
    url_prefixes = {}

    dict_files = [_ensure_dict(f) for f in files]

    for f in dict_files:
        fp = f["file_path"]
        content = f.get("content") or ""
        if fp.endswith("urls.py") and content:
            for m in _re.finditer(
                r"(?:path|re_path)\(\s*(['\"])(.+?)\1\s*,\s*include\((['\"])(.+?)\3\)",
                content,
            ):
                route, included = m.group(2), m.group(4)
                included_path = included.replace(".urls", "").replace(".", "/")
                url_prefixes[included_path] = route

    for f in dict_files:
        fp = f["file_path"]
        content = f.get("content") or ""
        if fp.endswith("urls.py") and content:
            file_key = fp.replace("\\", "/")
            parts = file_key.split("/")
            prefix = ""
            for p in range(len(parts)):
                candidate = "/".join(parts[p:]).replace("/urls.py", "").replace(".", "/")
                if candidate in url_prefixes:
                    prefix = url_prefixes[candidate]
                    break

            for m in _re.finditer(
                r"(?:path|re_path)\(\s*(['\"])(.+?)\1\s*,\s*([^)]+)",
                content,
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
    for f in dict_files:
        parsed = f.get("parsed_data") or {}
        if not parsed:
            continue
        fp = f["file_path"]
        if not (fp.endswith("views.py") or fp.endswith("admin.py")):
            continue
        parts = fp.replace("\\", "/").split("/")
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

        for item in parsed.get("ordered_items", []):
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
            if not route and not methods:
                continue
            dedup_methods = list(dict.fromkeys(methods))
            http_verbs = [m for m in dedup_methods if m in ("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
            custom_methods = [m for m in dedup_methods if m not in ("GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS")]
            app_docs[app_name].append({
                "name": name, "type": item["type"], "route": route,
                "http_verbs": http_verbs, "custom_methods": custom_methods,
                "description": desc, "file": fp,
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
                body = postman_body_example(clean_route) if any(v in methods_lower for v in ("post","put","patch")) else ""
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
