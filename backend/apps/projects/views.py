from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer, ProjectListSerializer

class ProjectListView(generics.ListAPIView):
    """
    List all projects for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectListSerializer

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

class ProjectDetailView(generics.RetrieveDestroyAPIView):
    """
    Get details of a specific project or delete it.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        project = self.get_object()
        project.delete()
        return Response({"detail": "Project deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
