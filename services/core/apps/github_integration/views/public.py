from github import GithubException
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project

from .user import parse_github_url
from ..fetcher import get_public_repo, get_public_repo_folders
from ..tasks import import_public_repo_task


class PublicRepoInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
