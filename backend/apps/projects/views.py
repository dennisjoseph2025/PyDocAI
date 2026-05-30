from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count
from .models import Project
from .serializers import ProjectSerializer, ProjectListSerializer

User = get_user_model()

class ProjectListView(generics.ListAPIView):
    """
    List all projects for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectListSerializer
    search_fields = ['name', 'description', 'status', 'source_type']
    filterset_fields = ['status', 'source_type']
    ordering_fields = ['created_at', 'name', 'status', 'source_type']

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).annotate(file_count=Count('files'))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        stats = {
            'total':         queryset.count(),
            'done':          queryset.filter(status='done').count(),
            'processing':    queryset.filter(status='processing').count(),
            'failed':        queryset.filter(status='failed').count(),
            'pending':       queryset.filter(status='pending').count(),
            'total_files':   queryset.aggregate(total=Count('files', distinct=True))['total'] or 0,
            'by_source': list(
                queryset.values('source_type')
                .annotate(count=Count('id', distinct=True))
                .order_by('-count')
            ),
        }

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['stats'] = stats
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({'stats': stats, 'results': serializer.data})

class ProjectDetailView(generics.RetrieveDestroyAPIView):
    """
    Get details of a specific project or delete it.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'is_admin', False):
            return Project.objects.all()
        return Project.objects.filter(user=user)

    def delete(self, request, *args, **kwargs):
        project = self.get_object()
        project.delete()
        return Response({"detail": "Project has been deleted successfully"}, status=status.HTTP_200_OK)
