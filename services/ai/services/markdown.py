import re


def sanitize_markdown(text: str) -> str:
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
