import ast
from typing import Any


def parse_python_file(source_code: str) -> dict:
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {
            "error": True,
            "error_message": f"SyntaxError on line {e.lineno}: {e.msg}"
        }

    result = {
        "error": False,
        "module_docstring": ast.get_docstring(tree),
        "imports": [],
        "functions": [],
        "classes": [],
        "ordered_items": []
    }

    top_level_names = set()

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            top_level_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            top_level_names.add(node.name)
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    top_level_names.add(item.name)

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_entry = _extract_import(node)
            result["imports"].append(import_entry)
            result["ordered_items"].append({
                "type": "import",
                "line": node.lineno,
                "data": import_entry
            })
        elif isinstance(node, ast.FunctionDef):
            func_data = _extract_function(node, top_level_names)
            result["functions"].append(func_data)
            result["ordered_items"].append({
                "type": "function",
                "line": node.lineno,
                "data": func_data
            })
        elif isinstance(node, ast.ClassDef):
            class_data = _extract_class(node, top_level_names)
            result["classes"].append(class_data)
            result["ordered_items"].append({
                "type": "class",
                "line": node.lineno,
                "data": class_data
            })

    return result


def _extract_import(node) -> dict[str, Any]:
    if isinstance(node, ast.Import):
        names = [alias.name for alias in node.names]
        return {
            "line": node.lineno,
            "type": "import",
            "module": names[0] if len(names) == 1 else None,
            "names": names,
            "display": ', '.join(names)
        }
    else:
        names = [alias.name for alias in node.names]
        module = node.module or ''
        return {
            "line": node.lineno,
            "type": "import-from",
            "module": module,
            "names": names,
            "display": f"from {module} import {', '.join(names)}"
        }


def _extract_function(node, available_names: set) -> dict[str, Any]:
    connections = _find_connections(node, available_names)
    return {
        "name": node.name,
        "args": extract_args(node),
        "returns": extract_return_type(node),
        "docstring": ast.get_docstring(node),
        "decorators": [ast.unparse(d) for d in node.decorator_list],
        "line": node.lineno,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "connections": connections
    }


def _extract_class(node, available_names: set) -> dict[str, Any]:
    methods = []
    class_connections = _find_connections(node, available_names)

    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            method_connections = _find_connections(item, available_names)
            methods.append({
                "name": item.name,
                "args": extract_args(item),
                "returns": extract_return_type(item),
                "docstring": ast.get_docstring(item),
                "is_private": item.name.startswith("_"),
                "line": item.lineno,
                "connections": method_connections,
                "parent_class": node.name
            })

    return {
        "name": node.name,
        "docstring": ast.get_docstring(node),
        "bases": [ast.unparse(b) for b in node.bases],
        "methods": methods,
        "line": node.lineno,
        "connections": class_connections
    }


def _find_connections(node, available_names: set) -> list[str]:
    connections = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                if child.func.id in available_names:
                    connections.add(child.func.id)
        elif isinstance(child, ast.Name):
            if child.id in available_names:
                connections.add(child.id)
    return sorted(connections)


def extract_args(func_node) -> list:
    args = []
    for arg in func_node.args.args:
        args.append({
            "name": arg.arg,
            "type": ast.unparse(arg.annotation) if arg.annotation else None
        })
    return args


def extract_return_type(func_node) -> str | None:
    if func_node.returns:
        return ast.unparse(func_node.returns)
    return None
