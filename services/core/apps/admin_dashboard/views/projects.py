from django.db.models import Count, Q
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from apps.projects.serializers import ProjectListSerializer, ProjectSerializer


class AdminProjectListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Project.objects.select_related('user') \
            .annotate(file_count=Count('files'))

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__name__icontains=search)
            )

        for field in ['status', 'source_type']:
            val = request.query_params.get(field)
            if val:
                qs = qs.filter(**{field: val})

        ordering = request.query_params.get('ordering', '-created_at')
        allowed = ['created_at', 'name', 'status', '-created_at', '-name', '-status']
        if ordering not in allowed:
            ordering = '-created_at'
        qs = qs.order_by(ordering)

        stats = {
            'total':      qs.count(),
            'done':       qs.filter(status='done').count(),
            'processing': qs.filter(status='processing').count(),
            'failed':     qs.filter(status='failed').count(),
            'pending':    qs.filter(status='pending').count(),
            'by_source':  list(
                qs.values('source_type')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
        }

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


class AdminUserProjectsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        qs = (Project.objects
              .filter(user_id=pk, is_published=True)
              .select_related('user')
              .annotate(file_count=Count('files'))
              .order_by('-updated_at'))
        serializer = ProjectListSerializer(qs, many=True)
        return Response(serializer.data)


class AdminProjectDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            project = Project.objects.select_related('user').get(pk=pk)
        except Project.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)
