import io
import zipfile

import requests
from django.conf import settings
from github import Github, GithubException


def get_github_client(github_token=None):
    if github_token:
        return Github(github_token, timeout=10, retry=0)
    api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
    if api_token and api_token.strip():
        return Github(api_token, timeout=10, retry=0)
    return Github(timeout=10, retry=0)


def _github_api_headers():
    api_token = getattr(settings, 'GITHUB_API_TOKEN', None)
    headers = {'Accept': 'application/vnd.github+json'}
    if api_token and api_token.strip():
        headers['Authorization'] = f'token {api_token}'
    return headers


def fetch_public_repo_api(full_name):
    headers = _github_api_headers()
    resp = requests.get(
        f'https://api.github.com/repos/{full_name}',
        headers=headers, timeout=10,
    )
    if resp.status_code == 404:
        raise GithubException(404, {'message': 'Not Found'})
    if resp.status_code == 403:
        raise GithubException(403, {'message': 'Rate limit exceeded or forbidden'})
    resp.raise_for_status()
    return resp.json()


def fetch_public_tree_api(full_name, branch):
    headers = _github_api_headers()
    resp = requests.get(
        f'https://api.github.com/repos/{full_name}/git/trees/{branch}?recursive=1',
        headers=headers, timeout=10,
    )
    if resp.status_code == 404:
        raise GithubException(404, {'message': 'Not Found'})
    if resp.status_code == 403:
        raise GithubException(403, {'message': 'Rate limit exceeded or forbidden'})
    resp.raise_for_status()
    return resp.json()


def download_zipball(url, headers, folder_path, file_filter=None):
    """Download a GitHub zipball and extract files.

    file_filter: optional callable(file_name) -> bool to filter files.
    By default (None), extracts ALL files except directories.
    """
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
            if file_filter and not file_filter(name):
                continue
            rel_path = name[len(prefix):] if prefix else name
            if folder_path and folder_path != '/' and not rel_path.startswith(folder_path.lstrip('/')):
                continue
            try:
                content = zf.read(name).decode('utf-8', errors='ignore').replace('\x00', '')
                files.append({'file_path': rel_path, 'content': content})
            except Exception:
                files.append({'file_path': rel_path, 'content': '[binary file]'})
    return files


def get_repo_tree_items(github_token, full_name, branch=None):
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


def get_public_repo_tree_items(full_name, branch=None):
    repo_data = fetch_public_repo_api(full_name)
    branch = branch or repo_data.get('default_branch') or 'main'
    tree_data = fetch_public_tree_api(full_name, branch)
    items = []
    for item in tree_data.get('tree', []):
        items.append({
            'path': item['path'],
            'type': item['type'],
            'size': item.get('size', 0),
        })
    return items
