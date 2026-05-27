from github import Github, GithubException, RateLimitExceededException
from django.conf import settings
import requests


def _get_github_client(github_token=None):
    """Create a Github client using user token, app API token, or unauthenticated."""
    if github_token:
        return Github(github_token, timeout=10, retry=0)
    api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
    if api_token and api_token.strip():
        return Github(api_token, timeout=10, retry=0)
    return Github(timeout=10, retry=0)


def _fetch_public_repo_api(full_name: str) -> dict:
    """Fetch public repo info directly via GitHub REST API (avoids PyGithub retry loops)."""
    api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
    headers = {'Accept': 'application/vnd.github+json'}
    if api_token and api_token.strip():
        headers['Authorization'] = f'token {api_token}'
    
    resp = requests.get(
        f'https://api.github.com/repos/{full_name}',
        headers=headers,
        timeout=10,
    )
    if resp.status_code == 404:
        raise GithubException(404, {'message': 'Not Found'})
    if resp.status_code == 403:
        raise GithubException(403, {'message': 'Rate limit exceeded or forbidden'})
    resp.raise_for_status()
    return resp.json()


def _fetch_public_tree_api(full_name: str, branch: str) -> dict:
    """Fetch repo tree directly via GitHub REST API."""
    api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
    headers = {'Accept': 'application/vnd.github+json'}
    if api_token and api_token.strip():
        headers['Authorization'] = f'token {api_token}'
    
    resp = requests.get(
        f'https://api.github.com/repos/{full_name}/git/trees/{branch}?recursive=1',
        headers=headers,
        timeout=10,
    )
    if resp.status_code == 404:
        raise GithubException(404, {'message': 'Not Found'})
    if resp.status_code == 403:
        raise GithubException(403, {'message': 'Rate limit exceeded or forbidden'})
    resp.raise_for_status()
    return resp.json()


def get_user_repos(github_token: str) -> list:
    """List all repos the user has access to."""
    g = Github(github_token)
    user = g.get_user()
    repos = []
    for repo in user.get_repos(sort='updated'):
        repos.append({
            'id':          repo.id,
            'name':        repo.name,
            'full_name':   repo.full_name,
            'description': repo.description,
            'private':     repo.private,
            'url':         repo.html_url,
            'updated_at':  repo.updated_at.isoformat(),
            'language':    repo.language,
            'default_branch': repo.default_branch,
        })
    return repos


def get_public_repo(full_name: str, github_token=None) -> dict:
    """Get info about a public repository without user OAuth token."""
    data = _fetch_public_repo_api(full_name)
    return {
        'id':              data['id'],
        'name':            data['name'],
        'full_name':       data['full_name'],
        'description':     data.get('description') or '',
        'private':         data['private'],
        'url':             data['html_url'],
        'default_branch':  data.get('default_branch') or 'main',
        'language':        data.get('language') or '',
        'stargazers_count': data.get('stargazers_count', 0),
        'forks_count':     data.get('forks_count', 0),
    }


def get_repo_tree(github_token: str, full_name: str, branch: str = None) -> list:
    """Get the folder/file tree of a repo."""
    g = Github(github_token)
    repo = g.get_repo(full_name)
    branch = branch or repo.default_branch

    tree = repo.get_git_tree(branch, recursive=True)
    items = []
    for item in tree.tree:
        items.append({
            'path': item.path,
            'type': item.type,  
            'size': item.size,
        })
    return items


def get_public_repo_tree(full_name: str, branch: str = None, github_token=None) -> list:
    """Get the folder/file tree of a public repo without user OAuth token."""
    # First get repo to find default branch if not provided
    repo_data = _fetch_public_repo_api(full_name)
    branch = branch or repo_data.get('default_branch') or 'main'
    
    tree_data = _fetch_public_tree_api(full_name, branch)
    items = []
    for item in tree_data.get('tree', []):
        items.append({
            'path': item['path'],
            'type': item['type'],  # 'blob' = file, 'tree' = folder
            'size': item.get('size', 0),
        })
    return items


def get_repo_folders(github_token: str, full_name: str, branch: str = None) -> list:
    """Get only folders from a repo (for folder picker UI)."""
    tree = get_repo_tree(github_token, full_name, branch)
    folders = [
        item for item in tree
        if item['type'] == 'tree'
    ]
    
    folders.insert(0, {'path': '/', 'type': 'tree', 'size': 0})
    return folders


def get_public_repo_folders(full_name: str, branch: str = None, github_token=None) -> list:
    """Get only folders from a public repo without user OAuth token."""
    tree = get_public_repo_tree(full_name, branch, github_token)
    folders = [
        item for item in tree
        if item['type'] == 'tree'
    ]
    folders.insert(0, {'path': '/', 'type': 'tree', 'size': 0})
    return folders


def import_folder_from_repo(github_token, full_name, folder_path, branch=None):
    from github import Github
    g = Github(github_token)
    repo = g.get_repo(full_name)
    branch = branch or repo.default_branch
    files = []

    def fetch_contents(path):
        try:
            contents = repo.get_contents(path, ref=branch)
            if not isinstance(contents, list):
                contents = [contents]
            for item in contents:
                if item.type == 'dir':
                    fetch_contents(item.path)
                elif item.type == 'file' and item.path.endswith('.py'):
                    try:
                        content = item.decoded_content.decode('utf-8', errors='ignore')
                        files.append({'file_path': item.path, 'content': content})
                    except Exception:
                        pass
        except Exception:
            pass

    start = folder_path.lstrip('/') if folder_path and folder_path != '/' else ''
    fetch_contents(start)
    return files


def _fetch_contents_api(full_name: str, path: str, branch: str) -> list:
    """Fetch directory contents via GitHub REST API."""
    api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
    headers = {'Accept': 'application/vnd.github+json'}
    if api_token and api_token.strip():
        headers['Authorization'] = f'token {api_token}'
    
    url = f'https://api.github.com/repos/{full_name}/contents/{path}'
    params = {'ref': branch} if branch else {}
    
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json()


def _fetch_file_content_api(full_name: str, path: str, branch: str) -> str | None:
    """Fetch a single file's content via GitHub REST API."""
    api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
    headers = {'Accept': 'application/vnd.github+json'}
    if api_token and api_token.strip():
        headers['Authorization'] = f'token {api_token}'
    
    url = f'https://api.github.com/repos/{full_name}/contents/{path}'
    params = {'ref': branch} if branch else {}
    
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    if resp.status_code != 200:
        return None
    
    import base64
    data = resp.json()
    return base64.b64decode(data['content']).decode('utf-8', errors='ignore')


def import_public_folder_from_repo(full_name, folder_path, branch=None, github_token=None):
    """Import .py files from a public repo without user OAuth token."""
    # Get repo to find default branch
    repo_data = _fetch_public_repo_api(full_name)
    branch = branch or repo_data.get('default_branch') or 'main'
    files = []

    def fetch_contents(path):
        try:
            contents = _fetch_contents_api(full_name, path, branch)
            for item in contents:
                if item['type'] == 'dir':
                    fetch_contents(item['path'])
                elif item['type'] == 'file' and item['name'].endswith('.py'):
                    content = _fetch_file_content_api(full_name, item['path'], branch)
                    if content:
                        files.append({'file_path': item['path'], 'content': content})
        except Exception as e:
            from django.conf import settings
            if getattr(settings, 'DEBUG', False):
                print(f"Error fetching {path}: {e}")

    start = folder_path.lstrip('/') if folder_path and folder_path != '/' else ''
    fetch_contents(start)
    return files