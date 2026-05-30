import base64
import io
import json
import zipfile

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.parser.tasks import parse_and_generate_docs_task, parse_folder_task
from apps.parser.validators import should_exclude
from apps.projects.models import Project


class AnalyseFolderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        zip_file = request.FILES.get('folder')
        name = request.data.get('name', 'Untitled Project')
        description = request.data.get('description', '')

        # Optional user-provided project details for documentation
        user_description = request.data.get('user_description', None)
        # Parse custom_info (Mandatory)
        custom_info = request.data.get('custom_info', None)
        if not custom_info:
            return Response({'error': 'additional project details (custom_info) are mandatory for folder uploads'}, status=400)

        if isinstance(custom_info, str):
            try:
                # Try parsing as JSON first
                custom_info = json.loads(custom_info)
            except json.JSONDecodeError:
                # If it's just plain text, wrap it in a JSON object
                custom_info = {"details": custom_info}

        if not zip_file:
            return Response({'error': 'No zip file provided'}, status=400)

        if not zip_file.name.endswith('.zip'):
            return Response({'error': 'File must be a .zip'}, status=400)

        try:
            zip_content = zip_file.read()
            zf = zipfile.ZipFile(io.BytesIO(zip_content))

            py_files = [
                f for f in zf.namelist()
                if f.endswith('.py') and not should_exclude(f)
            ]

            if not py_files:
                return Response({'error': 'No Python files found after filtering'}, status=400)

            project = Project.objects.create(
                user=request.user,
                name=name,
                description=description,
                source_type=Project.SourceType.FOLDER,
                status=Project.Status.PENDING,
                custom_details=custom_info
            )

            zip_base64 = base64.b64encode(zip_content).decode('utf-8')

            parse_folder_task.delay(
                project.id,
                py_files,
                zip_base64,
                user_description=user_description,
                custom_info=custom_info
            )

            return Response(
                {'project_id': str(project.id)},
                status=status.HTTP_202_ACCEPTED
            )

        except zipfile.BadZipFile:
            return Response({'error': 'Invalid zip file'}, status=400)


class AnalyseSingleFileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        name = request.data.get('name', 'Untitled Project')
        description = request.data.get('description', '')

        if not uploaded_file:
            return Response({'error': 'No file uploaded'}, status=400)

        if not uploaded_file.name.endswith('.py'):
            return Response({'error': 'Only .py files are allowed'}, status=400)

        try:
            source_code = uploaded_file.read().decode('utf-8')
            fname = uploaded_file.name
            fsize = uploaded_file.size
        except UnicodeDecodeError:
            return Response({'error': 'File must be UTF-8 encoded'}, status=400)

        project = Project.objects.create(
            user=request.user,
            name=name,
            description=description,
            source_type=Project.SourceType.FILE,
            file_name=fname,
            file_size=fsize,
            status=Project.Status.PENDING,
        )

        parse_and_generate_docs_task.delay(project.id, source_code, fname, fsize)

        return Response(
            {'project_id': str(project.id)},
            status=status.HTTP_202_ACCEPTED
        )
