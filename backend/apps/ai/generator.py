import re
from django.conf import settings
from .prompts import get_file_docs_prompt, get_item_docs_prompt, _build_structure_tree
from .project_docs import generate_project_docs


def _sanitize_markdown(text: str) -> str:
    """Clean up AI-generated markdown to fix common formatting issues."""
    if not text:
        return text

    # Fix "code\nCopy\npython" artifacts -> proper code fences
    text = re.sub(r'\bcode\s*\n\s*Copy\s*\n\s*python\s*\n', '```python\n', text)
    text = re.sub(r'\bcode\s*\n\s*Copy\s*\n\s*(\w+)\s*\n', r'```\1\n', text)
    text = re.sub(r'\bcode\s*\n\s*Copy\s*\n', '```\n', text)

    # Ensure code fences are properly closed
    # Count opening and closing fences, add missing closes
    opens = len(re.findall(r'```', text))
    if opens % 2 != 0:
        text += '\n```'

    # Fix orphaned closing fences
    text = re.sub(r'\n\s*```\s*\n\s*```\s*\n', '\n```\n', text)

    # Ensure blank lines before headings
    text = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', text)

    # Ensure blank lines after headings
    text = re.sub(r'(#{1,6} .+)\n([^\n#])', r'\1\n\n\2', text)

    # Remove duplicate blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def generate_file_docs(parsed: dict, file_path: str) -> str:

    if settings.DEBUG and not getattr(settings, 'GROQ_API_KEY', None):
        return _mock_docs(parsed, file_path)

    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    groq_key_2 = getattr(settings, 'GROQ_API_KEY_2', None)

    if not groq_key and not groq_key_2:
        return _sanitize_markdown(_mock_docs(parsed, file_path))

    from groq import Groq

    # Try primary key first, then fallback key
    groq_keys = []
    if groq_key:
        groq_keys.append(('primary', groq_key))
    if groq_key_2:
        groq_keys.append(('fallback', groq_key_2))

    for key_name, key in groq_keys:
        try:
            client = Groq(api_key=key)
            return _sanitize_markdown(_generate_with_client(client, parsed, file_path))
        except Exception as e:
            print(f"Groq {key_name} key failed for file docs: {e}")

    return _sanitize_markdown(_mock_docs(parsed, file_path))


def _call_ai(client, prompt: str, max_tokens: int = 2048) -> str:
    """Call the AI with a prompt and return the response."""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    result = response.choices[0].message.content.strip()

    # Strip wrapping code fences if model disobeys
    if result.startswith("```"):
        result = result.split("```", 2)[-1].strip()
        if result.endswith("```"):
            result = result[:-3].strip()

    return result


def _generate_with_client(client, parsed: dict, file_path: str) -> str:
    """Generate docs using Groq-compatible client."""
    ordered_items = parsed.get('ordered_items', [])
    module_doc    = parsed.get('module_docstring') or 'No module docstring'
    imports       = parsed.get('imports', [])

    import_displays = []
    for imp in imports:
        if isinstance(imp, dict):
            import_displays.append(imp.get('display', str(imp)))
        else:
            import_displays.append(str(imp))

    structure_tree = _build_structure_tree(ordered_items)

    overview_prompt = f"""
Generate the beginning sections for the Python file {file_path}.
Module docstring: {module_doc}
Imports: {', '.join(import_displays)}

Output ONLY the following sections in markdown (nothing else):

# {file_path}

## Overview
3-5 detailed paragraphs on what this module does, its purpose, architecture, and key components.

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
    overview_docs = _call_ai(client, overview_prompt, max_tokens=2048)

    item_docs = []
    for item in ordered_items:
        typ = item['type']
        data = item['data']
        line = item['line']

        if typ == 'import':
            continue
        elif typ in ('function', 'class'):
            item_prompt = get_item_docs_prompt(typ, data, file_path)
            docs = _call_ai(client, item_prompt, max_tokens=4096)
            item_docs.append(docs)

    result = overview_docs + "\n\n"
    result += "## Detailed Documentation (IN SOURCE ORDER)\n\n"
    result += "\n\n---\n\n".join(item_docs)
    result += "\n\n## End of Documentation"

    return result.strip()


def _mock_docs(parsed: dict, file_path: str) -> str:
    """Returns mock docs for development when no API key available."""
    functions = parsed.get('functions', [])
    classes   = parsed.get('classes', [])
    imports   = parsed.get('imports', [])
    ordered   = parsed.get('ordered_items', [])

    # Format imports properly (handle both dict and string format)
    import_lines = []
    for imp in imports:
        if isinstance(imp, dict):
            import_lines.append(f'- `{imp.get("display", str(imp))}` (line {imp.get("line", "?")})')
        else:
            import_lines.append(f'- `{imp}`')

    # Build documentation in source order
    doc_sections = []
    for item in ordered:
        typ = item['type']
        data = item['data']
        if typ == 'import':
            pass  # Already handled above
        elif typ == 'function':
            args = ', '.join(a['name'] for a in data.get('args', []))
            returns = data.get('returns') or 'None'
            line = data.get('line', '?')
            connections = data.get('connections', [])
            conn_str = f" (calls: {', '.join(connections)})" if connections else ''
            doc_sections.append(f'### `{data["name"]}({args}) -> {returns}`\n- **Line:** {line}{conn_str}\n- **Purpose:** Mock documentation')
        elif typ == 'class':
            line = data.get('line', '?')
            bases = ', '.join(data.get('bases', []))
            base_str = f'({bases})' if bases else ''
            connections = data.get('connections', [])
            conn_str = f" (uses: {', '.join(connections)})" if connections else ''
            doc_sections.append(f'### `{data["name"]}{base_str}`\n- **Line:** {line}{conn_str}\n- **Methods:** {", ".join(m["name"] for m in data.get("methods", []))}')

    return f"""# {file_path}

## Overview
Mock documentation generated for development purposes. This shows how the documentation will be structured with source order preserved.

## Imports
{chr(10).join(import_lines) or 'No imports'}

## Detailed Documentation (IN SOURCE ORDER)

{chr(10).join(doc_sections) or 'No functions or classes'}

> ⚠️ This is mock documentation. Configure GROQ_API_KEY to generate real AI-powered docs.
"""


def generate_folder_docs(
    folder_path: str,
    project_name: str = None,
    user_description: str = None,
    custom_info: dict = None,
    parsed_ast_data: list = None
) -> dict:
    """
    Generate comprehensive documentation for a whole project folder.
    
    This function is called when a user uploads a folder/project instead of a single file.
    It generates:
    - README.md for the project
    - Project summary/documentation
    - Overall project information
    
    Args:
        folder_path: Path to the project folder
        project_name: Optional name for the project
        user_description: Optional user-provided description of the project
        custom_info: Optional dictionary of user-provided project details
        
    Returns:
        dict with keys:
        - 'readme': README.md content
        - 'summary': Project documentation
        - 'project_info': Raw project information
    """
    return generate_project_docs(
        project_path=folder_path,
        project_name=project_name,
        user_description=user_description,
        custom_info=custom_info,
        use_ai=True,
        parsed_ast_data=parsed_ast_data
    )