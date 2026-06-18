import logging
import os
import zipfile

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project, ProjectFile
from apps.universal.tasks import generate_universal_docs_task, import_universal_github_task

logger = logging.getLogger(__name__)


class UniversalUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mode = request.data.get('mode', 'universal')
        name = request.data.get('name', '').strip()
        description = request.data.get('description', '').strip()
        github_url = request.data.get('github_url', '').strip()

        if not name:
            return Response({'detail': 'Project name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        valid_modes = ['universal']
        if mode not in valid_modes:
            return Response(
                {'detail': f'Invalid mode. Choose from: {", ".join(valid_modes)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = Project.objects.create(
            user=request.user,
            name=name,
            description=description,
            source_type='file',
            status=Project.Status.PENDING,
        )

        if github_url:
            project.source_type = 'github'
            project.save(update_fields=['source_type'])
            return self._handle_github(project, mode, github_url, request)

        uploaded_file = request.FILES.get('file')
        if uploaded_file and uploaded_file.name.endswith('.zip'):
            project.source_type = 'folder'
            project.save(update_fields=['source_type'])
            self._process_zip(project, uploaded_file)
        elif uploaded_file:
            self._process_single_file(project, uploaded_file)
        else:
            source_code = request.data.get('source_code', '')
            if source_code:
                ProjectFile.objects.create(
                    project=project,
                    file_name='source.txt',
                    file_path='source.txt',
                    content=source_code,
                )
            else:
                project.status = Project.Status.FAILED
                project.error_message = "No file, GitHub URL, or source code provided."
                project.save()
                return Response(
                    {'detail': 'No file, GitHub URL, or source code provided.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        project.save()
        generate_universal_docs_task.delay(str(project.id), mode)
        return Response({'project_id': project.id}, status=status.HTTP_202_ACCEPTED)

    def _handle_github(self, project, mode, github_url, request):
        from apps.github_integration.views import parse_github_url

        full_name = parse_github_url(github_url)
        if not full_name:
            project.delete()
            return Response({'detail': 'Invalid GitHub URL.'}, status=status.HTTP_400_BAD_REQUEST)

        folder_path = request.data.get('folder_path', '/')
        branch = request.data.get('branch', 'main') or 'main'
        project.github_url = f'https://github.com/{full_name}'

        # Check if user has connected GitHub (authenticated import)
        github_token = request.user.github_token if hasattr(request.user, 'github_token') else None
        project.save(update_fields=['github_url'])

        import_universal_github_task.delay(
            str(project.id), mode, full_name, folder_path, branch, github_token,
        )
        return Response({'project_id': project.id}, status=status.HTTP_202_ACCEPTED)

    def _process_zip(self, project, zip_file):
        try:
            with zipfile.ZipFile(zip_file) as zf:
                for file_path in zf.namelist():
                    if file_path.startswith('__MACOSX/') or file_path.startswith('.') or file_path.endswith('/'):
                        continue
                    try:
                        content = zf.read(file_path).decode('utf-8', errors='ignore').replace('\x00', '')
                        ProjectFile.objects.create(
                            project=project,
                            file_name=os.path.basename(file_path),
                            file_path=file_path,
                            content=content,
                        )
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing zip: {e}")
            raise

    def _process_single_file(self, project, uploaded_file):
        content = uploaded_file.read().decode('utf-8', errors='ignore').replace('\x00', '')
        ProjectFile.objects.create(
            project=project,
            file_name=uploaded_file.name,
            file_path=uploaded_file.name,
            content=content,
        )


class UniversalStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, user=request.user)
            data = {
                'id': project.id,
                'name': project.name,
                'description': project.description or '',
                'status': project.status,
                'mode': 'universal',
                'error': project.error_message or '',
                'docs': project.generated_docs or '',
                'created_at': project.created_at,
            }
            return Response(data)
        except Project.DoesNotExist:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
