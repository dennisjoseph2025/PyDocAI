import os
import sys
import ast
import importlib
import json
import re
import time
import zipfile
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

def should_exclude_path(path: Path) -> bool:
    """Check if the path should be excluded from analysis."""
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'staticfiles', 'media', '.gemini', 'scratch'}
    exclude_files = {'.DS_Store', 'db.sqlite3', '.env'}
    
    if path.name in exclude_files:
        return True
    
    return any(part in exclude_dirs for part in path.parts)

def extract_project_structure_from_zip(zip_path: str) -> Dict[str, Any]:
    """Extract structure directly from a zip file without extracting it."""
    structure = {'root_files': [], 'app_directories': [], 'subdirectories': {}, 'python_files': [], 'config_files': {}, 'total_files': 0, 'project_tree': ""}
    with zipfile.ZipFile(zip_path, 'r') as zf:
        namelist = zf.namelist()
        structure['total_files'] = len(namelist)
        structure['project_tree'] = "\n".join(namelist[:100]) # truncated for brevity
    return structure

def extract_project_structure(project_path: str) -> Dict[str, Any]:
    """Extract comprehensive project structure information."""
    structure = {
        'root_files': [],
        'app_directories': [],
        'subdirectories': {},
        'python_files': [],
        'config_files': {},
        'total_files': 0,
        'project_tree': ""
    }
    
    root_path = Path(project_path)
    
    def is_django_app(dir_path: Path) -> bool:
        return (dir_path / 'apps.py').exists() or (dir_path / 'models.py').exists()
    
    def scan_directory(dir_path: Path):
        for item in dir_path.iterdir():
            if should_exclude_path(item):
                continue
            
            if item.is_file():
                if item.suffix == '.py':
                    structure['python_files'].append({
                        'name': item.name,
                        'path': str(item.relative_to(root_path))
                    })
                elif item.name in ('requirements.txt', 'pyproject.toml', 'Dockerfile', 'docker-compose.yml'):
                    structure['config_files'][item.name] = str(item.relative_to(root_path))
                else:
                    structure['root_files'].append({
                        'name': item.name,
                        'path': str(item.relative_to(root_path))
                    })
            elif item.is_dir():
                if is_django_app(item):
                    app_files = []
                    for sub_item in item.rglob('*'):
                        if sub_item.is_file() and not should_exclude_path(sub_item):
                            app_files.append({
                                'name': sub_item.name,
                                'path': str(sub_item.relative_to(root_path))
                            })
                    structure['app_directories'].append({
                        'name': item.name,
                        'path': str(item.relative_to(root_path)),
                        'files': app_files
                    })
                else:
                    structure['subdirectories'][item.name] = str(item.relative_to(root_path))
    
    try:
        scan_directory(root_path)
    except:
        pass
    
    # Generate a full project tree string
    main_project_dir = None
    for item in root_path.iterdir():
        if item.is_dir() and item.name.lower() not in ('__pycache__', 'migrations', '.git', 'venv', '.venv', 'node_modules', 'tmp'):
            if any((item / f).exists() for f in ['apps.py', 'models.py', 'views.py', 'urls.py', 'manage.py', 'settings.py']) or item.name.lower() in ['apps', 'src', 'backend', 'project']:
                main_project_dir = item
                break
    
    if not main_project_dir:
        for item in root_path.iterdir():
            if item.is_dir() and item.name.lower() not in ('__pycache__', 'migrations', '.git', 'venv', '.venv', 'node_modules'):
                main_project_dir = item
                break
    
    tree_lines = []
    
    def build_tree_str(dir_path: Path, prefix="", is_root=False):
        try:
            items = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_dir(), x.name))
            for i, item in enumerate(items):
                if should_exclude_path(item):
                    continue
                is_last = (i == len(items) - 1)
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{connector}{item.name}")
                if item.is_dir():
                    if item.name == 'migrations':
                        continue
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    build_tree_str(item, new_prefix, False)
        except:
            pass
    
    if main_project_dir:
        tree_lines.append(f"{main_project_dir.name}/")
        build_tree_str(main_project_dir, "", False)
    else:
        tree_lines.append(f"{root_path.name}/")
        build_tree_str(root_path, "", False)
    
    structure['project_tree'] = "\n".join(tree_lines)
    
    structure['total_files'] = len(structure['python_files']) + sum(
        len(app['files']) for app in structure['app_directories']
    )
    
    return structure

def extract_dependencies(project_path: str) -> Dict[str, List[str]]:
    """Extract production and development dependencies from requirements files and pyproject.toml."""
    deps = {'production': [], 'development': []}
    
    def read_req_file(filepath, category):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-r'):
                        deps[category].append(line)
        except:
            pass

    # Walk project to find all requirements files
    for root, dirs, files in os.walk(project_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            fname_lower = fname.lower()
            if fname_lower in ('requirements.txt', 'base.txt'):
                read_req_file(fpath, 'production')
            elif fname_lower in ('development.txt', 'dev.txt', 'requirements-dev.txt', 'requirements_dev.txt'):
                read_req_file(fpath, 'development')
            elif fname_lower in ('production.txt', 'prod.txt', 'requirements-prod.txt'):
                read_req_file(fpath, 'production')

    # Try pyproject.toml (handles uv/poetry style)
    for root, dirs, files in os.walk(project_path):
        if 'pyproject.toml' in files:
            pyproject_path = os.path.join(root, 'pyproject.toml')
            try:
                try:
                    tomllib = importlib.import_module("tomllib")
                except ImportError:
                    tomllib = importlib.import_module("tomli")
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                project_deps = data.get("project", {}).get("dependencies", [])
                deps['production'].extend(project_deps)
                dev_deps = (
                    data.get("tool", {}).get("poetry", {}).get("dev-dependencies", {})
                )
                if isinstance(dev_deps, dict):
                    deps['development'].extend(dev_deps.keys())
            except:
                pass

    def dedup(dep_list):
        """Keep the versioned entry if both bare name and versioned entry exist."""
        seen = {}
        for dep in sorted(dep_list):
            name = dep.split('>=')[0].split('<=')[0].split('==')[0].split('>')[0].split('<')[0].strip().lower()
            # Prefer entry with version specifier
            if name not in seen or ('>' in dep or '=' in dep or '<' in dep):
                seen[name] = dep
        return sorted(seen.values())

    deps['production'] = dedup(deps['production'])
    deps['development'] = dedup(deps['development'])
    return deps

def get_py_file_contents(project_path: str, max_files: int = 30) -> Dict[str, str]:
    """Extract ONLY urls.py and views.py raw source code.
    
    All other files (models, serializers, admin, apps, tests, management
    commands) are fully captured by structured AST data. Sending both AST
    + raw source duplicates information and bloats the prompt. Raw source
    is only needed for business logic — urls.py (route definitions) and
    views.py (endpoint handlers).
    """
    contents = {}
    target_names = {'urls.py', 'routers.py', 'views.py', 'api.py'}
    
    for root, _, files in os.walk(project_path):
        if any(part in {'.git', '__pycache__', 'venv', '.venv'} for part in Path(root).parts):
            continue
        for f in files:
            if f.lower() in target_names and 'migration' not in f.lower():
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, project_path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        if f.lower() in ['urls.py', 'routers.py']:
                            contents[rel_path] = content[:600]
                        else:
                            contents[rel_path] = content[:1000]
                        if len(contents) >= max_files:
                            return contents
                except:
                    pass
    
    return contents

def generate_project_summary(project_name: str, project_path: str, user_description: str = None, custom_info: Dict = None, parsed_ast_data: list = None) -> Dict[str, Any]:
    """Build a comprehensive summary of the project by analyzing all files."""
    structure = extract_project_structure(project_path)
    dependencies = extract_dependencies(project_path)
    file_contents = get_py_file_contents(project_path)
    
    return {
        'project_name': project_name,
        'framework': 'Django',
        'file_structure': structure,
        'dependencies': dependencies,
        'user_description': user_description,
        'custom_details': custom_info,
        'file_contents': file_contents,
        'parsed_ast_data': parsed_ast_data
    }

def _format_ast_for_ai(parsed_data: list) -> str:
    """Format AST data densely to save tokens while keeping architectural context."""
    if not parsed_data:
        return "No AST data"
    
    lines = []
    for item in parsed_data:
        file_path = item.get('file_path', 'unknown.py')
        parsed = item.get('parsed', {})
        if not isinstance(parsed, dict):
            continue
            
        classes = parsed.get('classes', [])
        functions = parsed.get('functions', [])
        
        if not classes and not functions:
            continue
            
        lines.append(f"\n--- FILE: {file_path} ---")
        
        for c in classes:
            doc = c.get('docstring', '')
            doc = f" - {doc[:100]}" if doc else ""
            lines.append(f"Class: {c.get('name')}{doc}")
            for m in c.get('methods', []):
                args = [a.get('name', '') for a in m.get('args', [])]
                lines.append(f"  Method: {m.get('name')}({','.join(args)})")
                
        for f in functions:
            args = [a.get('name', '') for a in f.get('args', [])]
            doc = f.get('docstring', '')
            doc = f" - {doc[:100]}" if doc else ""
            lines.append(f"Function: {f.get('name')}({','.join(args)}){doc}")
            
    return "\n".join(lines)[:5000]

def create_unified_prompt(summary: Dict[str, Any]) -> str:
    """Create a prompt that requests a single JSON response for all docs."""
    tree = summary.get('file_structure', {}).get('project_tree', '')
    contents_dict = summary.get('file_contents', {})
    contents = json.dumps(contents_dict, indent=2)
    if len(contents) > 2000:
        contents = contents[:2000] + '\n[...content truncated for size...]'
    parsed_data = summary.get('parsed_ast_data', [])
    if not parsed_data and summary.get('file_contents'):
        try:
            for filepath, file_content in summary['file_contents'].items():
                parsed_data.append({'file': filepath, 'ast_nodes': len(ast.parse(file_content).body)})
        except: pass
        ast_data = json.dumps(parsed_data, indent=2) if parsed_data else "Not provided"
    else:
        ast_data = _format_ast_for_ai(parsed_data)
        
    custom = json.dumps(summary.get('custom_details', {}), indent=2) if summary.get('custom_details') else "None"
    common_libs = ['django', 'flask', 'fastapi', 'celery', 'redis', 'psycopg2', 'sqlalchemy', 'requests', 'httpx', 'pydantic', 'numpy', 'pandas', 'pillow', 'bcrypt', 'passlib', 'jwt', 'pyjwt', 'cryptography', 'google', 'openai', 'anthropic', 'groq', 'gunicorn', 'uvicorn', 'weasyprint', 'markdown', 'pygithub', 'djangorestframework', 'simplejwt', 'corsheaders']
    all_imports = set()
    for item in summary.get('parsed_ast_data', []):
        parsed = item.get('parsed', {})
        for imp in parsed.get('imports', []):
            if isinstance(imp, dict):
                imp_name = imp.get('display', '').split('.')[0]
            else:
                imp_name = str(imp).split('.')[0]
            if imp_name and imp_name.lower() not in ('os', 'sys', 're', 'json', 'datetime', 'typing', 'collections', 'functools', 'itertools', 'pathlib', 'abc', 'ast', 'inspect', 'logging'):
                all_imports.add(imp_name)
    
    detected_deps = [dep for dep in common_libs if any(dep.lower() in imp.lower() for imp in all_imports)]
    deps_info = ', '.join(detected_deps) if detected_deps else "No external dependencies detected from code analysis"

    return f"""You are an expert software architect documenting a Python project.

PROJECT NAME: {summary['project_name']}
USER DESCRIPTION: {summary.get('user_description', 'No description')}
EXTRA PROJECT DETAILS: {custom}
DETECTED DEPENDENCIES: {deps_info}

FILE STRUCTURE:
```text
{tree}
```

AST PARSED DATA:
{ast_data}

CORE FILE CONTENTS:
{contents}

TASK: Generate three documentation assets as a SINGLE JSON object. Use ONLY the code provided above. Do NOT hallucinate files or endpoints.

REQUIRED JSON FORMAT:
{{
  "summary": "Detailed project summary in MARKDOWN. Sections: ## Project Overview (3-4 paragraphs), ## Architecture Analysis (patterns, component interactions), ## App-by-App Breakdown (for each app: role, models with fields/relationships, views/serializers logic, connections), ## Data Flow & Relationships (model relationships, request lifecycle), ## Dependency Analysis (how each dependency is used in THIS project), ## Technology Stack, ## Architecture Diagram (valid mermaid.js flowchart using 'A --> B' or 'A -->|label| B' syntax only).",
  "readme": "Comprehensive README.md in MARKDOWN. Sections: # Project Title, ## Introduction (3-4 paragraphs), ## Features (all features grouped by category with descriptions), ## Prerequisites, ## Dependencies (explain each major dependency), ## Installation (step-by-step), ## Configuration (env vars), ## Quick Start, ## Project Structure (EXACT file tree from above, do not alter), ## API Overview (endpoint table), ## Database Schema, ## Contributing.",
  "api_docs": "Detailed API documentation in MARKDOWN. Sections: # API Documentation, ## Overview, ## Authentication (JWT token flow), ## Error Handling, ## Endpoints (group by resource). For EACH endpoint found in urls.py: ### [METHOD] /path/ with **Description** (2-3 paragraphs), **Request Headers**, **Path Parameters**, **Query Parameters**, **Request Body** (JSON structure from serializers), **Response** (JSON structure), **Status Codes**. Document EVERY route. Do NOT omit any."
}}

RULES:
1. Return ONLY valid JSON. No text before or after.
2. Escape newlines as \\n and quotes as \" inside strings.
3. Mermaid: use 'A --> B' or 'A -->|label| B' only. No '-->|text|>'.
4. Be thorough and detailed in every section.
"""

def _generate_fallback_docs(project_info: dict, project_name: str) -> Dict[str, str]:
    """Generate detailed documentation from parsed AST when no AI is available."""
    file_contents = project_info.get('file_contents', {})
    parsed_ast_data = project_info.get('parsed_ast_data', [])
    
    all_files = []
    for file_path, content in file_contents.items():
        all_files.append({
            'path': file_path,
            'content': content,
            'functions': [],
            'classes': [],
            'imports': []
        })
    
    for item in parsed_ast_data:
        file_path = item.get('file_path', item.get('file', ''))
        parsed = item.get('parsed', {})
        
        matched = False
        for f in all_files:
            if f['path'] == file_path or file_path.endswith(f['path']):
                f['functions'] = parsed.get('functions', [])
                f['classes'] = parsed.get('classes', [])
                f['imports'] = parsed.get('imports', [])
                matched = True
                break
        
        if not matched and file_path:
            all_files.append({
                'path': file_path,
                'content': '',
                'functions': parsed.get('functions', []),
                'classes': parsed.get('classes', []),
                'imports': parsed.get('imports', [])
            })
    
    # Collect all imports across files
    all_imports = set()
    for file_info in all_files:
        for imp in file_info.get('imports', []):
            if isinstance(imp, dict):
                all_imports.add(imp.get('module', imp.get('display', '')))
            else:
                all_imports.add(str(imp))
    
    # Count totals
    total_functions = sum(len(f.get('functions', [])) for f in all_files)
    total_classes = sum(len(f.get('classes', [])) for f in all_files)
    total_methods = sum(
        sum(len(c.get('methods', [])) for c in f.get('classes', []))
        for f in all_files
    )
    total_lines = sum(len(f.get('content', '').splitlines()) for f in all_files)
    
    # ─── README ───
    readme = f"# {project_name}\n\n"
    
    custom_details = project_info.get('custom_details', {})
    if custom_details:
        readme += "## Project Details\n\n"
        for key, value in custom_details.items():
            if isinstance(value, list):
                readme += f"- **{key}:** {', '.join(str(v) for v in value)}\n"
            else:
                readme += f"- **{key}:** {value}\n"
        readme += "\n"
    
    user_desc = project_info.get('user_description')
    if user_desc:
        readme += f"## Description\n\n{user_desc}\n\n"
    
    readme += "## Project Overview\n\n"
    readme += f"This project contains **{len(all_files)}** Python source files with approximately **{total_lines}** lines of code. "
    readme += f"It defines **{total_functions}** functions, **{total_classes}** classes with **{total_methods}** methods.\n\n"
    
    readme += "## Features\n\n"
    readme += "Based on code analysis, the following features have been identified:\n\n"
    for f in all_files:
        funcs = f.get('functions', [])
        classes = f.get('classes', [])
        if funcs or classes:
            readme += f"### {f['path']}\n\n"
            if funcs:
                for fn in funcs:
                    doc = fn.get('docstring', '')
                    if doc:
                        readme += f"- **{fn['name']}**: {doc[:150]}{'...' if len(doc) > 150 else ''}\n"
                    else:
                        args = ', '.join(a['name'] for a in fn.get('args', []))
                        readme += f"- **{fn['name']}({args})**: Function handling specific logic\n"
            if classes:
                for cls in classes:
                    doc = cls.get('docstring', '')
                    methods = cls.get('methods', [])
                    if doc:
                        readme += f"- **{cls['name']}**: {doc[:150]}{'...' if len(doc) > 150 else ''}\n"
                    else:
                        readme += f"- **{cls['name']}**: Class with {len(methods)} methods\n"
            readme += "\n"
    
    # Dependencies
    dependencies = project_info.get('dependencies', {})
    actual_deps = []
    
    for file_info in all_files:
        file_path = file_info.get('path', '')
        content = file_info.get('content', '')
        
        if 'requirements' in file_path.lower():
            if content:
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-r'):
                        line = line.lstrip('- ')
                        line = re.sub(r'^pip install -r.*', '', line)
                        if '==' in line:
                            dep_name = line.split('==')[0].strip()
                        elif '>=' in line:
                            dep_name = line.split('>=')[0].strip()
                        elif '<=' in line:
                            dep_name = line.split('<=')[0].strip()
                        elif '~=' in line:
                            dep_name = line.split('~=')[0].strip()
                        else:
                            dep_name = re.sub(r'\[.*\].*', '', line).strip()
                        if dep_name and not any(c in dep_name for c in '<>') and len(dep_name) > 1:
                            actual_deps.append(dep_name)
    
    dep_mapping = {
        'django': ['django'],
        'djangorestframework': ['rest_framework', 'djangorestframework', 'drf'],
        'simplejwt': ['rest_framework_simplejwt', 'simplejwt', 'djangorestframework_simplejwt'],
        'corsheaders': ['corsheaders', 'django-cors-headers', 'django_cors_headers'],
        'django-environ': ['environ', 'django_environ'],
        'python-dotenv': ['dotenv', 'python_dotenv'],
        'python-decouple': ['decouple', 'python_decouple'],
        'celery': ['celery'],
        'redis': ['redis'],
        'psycopg2': ['psycopg2', 'psycopg2_binary', 'psycopg2_pool'],
        'sqlalchemy': ['sqlalchemy', 'sqlacalchemy'],
        'flask': ['flask'],
        'fastapi': ['fastapi'],
        'uvicorn': ['uvicorn'],
        'gunicorn': ['gunicorn'],
        'requests': ['requests'],
        'httpx': ['httpx'],
        'pydantic': ['pydantic'],
        'numpy': ['numpy'],
        'pandas': ['pandas'],
        'pillow': ['PIL', 'pillow'],
        'bcrypt': ['bcrypt'],
        'passlib': ['passlib'],
        'pyjwt': ['jwt', 'pyjwt'],
        'cryptography': ['cryptography'],
        'google': ['google', 'google_auth', 'google_genai'],
        'openai': ['openai'],
        'anthropic': ['anthropic'],
        'groq': ['groq'],
        'weasyprint': ['weasyprint'],
        'markdown': ['markdown'],
        'pygithub': ['github', 'PyGithub'],
        'django-filter': ['django_filter'],
        'django-crispy-forms': ['crispy_forms', 'crispy'],
        'django-allauth': ['allauth'],
        'django-celery-beat': ['django_celery_beat'],
        'django-redis': ['django_redis'],
        'channels': ['channels', 'daphne'],
    }
    
    found_deps = set()
    for imp in all_imports:
        for dep, import_names in dep_mapping.items():
            if any(name.lower() == imp.lower() for name in import_names):
                found_deps.add(dep)
                break
    
    dep_descriptions = {
        'django': 'Core web framework providing the MVC architecture, ORM, admin interface, and request handling.',
        'djangorestframework': 'REST API framework that provides serializers, viewsets, routers, and authentication for building APIs.',
        'simplejwt': 'JSON Web Token authentication for Django REST Framework, providing access and refresh token management.',
        'corsheaders': 'Cross-Origin Resource Sharing middleware for Django, allowing controlled cross-domain requests.',
        'celery': 'Distributed task queue for asynchronous background processing of long-running jobs.',
        'redis': 'In-memory data store used as Celery message broker and/or cache backend.',
        'psycopg2': 'PostgreSQL database adapter for Python, enabling Django to communicate with PostgreSQL.',
        'gunicorn': 'Production-grade WSGI HTTP server for serving Django applications.',
        'requests': 'HTTP client library for making external API requests.',
        'pillow': 'Python Imaging Library for image processing, resizing, and manipulation.',
        'markdown': 'Markdown parser for converting markdown text to HTML.',
        'pygithub': 'Python wrapper for the GitHub API, enabling repository and user management.',
        'bcrypt': 'Password hashing library using the bcrypt algorithm for secure credential storage.',
        'pyjwt': 'Library for encoding and decoding JSON Web Tokens.',
        'python-dotenv': 'Environment variable loader from .env files for configuration management.',
        'django-environ': 'Django-specific environment variable management with type casting.',
    }
    
    if found_deps:
        readme += "\n## Dependencies\n\n"
        readme += "This project uses the following main dependencies:\n\n"
        for dep in sorted(found_deps):
            desc = dep_descriptions.get(dep, 'Library used for specific functionality in this project.')
            readme += f"- **{dep}**: {desc}\n"
    
    readme += "\n## File Structure\n\n"
    readme += "The project contains the following files:\n\n"
    for f in all_files:
        funcs = f.get('functions', [])
        classes = f.get('classes', [])
        imports = f.get('imports', [])
        loc = len(f.get('content', '').splitlines())
        readme += f"### `{f['path']}`\n\n"
        readme += f"- **Lines of code:** {loc}\n"
        readme += f"- **Functions:** {len(funcs)}\n"
        readme += f"- **Classes:** {len(classes)}\n"
        readme += f"- **Imports:** {len(imports)}\n\n"
        
        if imports:
            readme += "**Key Imports:**\n\n"
            for imp in imports[:10]:
                if isinstance(imp, dict):
                    readme += f"- `{imp.get('display', str(imp))}`\n"
                else:
                    readme += f"- `{imp}`\n"
            readme += "\n"
        
        if funcs:
            readme += "**Functions:**\n\n"
            for fn in funcs:
                args = ', '.join([
                    f"{a['name']}: {a.get('type', 'Any')}" if a.get('type') else a['name']
                    for a in fn.get('args', [])
                ])
                ret = fn.get('returns', 'None')
                doc = fn.get('docstring', '')
                decorators = fn.get('decorators', [])
                conn = fn.get('connections', [])
                
                readme += f"#### `{fn['name']}({args})` → `{ret}`\n\n"
                if decorators:
                    readme += f"**Decorators:** {', '.join(decorators)}\n\n"
                if doc:
                    readme += f"**Description:** {doc}\n\n"
                if fn.get('args'):
                    readme += "**Parameters:**\n\n"
                    for a in fn.get('args'):
                        ptype = a.get('type', 'Any')
                        pname = a['name']
                        pdefault = a.get('default')
                        default_str = f" = `{repr(pdefault)}`" if pdefault else ""
                        readme += f"- `{pname}: {ptype}{default_str}`\n"
                    readme += "\n"
                if conn:
                    readme += f"**Calls:** {', '.join(f'`{c}`' for c in conn)}\n\n"
        
        if classes:
            readme += "**Classes:**\n\n"
            for cls in classes:
                bases = ', '.join(cls.get('bases', []))
                base_str = f"({bases})" if bases else ""
                doc = cls.get('docstring', '')
                methods = cls.get('methods', [])
                conn = cls.get('connections', [])
                
                readme += f"#### `{cls['name']}{base_str}`\n\n"
                if doc:
                    readme += f"**Description:** {doc}\n\n"
                if conn:
                    readme += f"**Uses:** {', '.join(f'`{c}`' for c in conn)}\n\n"
                if methods:
                    readme += "**Methods:**\n\n"
                    for m in methods:
                        margs = ', '.join([
                            f"{a['name']}: {a.get('type', 'Any')}" if a.get('type') else a['name']
                            for a in m.get('args', [])
                        ])
                        mret = m.get('returns', 'None')
                        mdoc = m.get('docstring', '')
                        mconn = m.get('connections', [])
                        
                        readme += f"- `{m['name']}({margs})` → `{mret}`"
                        if mdoc:
                            readme += f" — {mdoc[:100]}"
                        if mconn:
                            readme += f" (calls: {', '.join(f'`{c}`' for c in mconn)})"
                        readme += "\n"
                    readme += "\n"
    
    # ─── SUMMARY ───
    summary = f"# {project_name} — Project Documentation\n\n"
    summary += "## Project Overview\n\n"
    summary += f"This documentation was generated for the project **'{project_name}'** which contains **{len(all_files)}** Python source files, "
    summary += f"**{total_functions}** functions, **{total_classes}** classes with **{total_methods}** methods, and approximately **{total_lines}** lines of code.\n\n"
    
    summary += "## Architecture Analysis\n\n"
    summary += "### Code Organization\n\n"
    # Group files by directory
    dir_groups = {}
    for f in all_files:
        parts = f['path'].split('/')
        if len(parts) > 1:
            dir_name = parts[0]
            if dir_name not in dir_groups:
                dir_groups[dir_name] = []
            dir_groups[dir_name].append(f)
        else:
            if 'root' not in dir_groups:
                dir_groups['root'] = []
            dir_groups['root'].append(f)
    
    for dir_name, files in dir_groups.items():
        summary += f"### `{dir_name}/` Module\n\n"
        summary += f"Contains {len(files)} file(s):\n\n"
        for f in files:
            funcs = f.get('functions', [])
            classes = f.get('classes', [])
            summary += f"- **`{f['path']}`**: {len(funcs)} functions, {len(classes)} classes"
            # List class names
            if classes:
                class_names = ', '.join(f"`{c['name']}`" for c in classes)
                summary += f" — Classes: {class_names}"
            # List function names
            if funcs:
                func_names = ', '.join(f"`{fn['name']}`" for fn in funcs)
                summary += f" — Functions: {func_names}"
            summary += "\n"
        summary += "\n"
    
    summary += "## Data Flow & Relationships\n\n"
    summary += "### Function Call Graph\n\n"
    for f in all_files:
        for fn in f.get('functions', []):
            conn = fn.get('connections', [])
            if conn:
                summary += f"- `{fn['name']}` in `{f['path']}` calls: {', '.join(f'`{c}`' for c in conn)}\n"
        for cls in f.get('classes', []):
            conn = cls.get('connections', [])
            if conn:
                summary += f"- `{cls['name']}` in `{f['path']}` uses: {', '.join(f'`{c}`' for c in conn)}\n"
            for m in cls.get('methods', []):
                mconn = m.get('connections', [])
                if mconn:
                    summary += f"  - `{cls['name']}.{m['name']}` calls: {', '.join(f'`{c}`' for c in mconn)}\n"
    summary += "\n"
    
    summary += "## How This Documentation Was Generated\n\n"
    summary += "### Step 1: File Upload & Extraction\n"
    summary += f"When the ZIP file was uploaded, it was extracted and {len(all_files)} Python files were identified and read.\n\n"
    summary += "### Step 2: AST Parsing (Code Analysis)\n"
    summary += "Each Python file was parsed using Python's Abstract Syntax Tree (AST) module, extracting:\n"
    summary += "- **Imports**: All imported modules and their usage\n"
    summary += "- **Functions**: Standalone functions with parameters, return types, docstrings, and decorators\n"
    summary += "- **Classes**: Class definitions with base classes, attributes, methods, and docstrings\n"
    summary += "- **Connections**: Cross-references between functions, classes, and methods\n\n"
    summary += "### Step 3: Documentation Generation\n"
    summary += "The extracted information was processed to create this comprehensive documentation.\n\n"
    
    # ─── API DOCS ───
    api_docs = f"# API Documentation — {project_name}\n\n"
    api_docs += "## Overview\n\n"
    api_docs += f"This document provides a complete reference of all **{total_functions}** functions and **{total_methods}** methods "
    api_docs += f"found across **{len(all_files)}** files in the project.\n\n"
    
    # Group by file
    for f in all_files:
        funcs = f.get('functions', [])
        classes = f.get('classes', [])
        if funcs or classes:
            api_docs += f"## `{f['path']}`\n\n"
            
            # File-level imports
            imports = f.get('imports', [])
            if imports:
                api_docs += "**Imports:**\n\n"
                for imp in imports:
                    if isinstance(imp, dict):
                        api_docs += f"- `{imp.get('display', str(imp))}`\n"
                    else:
                        api_docs += f"- `{imp}`\n"
                api_docs += "\n"
            
            # Functions
            for fn in funcs:
                args_str = ', '.join([
                    f"{a['name']}: {a.get('type', 'Any')}" if a.get('type') else a['name'] 
                    for a in fn.get('args', [])
                ])
                ret = fn.get('returns', 'None')
                doc = fn.get('docstring', 'No docstring provided')
                decorators = fn.get('decorators', [])
                conn = fn.get('connections', [])
                line = fn.get('line', '?')
                
                api_docs += f"### `{fn['name']}({args_str})` → `{ret}`\n\n"
                api_docs += f"**Line:** {line}\n\n"
                
                if decorators:
                    api_docs += f"**Decorators:**\n\n"
                    for dec in decorators:
                        api_docs += f"- `{dec}`\n"
                    api_docs += "\n"
                
                api_docs += f"**Description:** {doc}\n\n"
                
                if fn.get('args'):
                    api_docs += "**Parameters:**\n\n"
                    api_docs += "| Parameter | Type | Default | Description |\n"
                    api_docs += "|-----------|------|---------|-------------|\n"
                    for a in fn.get('args'):
                        ptype = a.get('type', 'Any')
                        pname = a['name']
                        pdefault = a.get('default')
                        pdoc = a.get('docstring', '—')
                        default_str = f"`{repr(pdefault)}`" if pdefault else "—*"
                        api_docs += f"| `{pname}` | `{ptype}` | {default_str} | {pdoc} |\n"
                    api_docs += "\n"
                
                if ret != 'None':
                    api_docs += f"**Returns:** `{ret}`\n\n"
                
                if conn:
                    api_docs += f"**Calls:** {', '.join(f'`{c}`' for c in conn)}\n\n"
            
            # Classes
            for cls in classes:
                bases = ', '.join(cls.get('bases', []))
                base_str = f"({bases})" if bases else ""
                doc = cls.get('docstring', 'No docstring provided')
                methods = cls.get('methods', [])
                conn = cls.get('connections', [])
                line = cls.get('line', '?')
                
                api_docs += f"### `class {cls['name']}{base_str}`\n\n"
                api_docs += f"**Line:** {line}\n\n"
                api_docs += f"**Description:** {doc}\n\n"
                
                if conn:
                    api_docs += f"**Uses:** {', '.join(f'`{c}`' for c in conn)}\n\n"
                
                if methods:
                    api_docs += "#### Methods\n\n"
                    for m in methods:
                        margs_str = ', '.join([
                            f"{a['name']}: {a.get('type', 'Any')}" if a.get('type') else a['name'] 
                            for a in m.get('args', [])
                        ])
                        mret = m.get('returns', 'None')
                        mdoc = m.get('docstring', 'No docstring')
                        mconn = m.get('connections', [])
                        mline = m.get('line', '?')
                        is_private = m.get('is_private', False)
                        visibility = "🔒 Private" if is_private else "🌐 Public"
                        
                        api_docs += f"##### `{m['name']}({margs_str})` → `{mret}`\n\n"
                        api_docs += f"**Line:** {mline} | **Visibility:** {visibility}\n\n"
                        api_docs += f"**Description:** {mdoc}\n\n"
                        
                        if m.get('args'):
                            api_docs += "**Parameters:**\n\n"
                            api_docs += "| Parameter | Type | Default | Description |\n"
                            api_docs += "|-----------|------|---------|-------------|\n"
                            for a in m.get('args'):
                                ptype = a.get('type', 'Any')
                                pname = a['name']
                                pdefault = a.get('default')
                                pdoc = a.get('docstring', '—')
                                default_str = f"`{repr(pdefault)}`" if pdefault else "—*"
                                api_docs += f"| `{pname}` | `{ptype}` | {default_str} | {pdoc} |\n"
                            api_docs += "\n"
                        
                        if mret != 'None':
                            api_docs += f"**Returns:** `{mret}`\n\n"
                        
                        if mconn:
                            api_docs += f"**Calls:** {', '.join(f'`{c}`' for c in mconn)}\n\n"
            
            api_docs += "\n---\n\n"
    
    return {
        'readme': readme,
        'summary': summary,
        'api_docs': api_docs
    }


def _sanitize_markdown(text: str) -> str:
    """Clean up AI-generated markdown to fix common formatting issues."""
    if not text:
        return text
    
    # Fix broken code fences: ```json { ... } without proper closing
    text = re.sub(r'```json\s*\{', '\n```json\n{', text)
    text = re.sub(r'\}\s*```', '\n}\n```\n', text)
    
    # Fix orphaned "code" and "Copy" text (AI artifacts)
    text = re.sub(r'\n\s*code\s*\n\s*Copy\s*\n', '\n', text)
    
    # Ensure mermaid code blocks are properly formatted
    text = re.sub(r'```mermaid\s*\n', '\n```mermaid\n', text)
    text = re.sub(r'\n\s*graph\s+(?:LR|RL|BT|TD)?', '\ngraph TD', text)
    
    # Ensure blank line before headings
    text = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', text)
    
    # Ensure blank line after headings
    text = re.sub(r'(#{1,6} .+)\n([^\n#])', r'\1\n\n\2', text)
    
    # Ensure blank line before list items that follow non-list content
    text = re.sub(r'([^\n\-*])\n(\s*[-*] )', r'\1\n\n\2', text)
    
    # Ensure blank line after list blocks before headings
    text = re.sub(r'(\n\s*[-*] .+)\n+(#{1,6} )', r'\1\n\n\2', text)
    
    # Fix missing markdown formatting on list items
    text = re.sub(r'^(?<!\n)(- \*\*)', r'\n\1', text, flags=re.MULTILINE)
    
    # Remove duplicate blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def _call_ai_unified(prompt: str) -> Dict[str, str]:
    """Call Groq AI with fallback key and return parsed JSON."""
    from django.conf import settings
    
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    groq_key_2 = getattr(settings, 'GROQ_API_KEY_2', None)

    print(f"[AI] GROQ_API_KEY loaded: {'YES' if groq_key else 'NO'} (len={len(groq_key) if groq_key else 0})")
    print(f"[AI] GROQ_API_KEY_2 loaded: {'YES' if groq_key_2 else 'NO'} (len={len(groq_key_2) if groq_key_2 else 0})")

    if not groq_key and not groq_key_2:
        raise Exception("GROQ_API_KEY not configured.")

    def sanitize_ai_json(raw: str) -> dict:
        """Robustly sanitize and parse AI-generated JSON."""
        raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', raw)
        valid_escapes = set('"\\/bfnrtu')
        def fix_escape(m):
            char = m.group(1)
            if char in valid_escapes:
                return m.group(0)
            return char
        raw = re.sub(r'\\(.)', fix_escape, raw)
        parsed = json.loads(raw)
        for key in parsed:
            if isinstance(parsed[key], str):
                parsed[key] = _sanitize_markdown(parsed[key])
        return parsed

    def extract_json(content: str) -> dict:
        """Extract JSON from AI response content."""
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return sanitize_ai_json(match.group())
        raise ValueError("No JSON object found in response")

    from groq import Groq

    # Try primary key first, then fallback key
    groq_keys = []
    if groq_key:
        groq_keys.append(('primary', groq_key))
    if groq_key_2:
        groq_keys.append(('fallback', groq_key_2))

    for key_name, key in groq_keys:
        print(f"[AI] Trying Groq key: {key_name} ({len(key)} chars, starts with {key[:8]}...)")
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
            )
            content = response.choices[0].message.content
            print(f"[AI] Groq {key_name} succeeded! Response length: {len(content)}")
            return extract_json(content)
        except Exception as e:
            print(f"[AI] Groq {key_name} key failed: {type(e).__name__}: {e}")

    raise Exception("All Groq API keys failed.")

def generate_project_docs(project_path: str, project_name: str = None, user_description: str = None, custom_info: Dict = None, use_ai: bool = True, parsed_ast_data: list = None) -> Dict[str, Any]:
    """Main entry point for generating documentation."""
    if not project_name:
        project_name = os.path.basename(project_path.rstrip('/\\'))
    
    print(f"[DEBUG] generate_project_docs called for: {project_name}")
    print(f"[DEBUG] project_path: {project_path}")
    print(f"[DEBUG] parsed_ast_data provided: {parsed_ast_data}")
    
    project_info = generate_project_summary(project_name, project_path, user_description, custom_info, parsed_ast_data)
    
    print(f"[DEBUG] project_info keys: {project_info.keys()}")
    print(f"[DEBUG] file_contents count: {len(project_info.get('file_contents', {}))}")
    print(f"[DEBUG] parsed_ast_data count: {len(project_info.get('parsed_ast_data', []))}")
    
    fallback_docs = _generate_fallback_docs(project_info, project_name)
    print(f"[DEBUG] fallback readme length: {len(fallback_docs.get('readme', ''))}")
    
    if not use_ai:
        return {
            'readme': fallback_docs.get('readme', ''),
            'summary': fallback_docs.get('summary', ''),
            'api_docs': fallback_docs.get('api_docs', ''),
            'project_info': project_info,
            'ai_available': False
        }

    ai_succeeded = False
    try:
        start_time = time.time()
        unified_docs = _call_ai_unified(create_unified_prompt(project_info))
        duration = time.time() - start_time
        print(f"AI Generation took {duration:.2f} seconds")
        ai_succeeded = True
        return {
            'readme': unified_docs.get('readme', ''),
            'summary': unified_docs.get('summary', ''),
            'api_docs': unified_docs.get('api_docs', ''),
            'project_info': project_info,
            'ai_available': True
        }
    except Exception as e:
        print(f"AI enhancement failed: {e}")
        traceback.print_exc()
        
        readme_note = "\n\n---\n\n> **Note:** AI enhancement is currently unavailable. The documentation below is generated from code analysis."
        summary_note = "\n\n---\n\n> **Note:** AI enhancement is currently unavailable. The documentation below is generated from code analysis."
        api_note = "\n\n---\n\n> **Note:** AI enhancement is currently unavailable. The documentation below is generated from code analysis."
        
        return {
            'readme': fallback_docs.get('readme', '') + readme_note,
            'summary': fallback_docs.get('summary', '') + summary_note,
            'api_docs': fallback_docs.get('api_docs', '') + api_note,
            'project_info': project_info,
            'ai_available': False
        }