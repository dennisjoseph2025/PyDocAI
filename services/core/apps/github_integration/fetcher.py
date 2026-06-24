from django.conf import settings

from apps.common.github import (
    download_zipball,
    fetch_public_repo_api,
    get_github_client,
    get_public_repo_tree_items,
    get_repo_tree_items,
)


def get_user_repos(github_token: str) -> list:
    g = get_github_client(github_token)
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
    data = fetch_public_repo_api(full_name)
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
    return get_repo_tree_items(github_token, full_name, branch)


def get_public_repo_tree(full_name: str, branch: str = None, github_token=None) -> list:
    return get_public_repo_tree_items(full_name, branch)


def _py_file_filter(name):
    return name.endswith('.py')


def get_repo_folders(github_token: str, full_name: str, branch: str = None) -> list:
    tree = get_repo_tree(github_token, full_name, branch)
    folders = [item for item in tree if item['type'] == 'tree']
    folders.insert(0, {'path': '/', 'type': 'tree', 'size': 0})
    return folders


def get_public_repo_folders(full_name: str, branch: str = None, github_token=None) -> list:
    tree = get_public_repo_tree(full_name, branch, github_token)
    folders = [item for item in tree if item['type'] == 'tree']
    folders.insert(0, {'path': '/', 'type': 'tree', 'size': 0})
    return folders


def import_folder_from_repo(github_token, full_name, folder_path, branch=None):
    g = get_github_client(github_token)
    repo = g.get_repo(full_name)
    branch = branch or repo.default_branch

    url = f'https://api.github.com/repos/{full_name}/zipball/{branch}'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'token {github_token}',
    }
    return download_zipball(url, headers, folder_path, file_filter=_py_file_filter)


def import_public_folder_from_repo(full_name, folder_path, branch=None, github_token=None):
    repo_data = fetch_public_repo_api(full_name)
    branch = branch or repo_data.get('default_branch') or 'main'

    api_token = github_token or getattr(settings, 'GITHUB_API_TOKEN', None)
    headers = {'Accept': 'application/vnd.github+json'}
    if api_token and api_token.strip():
        headers['Authorization'] = f'token {api_token}'
        url = f'https://api.github.com/repos/{full_name}/zipball/{branch}'
    else:
        url = f'https://github.com/{full_name}/archive/refs/heads/{branch}.zip'

    return download_zipball(url, headers, folder_path, file_filter=_py_file_filter)
