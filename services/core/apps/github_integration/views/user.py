import re

from github import GithubException
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project

from ..fetcher import get_repo_folders, get_user_repos
from ..serializers import RepoImportSerializer
from ..tasks import import_github_repo_task


def parse_github_url(url: str) -> str | None:
    patterns = [
        r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?(?:/|$)',
        r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            full_name = match.group(1)
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
