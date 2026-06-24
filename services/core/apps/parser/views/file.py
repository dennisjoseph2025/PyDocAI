from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.parser.tasks import parse_and_generate_docs_task
from apps.projects.models import Project


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
