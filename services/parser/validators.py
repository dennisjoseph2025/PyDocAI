import ast


def validate_python_code(source_code: str) -> tuple:
    if not source_code or not source_code.strip():
        return False, "Code cannot be empty"

    try:
        ast.parse(source_code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError on line {e.lineno}: {e.msg}"


EXCLUDED_DIRS = {
    'venv', '.venv', 'env', '.env',
    'virtualenv', '.virtualenv',
    'node_modules', 'site-packages',
    '__pycache__', '.pytest_cache',
    'build', 'dist', '*.egg-info',
    '.git', '.github', '.gitignore',
    '.vscode', '.idea',
    'migrations',
    'media',
    'staticfiles',
}


def should_exclude(file_path: str) -> bool:
    parts = file_path.replace('\\', '/').split('/')
    for part in parts:
        if part in EXCLUDED_DIRS:
            return True
        if part.endswith('.egg-info') or part.endswith('.dist-info'):
            return True
    return False
