from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Count
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Project
from .serializers import ProjectListSerializer, ProjectSerializer, PublicProjectListSerializer, PublicProjectSerializer
from .throttles import PublicRateThrottle, PublishRateThrottle

User = get_user_model()

class ProjectListView(generics.ListAPIView):
    """
    List all projects for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectListSerializer
    search_fields = ['name', 'description', 'status', 'source_type']
    filterset_fields = ['status', 'source_type', 'is_published']
    ordering_fields = ['created_at', 'name', 'status', 'source_type']

    def get_queryset(self):
        return (Project.objects
                .filter(user=self.request.user)
                .select_related('user')
                .annotate(file_count=Count('files'))
                .order_by('-created_at'))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        cache_key = f'project_stats_{request.user.id}'
        stats = cache.get(cache_key)
        if not stats:
            stats = self._compute_stats(queryset)
            cache.set(cache_key, stats, 60)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['stats'] = stats
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({'stats': stats, 'results': serializer.data})

    def _compute_stats(self, queryset):
        base = (Project.objects
                .filter(user=self.request.user)
                .order_by())
        counts = base.values('status').annotate(count=Count('id'))
        status_map = {c['status']: c['count'] for c in counts}
        return {
            'total':       sum(status_map.values()),
            'done':        status_map.get('done', 0),
            'processing':  status_map.get('processing', 0),
            'failed':      status_map.get('failed', 0),
            'pending':     status_map.get('pending', 0),
            'published':   base.filter(is_published=True).count(),
            'total_files': base.aggregate(total=Count('files', distinct=True))['total'] or 0,
            'by_source': list(
                base.values('source_type')
                .annotate(count=Count('id', distinct=True))
                .order_by('-count')
            ),
        }

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
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM feedback WHERE project_id = %s", [str(project.id)])
        project.files.all().delete()
        project.delete()
        return Response({"detail": "Project has been deleted successfully"}, status=status.HTTP_200_OK)


class PublishProjectView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [PublishRateThrottle]

    def patch(self, request, pk):
        try:
            project = Project.objects.get(pk=pk, user=request.user)
        except Project.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        is_published = request.data.get("is_published")
        if is_published is None:
            return Response({"detail": "is_published is required."}, status=status.HTTP_400_BAD_REQUEST)

        project.is_published = is_published
        if is_published and request.data.get("published_description"):
            project.published_description = request.data["published_description"]
        project.save(update_fields=["is_published", "published_description", "updated_at"])
        cache.delete(f'project_stats_{request.user.id}')
        return Response(ProjectSerializer(project).data)


class NoPagination(PageNumberPagination):
    page_size = None


class PublicProjectPage(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class PublicProjectListView(generics.ListAPIView):
    permission_classes = []
    serializer_class = PublicProjectListSerializer
    throttle_classes = [PublicRateThrottle]
    pagination_class = PublicProjectPage

    def get_queryset(self):
        return (Project.objects
                .filter(is_published=True, status='done')
                .select_related('user')
                .annotate(file_count=Count('files'))
                .order_by('-updated_at'))


class PublicProjectDetailView(APIView):
    permission_classes = []
    throttle_classes = [PublicRateThrottle]

    def get(self, request, slug):
        cache_key = f'public_project_{slug}'
        data = cache.get(cache_key)
        if not data:
            try:
                project = (Project.objects
                           .filter(public_slug=slug, is_published=True)
                           .select_related('user')
                           .prefetch_related('files')
                           .get())
            except Project.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            data = PublicProjectSerializer(project).data
            cache.set(cache_key, data, 300)
        return Response(data)
