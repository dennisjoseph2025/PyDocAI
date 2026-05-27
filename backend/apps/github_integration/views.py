from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import re
from github import GithubException

from .fetcher import get_user_repos, get_repo_folders, get_public_repo, get_public_repo_folders
from .serializers import RepoImportSerializer
from .tasks import import_github_repo_task, import_public_repo_task
from apps.projects.models import Project


def parse_github_url(url: str) -> str | None:
    """Extract owner/repo from a GitHub URL. Returns None if invalid."""
    patterns = [
        r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?(?:/|$)',
        r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            full_name = match.group(1)
            # Strip trailing slashes or dots
            full_name = full_name.rstrip('/.')
            if '/' in full_name and not full_name.endswith('.'):
                return full_name
    return None


class UserReposView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.github_token:
            return Response({'detail': 'GitHub account not connected.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            repos = get_user_repos(user.github_token)
            return Response(repos)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RepoFoldersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        full_name = request.query_params.get('repo')
        branch    = request.query_params.get('branch', None)
        if not full_name:
            return Response({'detail': 'repo parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        if not user.github_token:
            return Response({'detail': 'GitHub account not connected.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            folders = get_repo_folders(user.github_token, full_name, branch)
            return Response(folders)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ImportRepoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RepoImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data        = serializer.validated_data
        full_name   = data['full_name']
        folder_path = data.get('folder_path', '/')
        branch      = data.get('branch') or None
        name        = data.get('name') or full_name.split('/')[-1]
        description = data.get('description', '')
        custom_info = data.get('custom_info', {})

        user = request.user
        if not user.github_token:
            return Response({'detail': 'GitHub account not connected.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create project immediately and return — all slow GitHub work happens in Celery
        project = Project.objects.create(
            user=user,
            name=name,
            description=description,
            source_type=Project.SourceType.GITHUB,
            github_url=f'https://github.com/{full_name}',
            status=Project.Status.PENDING,
            custom_details=custom_info or None,
        )

        import_github_repo_task.delay(
            project.id,
            user.github_token,
            full_name,
            folder_path,
            branch,
            description,
            custom_info or None,
        )

        return Response({'project_id': str(project.id)}, status=status.HTTP_202_ACCEPTED)


class PublicRepoInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get info about a public repo from URL or full_name."""
        url = request.query_params.get('url')
        full_name = request.query_params.get('full_name')

        if url:
            full_name = parse_github_url(url)
            if not full_name:
                return Response({'detail': 'Invalid GitHub URL. Expected: https://github.com/owner/repo'}, status=status.HTTP_400_BAD_REQUEST)
        elif not full_name:
            return Response({'detail': 'url or full_name parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            repo = get_public_repo(full_name)
            return Response(repo)
        except GithubException as e:
            if e.status == 404:
                return Response({'detail': 'Repository not found. It may be private or does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            if e.status == 403:
                return Response({'detail': 'Rate limit exceeded or repository is private.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({'detail': f'GitHub API error: {e.data.get("message", str(e))}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PublicRepoFoldersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get folders from a public repo."""
        full_name = request.query_params.get('full_name')
        url = request.query_params.get('url')
        branch = request.query_params.get('branch', None)

        if url:
            full_name = parse_github_url(url)
            if not full_name:
                return Response({'detail': 'Invalid GitHub URL'}, status=status.HTTP_400_BAD_REQUEST)
        elif not full_name:
            return Response({'detail': 'full_name or url parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            folders = get_public_repo_folders(full_name, branch)
            return Response(folders)
        except GithubException as e:
            if e.status == 404:
                return Response({'detail': 'Repository not found'}, status=status.HTTP_404_NOT_FOUND)
            if e.status == 403:
                return Response({'detail': 'Rate limit exceeded or repository is private.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({'detail': f'GitHub API error: {e.data.get("message", str(e))}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImportPublicRepoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Import a public GitHub repo using URL or full_name (no OAuth required)."""
        url = request.data.get('url')
        full_name = request.data.get('full_name')
        folder_path = request.data.get('folder_path', '/')
        branch = request.data.get('branch') or None
        name = request.data.get('name')
        description = request.data.get('description', '')
        custom_info = request.data.get('custom_info', {})

        if url:
            full_name = parse_github_url(url)
            if not full_name:
                return Response({'detail': 'Invalid GitHub URL. Expected: https://github.com/owner/repo'}, status=status.HTTP_400_BAD_REQUEST)
        elif not full_name:
            return Response({'detail': 'url or full_name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not name:
            name = full_name.split('/')[-1]

        project = Project.objects.create(
            user=request.user,
            name=name,
            description=description,
            source_type=Project.SourceType.GITHUB,
            github_url=f'https://github.com/{full_name}',
            status=Project.Status.PENDING,
            custom_details=custom_info or None,
        )

        import_public_repo_task.delay(
            project.id,
            full_name,
            folder_path,
            branch,
            description,
            custom_info or None,
        )

        return Response({'project_id': str(project.id)}, status=status.HTTP_202_ACCEPTED)