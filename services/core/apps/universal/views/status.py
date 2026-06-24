from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project


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
