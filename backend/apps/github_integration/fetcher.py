from github import Github


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
            'type': item.type,   # 'blob' = file, 'tree' = folder
            'size': item.size,
        })
    return items


def get_repo_folders(github_token: str, full_name: str, branch: str = None) -> list:
    """Get only folders from a repo (for folder picker UI)."""
    tree = get_repo_tree(github_token, full_name, branch)
    folders = [
        item for item in tree
        if item['type'] == 'tree'
    ]
    # always include root
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