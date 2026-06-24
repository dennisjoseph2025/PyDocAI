from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Project
from ..serializers import ProjectListSerializer, ProjectSerializer
from ..throttles import PublishRateThrottle

User = get_user_model()


class ProjectListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = (Project.objects
              .filter(user=request.user)
              .select_related('user')
              .annotate(file_count=Count('files'))
              .order_by('-created_at'))

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(status__icontains=search) |
                Q(source_type__icontains=search)
            )

        for field in ['status', 'source_type', 'is_published']:
            val = request.query_params.get(field)
            if val is not None:
                qs = qs.filter(**{field: val})

        ordering = request.query_params.get('ordering', '-created_at')
        allowed = ['created_at', 'name', 'status', 'source_type',
                   '-created_at', '-name', '-status', '-source_type']
        if ordering not in allowed:
            ordering = '-created_at'
        qs = qs.order_by(ordering)

        cache_key = f'project_stats_{request.user.id}'
        stats = cache.get(cache_key)
        if not stats:
            base = Project.objects.filter(user=request.user).order_by()
            counts = base.values('status').annotate(count=Count('id'))
            status_map = {c['status']: c['count'] for c in counts}
            stats = {
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
            cache.set(cache_key, stats, 60)

        page_size = int(request.query_params.get('page_size', 25))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        page_qs = qs[start:end]
        serializer = ProjectListSerializer(page_qs, many=True)

        return Response({
            'stats': stats,
            'results': serializer.data,
            'count': total,
            'page': page,
            'page_size': page_size,
        })


class ProjectDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        if user.is_staff or getattr(user, 'is_admin', False):
            qs = Project.objects.all()
        else:
            qs = Project.objects.filter(user=user)
        try:
            return qs.get(pk=pk)
        except Project.DoesNotExist:
            return None

    def get(self, request, id):
        project = self.get_object(id, request.user)
        if not project:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def delete(self, request, id):
        project = self.get_object(id, request.user)
        if not project:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
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
