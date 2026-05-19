def _get_example_value(arg: dict) -> str:
    """Generate realistic example value based on parameter type."""
    param_type = (arg.get('type') or '').lower()
    arg_name = arg.get('name', 'value')
    default = arg.get('default')

    if default is not None:
        return repr(default)

    if 'int' in param_type or 'float' in param_type or 'num' in param_type:
        return '0' if 'int' in param_type else '0.0'
    elif 'str' in param_type:
        return '"example_string"'
    elif 'bool' in param_type:
        return 'True'
    elif 'list' in param_type or 'array' in param_type:
        return '[]'
    elif 'dict' in param_type or 'object' in param_type:
        return '{}'
    elif 'None' in param_type:
        return 'None'
    else:
        return arg_name


def _get_return_example(return_type: str) -> str:
    """Generate realistic example return value based on return type."""
    rt = (return_type or '').lower()
    if rt in ('none', 'nonetype'):
        return 'None'
    elif 'str' in rt:
        return '"output_string"'
    elif 'int' in rt and 'list' not in rt:
        return '42'
    elif 'float' in rt:
        return '3.14'
    elif 'bool' in rt:
        return 'True'
    elif 'list' in rt or 'tuple' in rt:
        return '["item1", "item2"]'
    elif 'dict' in rt:
        return '{"key": "value"}'
    elif 'bytes' in rt:
        return 'b"data"'
    elif 'object' in rt:
        return '<CustomClass object>'
    else:
        return 'result'


def _format_functions(functions: list) -> str:
    if not functions:
        return '  None'
    lines = []
    for f in functions:
        args       = ', '.join([
            f"{a['name']}: {a['type']}" if a['type'] else a['name']
            for a in f.get('args', [])
        ])
        ret        = f.get('returns') or 'None'
        doc        = (f.get('docstring') or 'No docstring')[:150]
        decorators = ', '.join(f.get('decorators', []))
        async_tag  = 'async ' if f.get('is_async') else ''
        connections = f.get('connections', [])
        conn_str   = f"\n    connections: {', '.join(connections)}" if connections else ''
        lines.append(
            f"  - {async_tag}{f['name']}({args}) -> {ret}\n"
            f"    docstring: {doc}\n"
            f"    decorators: {decorators or 'none'}\n"
            f"    line: {f.get('line')}"
            f"{conn_str}"
        )
    return '\n'.join(lines)


def _format_classes(classes: list) -> str:
    if not classes:
        return '  None'
    lines = []
    for c in classes:
        doc     = (c.get('docstring') or 'No docstring')[:150]
        bases   = ', '.join(c.get('bases', []))
        class_connections = c.get('connections', [])
        conn_str = f"\n    connections: {', '.join(class_connections)}" if class_connections else ''
        lines.append(
            f"  - {c['name']}({bases})\n"
            f"    docstring: {doc}\n"
            f"    line: {c.get('line')}"
            f"{conn_str}"
        )
        # Add methods with connections
        for m in c.get('methods', []):
            method_args = ', '.join([
                f"{a['name']}: {a['type']}" if a['type'] else a['name']
                for a in m.get('args', [])
            ])
            method_ret = m.get('returns') or 'None'
            visibility = 'private' if m.get('is_private') else 'public'
            method_connections = m.get('connections', [])
            method_conn_str = f"\n        connections: {', '.join(method_connections)}" if method_connections else ''
            lines.append(
                f"    - {m['name']}({method_args}) -> {method_ret} [{visibility}]\n"
                f"      docstring: {(m.get('docstring') or 'No docstring')[:150]}\n"
                f"      line: {m.get('line')}"
                f"{method_conn_str}"
            )
    return '\n'.join(lines)


def _build_ordered_section(ordered_items: list) -> str:
    """Build the documentation section in source order."""
    if not ordered_items:
        return "No items found."

    lines = []
    for item in ordered_items:
        typ = item['type']
        data = item['data']
        line = item['line']

        if typ == 'import':
            lines.append(f"### IMPORT at line {line}: {data.get('display', 'import')}")
        elif typ == 'function':
            name = data['name']
            connections = data.get('connections', [])
            conn_str = f" (calls: {', '.join(connections)})" if connections else ''
            lines.append(f"### FUNCTION at line {line}: {name}(){conn_str}")
        elif typ == 'class':
            name = data['name']
            bases = ', '.join(data.get('bases', []))
            base_str = f"({bases})" if bases else ''
            connections = data.get('connections', [])
            conn_str = f" (uses: {', '.join(connections)})" if connections else ''
            lines.append(f"### CLASS at line {line}: {name}{base_str}{conn_str}")
            # Add methods
            for m in data.get('methods', []):
                mname = m['name']
                mline = m['line']
                mconns = m.get('connections', [])
                mconn_str = f" (calls: {', '.join(mconns)})" if mconns else ''
                lines.append(f"  #### METHOD at line {mline}: {mname}(){mconn_str}")

    return '\n'.join(lines)


def _get_example_value(arg: dict) -> str:
    """Generate realistic example value based on parameter type."""
    param_type = (arg.get('type') or '').lower()
    arg_name = arg.get('name', 'value')
    default = arg.get('default')

    if default is not None:
        return repr(default)

    if 'int' in param_type or 'float' in param_type or 'num' in param_type:
        return '0' if 'int' in param_type else '0.0'
    elif 'str' in param_type:
        return '"example_string"'
    elif 'bool' in param_type:
        return 'True'
    elif 'list' in param_type or 'array' in param_type:
        return '[]'
    elif 'dict' in param_type or 'object' in param_type:
        return '{}'
    elif 'None' in param_type:
        return 'None'
    else:
        return arg_name


def get_item_docs_prompt(item_type: str, data: dict, file_path: str) -> str:
    """Generate a prompt for documenting a single item (function/class)."""
    if item_type == 'function':
        name = data['name']
        args = ', '.join(f"{a['name']}: {a['type']}" if a['type'] else a['name'] for a in data.get('args', []))
        args_examples = ', '.join(_get_example_value(a) for a in data.get('args', []))
        ret = data.get('returns') or 'None'
        line = data.get('line', '?')
        connections = data.get('connections', [])
        is_async = data.get('is_async', False)
        async_tag = 'async ' if is_async else ''
        docstring = data.get('docstring') or 'No docstring'
        decorators = data.get('decorators', [])

        conn_str = f"\nConnections: Calls {', '.join(connections)}" if connections else ''

        return f"""
Document this function ONLY. Output ONLY the markdown for this function, nothing else. Be EXTREMELY detailed.

File: {file_path}
Function: {async_tag}{name}({args}) -> {ret}
Line: {line}
Docstring: {docstring}
Decorators: {', '.join(decorators) or 'none'}
{conn_str}

Output ONLY the markdown for this function in this EXACT format (fill in all sections):

### `{async_tag}{name}({args}) -> {ret}`
**Line:** {line} | **Visibility:** Public/Private | **Async:** {'Yes' if is_async else 'No'} | **Connections:** {', '.join(connections) if connections else 'none'}

#### Purpose
(3-5 sentences explaining exactly what this function does, when to use it, and why it exists)

#### Behavior
(Step-by-step explanation of what happens when this function is called):
1. First, it validates...
2. Then, it processes...
3. Finally, it returns...

#### Description
(Detailed technical description including):
- Complete logic flow
- All side effects (print, file I/O, network calls)
- Error handling approach
- Edge cases handled
- Performance considerations

#### Parameters
| Parameter | Type | Description | Default | Constraints |
|-----------|------|-------------|---------|-------------|
| ... | ... | ... | ... | ... |

#### Returns
- **Type:** `{ret}`
- **Description:** What the return value represents
- **Possible Values:** Enumeration if limited
- **None cases:** When it returns None

#### Raises
(List all exceptions that can be raised and when)

#### Relationships
- **Calls:** {', '.join(connections) if connections else 'none'}
- **Called By:** (infer from context)
- **Uses:** imports or external dependencies

#### Example Input
```python
# Full working example with all parameters
result = {name}({args_examples})
```

#### Example Output
```python
# Returns: {ret}
# Example value: {_get_return_example(ret)}
```

#### Edge Cases
- Empty inputs
- None values
- Invalid types
- Boundary conditions

#### Complexity
- **Time:** Big O notation
- **Space:** Big O notation
- **Explanation:** Why this complexity
"""

    elif item_type == 'class':
        name = data['name']
        bases = ', '.join(data.get('bases', []))
        base_str = f"({bases})" if bases else ''
        line = data.get('line', '?')
        connections = data.get('connections', [])
        docstring = data.get('docstring') or 'No docstring'
        methods = data.get('methods', [])

        conn_str = f"\nConnections: Uses {', '.join(connections)}" if connections else ''

        # Build detailed methods prompt
        methods_detail = ""
        for m in methods:
            mname = m['name']
            margs = ', '.join(f"{a['name']}: {a['type']}" if a['type'] else a['name'] for a in m.get('args', []))
            margs_examples = ', '.join(_get_example_value(a) for a in m.get('args', []))
            mret = m.get('returns') or 'None'
            mline = m.get('line', '?')
            mconns = m.get('connections', [])
            mconn_str = f" (calls: {', '.join(mconns)})" if mconns else ''
            is_private = m.get('is_private', False)
            visibility = 'Private' if is_private else 'Public'

            methods_detail += f"""
#### `{mname}({margs}) -> {mret}`
**Line:** {mline} | **Visibility:** {visibility} | **Connections:** {', '.join(mconns) if mconns else 'none'}

##### Purpose
(3-5 sentences explaining what this method does, when to call it, why it exists)

##### Behavior
(Step-by-step explanation of what happens when called):
1. First, it validates...
2. Then, it processes...
3. Finally, it returns...

##### Description
(Detailed technical description including):
- Complete logic flow
- All side effects (I/O, network, state changes)
- Error handling approach
- Edge cases handled

##### Parameters
| Parameter | Type | Description | Default | Constraints |
|-----------|------|-------------|---------|-------------|
| ... | ... | ... | ... | ... |

##### Returns
- **Type:** `{mret}`
- **Description:** What the return value represents
- **Possible Values:** (enumeration if limited)
- **None cases:** When it returns None

##### Raises
(List ALL exceptions this method can raise and when)

##### Relationships
- **Calls:** {', '.join(mconns) if mconns else 'none'}
- **Called By:** (infer from other functions/classes)
- **Uses:** imports or external dependencies

##### Example Input
```python
# Full working example with all parameters
obj = {name}()
result = obj.{mname}({margs_examples})
```

##### Example Output
```python
# Returns: {mret}
# Example value: {_get_return_example(mret)}
```

##### Edge Cases
- Empty inputs
- None values
- Invalid types
- Boundary conditions

##### Complexity
- **Time:** Big O notation
- **Space:** Big O notation
- **Explanation:** Why this complexity

---
"""

        return f"""
Document this class ONLY. Output ONLY the markdown for this class, nothing else. Be EXTREMELY detailed.

File: {file_path}
Class: {name}{base_str}
Line: {line}
Docstring: {docstring}
Base classes: {bases or 'none'}
Connections: {', '.join(connections) if connections else 'none'}

Output ONLY the markdown for this class in this EXACT format (fill in ALL sections):

### `{name}{base_str}`
**Line:** {line} | **Connections:** {', '.join(connections) if connections else 'none'}

#### Purpose
(3-5 sentences explaining what this class does, its responsibilities, design patterns used, when to use it)

#### Behavior
(How this class works, its lifecycle, key operations, thread safety, state management)

#### Attributes
(Inferred from __init__ or class body):
| Attribute | Type | Description | Default |
|-----------|------|-------------|---------|
| ... | ... | ... | ... |

#### Inherits
- **Base Classes:** {bases or 'none'}
- **Inherited Methods:** (list key inherited methods and their behavior)
- **Inherited Behavior:** How base classes affect this class

#### Methods
{methods_detail}
"""

    return ""


def _build_structure_tree(ordered_items: list) -> str:
    """Build a visual tree representation of the code structure."""
    if not ordered_items:
        return "No items found."

    tree_lines = []
    tree_lines.append("# <filename>")
    tree_lines.append("├── Overview")
    tree_lines.append("├── Code Structure and Relationships")
    tree_lines.append("├── Imports")

    for i, item in enumerate(ordered_items):
        typ = item['type']
        data = item['data']
        line = item['line']
        is_last = (i == len(ordered_items) - 1)
        prefix = "└── " if is_last else "├── "

        if typ == 'import':
            display = data.get('display', 'import')
            tree_lines.append(f"{prefix}IMPORT: {display} (line {line})")
        elif typ == 'function':
            name = data['name']
            connections = data.get('connections', [])
            conn_str = f" → calls: {', '.join(connections)}" if connections else ''
            tree_lines.append(f"{prefix}FUNCTION: {name}() (line {line}){conn_str}")
        elif typ == 'class':
            name = data['name']
            bases = ', '.join(data.get('bases', []))
            base_str = f"({bases})" if bases else ''
            connections = data.get('connections', [])
            conn_str = f" → uses: {', '.join(connections)}" if connections else ''
            tree_lines.append(f"{prefix}CLASS: {name}{base_str} (line {line}){conn_str}")

            # Add methods indented
            methods = data.get('methods', [])
            for j, m in enumerate(methods):
                mname = m['name']
                mline = m['line']
                mconns = m.get('connections', [])
                mconn_str = f" → calls: {', '.join(mconns)}" if mconns else ''
                is_last_method = (j == len(methods) - 1)
                method_prefix = "    └── " if is_last_method else "    ├── "
                tree_lines.append(f"{method_prefix}METHOD: {mname}() (line {mline}){mconn_str}")

    tree_lines.append("└── Notes")
    return '\n'.join(tree_lines)


def _build_skeleton(ordered_items: list) -> str:
    """Build a skeleton that the AI must fill in, preserving source order."""
    if not ordered_items:
        return "No items found."

    lines = []
    lines.append("# <filename>")
    lines.append("")
    lines.append("## Overview")
    lines.append("[Fill in 2-3 paragraphs]")
    lines.append("")
    lines.append("## Code Structure and Relationships")
    lines.append("[Brief overview of organization and relationships]")
    lines.append("")
    lines.append("## Imports")
    lines.append("[Document each import with purpose and usage]")
    lines.append("")
    lines.append("## Detailed Documentation (IN SOURCE ORDER)")
    lines.append("")

    for item in ordered_items:
        typ = item['type']
        data = item['data']
        line = item['line']

        if typ == 'import':
            display = data.get('display', 'import')
            lines.append(f"### IMPORT at line {line}: `{display}`")
            lines.append("[Purpose and where used]")
            lines.append("")

        elif typ == 'function':
            name = data['name']
            args = ', '.join(a['name'] for a in data.get('args', []))
            ret = data.get('returns') or 'None'
            connections = data.get('connections', [])
            conn_str = f" (calls: {', '.join(connections)})" if connections else ''
            lines.append(f"### FUNCTION at line {line}: `{name}({args}) -> {ret}`{conn_str}")
            lines.append("- **Purpose:** [What it does]")
            lines.append("- **Behavior:** [Step-by-step logic]")
            lines.append("- **Args:** [table with type, description]")
            lines.append("- **Returns:** [type and description]")
            lines.append("- **Calls:** [list connections]")
            lines.append("")

        elif typ == 'class':
            name = data['name']
            bases = ', '.join(data.get('bases', []))
            base_str = f"({bases})" if bases else ''
            connections = data.get('connections', [])
            conn_str = f" (uses: {', '.join(connections)})" if connections else ''
            lines.append(f"### CLASS at line {line}: `{name}{base_str}`{conn_str}")
            lines.append("- **Purpose:** [What it does]")
            lines.append("- **Behavior:** [How it works]")
            lines.append("- **Inherits:** " + (bases if bases else "Nothing"))
            lines.append("")
            lines.append("#### Methods:")
            for m in data.get('methods', []):
                mname = m['name']
                margs = ', '.join(a['name'] for a in m.get('args', []))
                mret = m.get('returns') or 'None'
                mline = m['line']
                mconns = m.get('connections', [])
                mconn_str = f" (calls: {', '.join(mconns)})" if mconns else ''
                lines.append(f"  #### METHOD at line {mline}: `{mname}({margs}) -> {mret}`{mconn_str}")
                lines.append(f"  - **Purpose:** [What it does]")
                lines.append(f"  - **Behavior:** [Step-by-step logic]")
                lines.append(f"  - **Args:** [table]")
                lines.append(f"  - **Calls:** [list connections]")
            lines.append("")

    lines.append("## Notes")
    lines.append("[Additional observations]")

    return '\n'.join(lines)


def _format_code_structure(ordered_items: list) -> str:
    """Format the source code structure showing items in their original order."""
    if not ordered_items:
        return '  None'
    lines = []
    for item in ordered_items:
        item_type = item.get('type')
        data = item.get('data', {})
        line = item.get('line', '?')

        if item_type == 'import':
            display = data.get('display', 'import')
            lines.append(f"  Line {line}: [IMPORT] {display}")

        elif item_type == 'function':
            name = data.get('name', '?')
            connections = data.get('connections', [])
            conn_str = f" -> calls: {', '.join(connections)}" if connections else ''
            lines.append(f"  Line {line}: [FUNCTION] {name}(){conn_str}")

        elif item_type == 'class':
            name = data.get('name', '?')
            bases = data.get('bases', [])
            base_str = f"({', '.join(bases)})" if bases else ''
            class_connections = data.get('connections', [])
            conn_str = f" -> uses: {', '.join(class_connections)}" if class_connections else ''
            lines.append(f"  Line {line}: [CLASS] {name}{base_str}{conn_str}")
            # Show methods indented
            for method in data.get('methods', []):
                method_name = method.get('name')
                method_line = method.get('line')
                method_connections = method.get('connections', [])
                method_conn_str = f" -> uses: {', '.join(method_connections)}" if method_connections else ''
                lines.append(f"    Line {method_line}: [METHOD] {method_name}(){method_conn_str}")

    return '\n'.join(lines)


def get_file_docs_prompt(file_path: str, module_doc: str, imports: list, functions: list, classes: list, ordered_items: list = None) -> str:
    # Handle both string imports (old) and dict imports (new)
    import_displays = []
    for imp in imports:
        if isinstance(imp, dict):
            import_displays.append(imp.get('display', str(imp)))
        else:
            import_displays.append(str(imp))

    # Build the ordered skeleton that AI must fill in (preserves source order)
    skeleton = _build_skeleton(ordered_items)
    structure_tree = _build_structure_tree(ordered_items)

    # Build the prompt using string concatenation to avoid f-string issues with curly braces
    prompt = """
You are an expert Python documentation generator producing EXTREMELY DETAILED documentation.

File: """ + file_path + """
Module docstring: """ + str(module_doc) + """
Imports: """ + ', '.join(import_displays) + """

## Code Structure (Visual Tree - MUST FOLLOW EXACTLY):
""" + structure_tree + """

CRITICAL RULES:
1. The "Code Structure" tree above shows the EXACT order and hierarchy of items in the source file.
2. You MUST document items in this EXACT same order - do NOT group or rearrange.
3. If the tree shows: CLASS -> FUNCTION -> CLASS, your docs MUST be: CLASS -> FUNCTION -> CLASS.
4. For each class, document methods IN THE ORDER they appear in the source.

YOUR TASK: Generate COMPLETE, EXTREMELY DETAILED documentation for each item in the EXACT order shown above.

# <filename>

## Overview
(Write 3-5 detailed paragraphs covering):
- What this module does in detail
- Main purpose and use cases
- Key components and how they interact
- Design patterns used
- Overall architecture

## Code Structure and Relationships

### Visual Structure Tree
""" + structure_tree + """

### Dependency Analysis
(Explain the relationships between components):
- Which functions call which other functions
- Inheritance hierarchy
- Data flow through the module
- Circular dependencies (if any)

## Imports
For EACH import, provide DETAILED information:
| Import | Purpose | Where Used | Notes |
|--------|---------|----------|-------|
| ... | ... | ... | ... |

## Detailed Documentation (IN EXACT SOURCE ORDER)

""" + skeleton + """

## Testing Recommendations
- How to unit test each function/class
- Integration test scenarios
- Edge cases to test
- Mock recommendations

## Potential Improvements
(Only if you spot genuine issues):
- Performance optimizations
- Missing error handling
- Code quality improvements

## Notes
- Additional observations
- Warnings about the code
- Compatibility issues

Rules:
- Respond with ONLY the markdown. No preamble.
- You MUST keep the exact order from the tree above.
- Be EXTREMELY detailed - document every aspect.
- Use tables for parameters. Use code blocks for examples.
- Professional and publication-ready output.
"""
    return prompt
