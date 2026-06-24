from typing import Optional


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
