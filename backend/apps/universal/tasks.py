import io
import logging
import os
import zipfile

import requests
from celery import shared_task
from groq import Groq
from django.conf import settings

from apps.projects.models import Project, ProjectFile
from apps.universal.prompts import get_prompt, MAX_SOURCE_CHARS

logger = logging.getLogger(__name__)

FILE_PRIORITY_KEYWORDS = [
    (10, ['urls.py', 'routes.py', 'router', 'main.py', 'app.py',
          'manage.py', 'wsgi.py', 'asgi.py', 'index.js', 'index.ts',
          'index.jsx', 'index.tsx', 'entry', 'server.js', 'server.ts',
          'app.js', 'app.ts', 'app.jsx', 'app.tsx']),
    (8, ['views.py', 'controllers.py', 'handlers.py', 'serializers.py',
         'schemas.py', 'resolver']),
    (7, ['models.py', 'entities.py', 'database.py', 'schema.prisma',
         'migration']),
    (6, ['requirements.txt', 'pyproject.toml', 'package.json', 'Dockerfile',
         'docker-compose.yml', '.env.example', 'settings', 'config',
         'tailwind.config', 'vite.config', 'next.config', 'webpack.config']),
    (5, ['services.py', 'repositories.py', 'middleware.py', 'middleware.',
         'decorators.py', 'permissions.py', 'auth.py', 'authentication']),
    (4, ['admin.py', 'forms.py', 'tasks.py', 'apps.py',
         'tests.py', 'test_', '_test.', 'spec.', 'cypress', 'jest']),
    (3, ['utils.py', 'helpers.py', 'constants.py', 'types.py',
         'exceptions.py', 'filters.py', 'pagination.py',
         'signals.py', 'context_processors.py']),
    (2, ['css', '.scss', '.less', '.svg', '.png', '.jpg', '.ico',
         'locale', 'translation', 'messages.']),
]


def _file_priority(path):
    name = (path or '').lower()
    for score, keywords in FILE_PRIORITY_KEYWORDS:
        for kw in keywords:
            if kw.lower() in name:
                return score
    return 1


def _build_file_tree(file_paths):
    tree = {}
    for path in sorted(file_paths):
        parts = path.replace('\\', '/').split('/')
        node = tree
        for part in parts:
            node = node.setdefault(part, {})
    return tree


def _format_tree(tree, prefix=''):
    lines = []
    items = sorted(tree.items(), key=lambda x: (isinstance(x[1], dict) and len(x[1]) == 0, x[0]))
    for i, (name, subtree) in enumerate(items):
        is_last = i == len(items) - 1
        connector = '└── ' if is_last else '├── '
        if isinstance(subtree, dict) and subtree:
            lines.append(f'{prefix}{connector}{name}/')
            extension = '    ' if is_last else '│   '
            lines.extend(_format_tree(subtree, prefix + extension))
        else:
            lines.append(f'{prefix}{connector}{name}')
    return lines


def _detect_req_files(file_list):
    req_patterns = {p.lower() for p in [
        'requirements.txt', 'pyproject.toml', 'Pipfile',
        'package.json', 'composer.json', 'Cargo.toml',
        'Gemfile', 'go.mod', 'build.gradle', 'pom.xml',
    ]}
    found = []
    for f in file_list:
        name = f.lower().split('/')[-1]
        if name in req_patterns:
            found.append(f)
    return found


def _validate_and_fix_output(output, github_url, project_name, file_tree, file_list):
    """Check generated docs for common errors and fix via a corrective prompt."""
    repo_dir = ''
    if github_url:
        repo_dir = github_url.rstrip('/').split('/')[-1].replace('.git', '')
    if not repo_dir:
        repo_dir = project_name

    errors = []

    # Check 1: cd command after git clone uses the wrong directory
    import re
    clone_blocks = re.findall(r'```(?:bash|sh|shell)?\s*\n(git clone[^\n]*)\n(cd [^\n]*)', output)
    for clone_line, cd_line in clone_blocks:
        cd_dir = cd_line.replace('cd ', '').strip()
        if cd_dir != repo_dir:
            errors.append(
                f"Wrong cd directory '{cd_dir}' after `{clone_line}`. "
                f"Must be '{repo_dir}' (the cloned repo name)."
            )

    # Check 2: referenced paths exist in file tree
    path_refs = re.findall(r'`([^`]+)`', output)
    file_set = set(f.lower() for f in file_list)
    for ref in path_refs:
        ref_lower = ref.lower()
        if '/' in ref and not ref_lower.startswith('http') and not ref_lower.startswith('api'):
            # Skip common false positives
            if any(ref_lower.endswith(ext) for ext in ['.png', '.jpg', '.svg', '.ico', '.md']):
                continue
            if ref_lower in file_set:
                continue
            parts = ref_lower.split('/')
            if len(parts) >= 2:
                matched = any(parts[-1] in f or f.endswith('/' + parts[-1]) for f in file_set)
                if not matched and len(parts) >= 3:
                    # Might be a hallucinated path — flag it
                    pass

    if errors:
        logger.warning(f"Output validation found {len(errors)} issue(s), sending corrective prompt")
        correction_prompt = (
            "The following documentation was generated but has errors. "
            "Fix ONLY the specific issues listed below. Output ONLY the corrected markdown, nothing else.\n\n"
            "Errors:\n" + "\n".join(f"- {e}" for e in errors) +
            f"\n\nFile tree for reference:\n{file_tree}\n\n"
            f"Here is the documentation to fix:\n\n{output}"
        )
        try:
            fixed = _call_groq(correction_prompt)
            return fixed
        except Exception as e:
            logger.warning(f"Correction attempt failed: {e}, returning original output")

    return output


def _call_groq(prompt, model="llama-3.3-70b-versatile"):
    keys = [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_2"),
    ]
    last_error = None
    for key in keys:
        if not key:
            continue
        try:
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3000,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            logger.warning(f"Groq key failed: {e}")
    raise last_error or Exception("No Groq API keys available")


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_universal_docs_task(self, project_id, mode):
    project = None
    try:
        project = Project.objects.get(id=project_id)
        project.status = Project.Status.PROCESSING
        project.save()

        files = project.files.all()
        skip_dirs = {'node_modules', 'vendor', '.git', '__pycache__', '.next', 'dist', 'build',
                     '.venv', 'venv', 'env', '.tox', 'eggs', 'bundle', '.gem',
                     '.gradle', 'target', 'bin', 'obj', '.idea', '.vscode',
                     '.settings', '.metadata', 'tmp', 'temp', 'logs',
                     '.npm', '.yarn', '.pytest_cache', '.mypy_cache',
                     '.serverless', '.terraform', 'Pods', '.swiftpm'}
        files = [f for f in files if not any(
            seg in (f.file_path or '').lower().split('/') for seg in skip_dirs
        )]
        source_parts = []
        file_list = []
        for f in files:
            file_list.append(f.file_path or f.file_name)
            content = (f.content or '').replace('\x00', '')
            if content:
                source_parts.append((f.file_path or f.file_name, content))

        source_parts.sort(key=lambda x: _file_priority(x[0]), reverse=True)

        source_code_lines = []
        for path, content in source_parts:
            source_code_lines.append(f"--- {path} ---\n{content}")

        source_code = "\n\n".join(source_code_lines) if source_code_lines else ""

        tree = _build_file_tree(file_list)
        tree_text = '\n'.join(_format_tree(tree))
        req_files = _detect_req_files(file_list)

        max_chars = MAX_SOURCE_CHARS
        for attempt in range(3):
            prompt = get_prompt(mode, source_code, project.name, file_list,
                                max_chars, github_url=project.github_url or '',
                                file_tree=tree_text, req_files=req_files)
            try:
                result = _call_groq(prompt).replace('\x00', '')
                break
            except Exception as e:
                err_str = str(e)
                is_too_large = '413' in err_str or 'rate_limit_exceeded' in err_str or 'Request too large' in err_str
                if is_too_large and attempt < 2:
                    max_chars = max_chars // 2
                    logger.warning(f"Request too large, retrying with MAX_SOURCE_CHARS={max_chars}")
                    continue
                raise

        if result.startswith("REJECT:"):
            project.status = Project.Status.FAILED
            project.error_message = result
            project.save()
            return {"error": result}

        # Validate output for common errors and retry if needed
        result = _validate_and_fix_output(result, project.github_url or '',
                                           project.name, tree_text, file_list)

        project.generated_docs = result

        project.status = Project.Status.DONE
        project.save()
        return {"project_id": str(project.id)}

    except Exception as e:
        logger.error(f"generate_universal_docs_task error: {e}")
        if project:
            project.status = Project.Status.FAILED
            project.error_message = str(e)
            project.save()
        return {"error": str(e)}


# ── GitHub Import (Universal, all file types) ────────────────

def _download_github_zipball(url: str, headers: dict, folder_path: str) -> list:
    """Download a GitHub zipball and extract ALL files (no .py filter)."""
    resp = requests.get(url, headers=headers, timeout=30, stream=True)
    resp.raise_for_status()
    zip_bytes = resp.content

    files = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        prefix = ''
        if names:
            first = names[0]
            if '/' in first:
                prefix = first.split('/', 1)[0] + '/'
        for name in names:
            if name.endswith('/'):
                continue
            rel_path = name[len(prefix):] if prefix else name
            if folder_path and folder_path != '/':
                if not rel_path.startswith(folder_path.lstrip('/')):
                    continue
            try:
                content = zf.read(name).decode('utf-8', errors='ignore').replace('\x00', '')
                files.append({'file_path': rel_path, 'content': content})
            except Exception:
                files.append({'file_path': rel_path, 'content': '[binary file]'})
    return files


def _fetch_public_repo_api(full_name: str) -> dict:
    api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
    headers = {'Accept': 'application/vnd.github+json'}
    if api_token and api_token.strip():
        headers['Authorization'] = f'token {api_token}'
    resp = requests.get(
        f'https://api.github.com/repos/{full_name}',
        headers=headers, timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def import_universal_github_task(self, project_id, mode, full_name, folder_path, branch, github_token=None):
    """Download ALL files from a GitHub repo (any language), create ProjectFiles, then delegate to generate_universal_docs_task."""
    project = None
    try:
        project = Project.objects.get(id=project_id)
        project.status = Project.Status.PROCESSING
        project.save(update_fields=['status'])

        if github_token:
            url = f'https://api.github.com/repos/{full_name}/zipball/{branch}'
            headers = {
                'Accept': 'application/vnd.github+json',
                'Authorization': f'token {github_token}',
            }
        else:
            repo_data = _fetch_public_repo_api(full_name)
            branch = branch or repo_data.get('default_branch') or 'main'
            api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
            headers = {'Accept': 'application/vnd.github+json'}
            if api_token and api_token.strip():
                headers['Authorization'] = f'token {api_token}'
                url = f'https://api.github.com/repos/{full_name}/zipball/{branch}'
            else:
                url = f'https://github.com/{full_name}/archive/refs/heads/{branch}.zip'

        raw_files = _download_github_zipball(url, headers, folder_path)

        if not raw_files:
            project.status = Project.Status.FAILED
            project.error_message = "No files found in the specified repository path."
            project.save(update_fields=['status', 'error_message'])
            return {"error": "No files found"}

        for f in raw_files:
            ProjectFile.objects.create(
                project=project,
                file_name=os.path.basename(f['file_path']),
                file_path=f['file_path'],
                content=f['content'],
            )

        # Delegate AI generation to the existing task
        generate_universal_docs_task.delay(str(project.id), mode)
        return {"project_id": str(project.id)}

    except Exception as e:
        logger.error(f"import_universal_github_task error: {e}")
        if project:
            project.status = Project.Status.FAILED
            project.error_message = str(e)
            project.save(update_fields=['status', 'error_message'])
        return {"error": str(e)}
