from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from apps.projects.serializers import ProjectListSerializer, ProjectSerializer
from apps.users.models import User
from apps.users.serializers import UserSerializer


class AdminStatsView(APIView):
    """Admin-only endpoint returning platform statistics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff and not request.user.is_admin:
            from rest_framework import status
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        now   = timezone.now()
        week  = now - timedelta(days=7)
        month = now - timedelta(days=30)

        stats = {
            'users': {
                'total':           User.objects.count(),
                'verified':        User.objects.filter(is_verified=True).count(),
                'github_connected':User.objects.exclude(github_token__isnull=True).exclude(github_token='').count(),
                'new_this_week':   User.objects.filter(created_at__gte=week).count(),
                'new_this_month':  User.objects.filter(created_at__gte=month).count(),
            },
            'projects': {
                'total':           Project.objects.count(),
                'done':            Project.objects.filter(status='done').count(),
                'processing':      Project.objects.filter(status='processing').count(),
                'failed':          Project.objects.filter(status='failed').count(),
                'pending':         Project.objects.filter(status='pending').count(),
                'new_this_week':   Project.objects.filter(created_at__gte=week).count(),
                'new_this_month':  Project.objects.filter(created_at__gte=month).count(),
                'by_source': list(
                    Project.objects.values('source_type')
                    .annotate(count=Count('id'))
                    .order_by('-count')
                ),
            },
            'top_users': list(
                User.objects.annotate(project_count=Count('projects'))
                .order_by('-project_count')
                .values('email', 'name', 'project_count')[:10]
            ),
        }
        return Response(stats)


class AdminUserListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('-created_at')
    filterset_fields = ['is_active', 'is_verified', 'role']
    search_fields = ['email', 'username', 'name']
    ordering_fields = ['created_at', 'email', 'username']

class AdminUserDetailView(RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'pk'

class AdminProjectListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProjectListSerializer
    filterset_fields = ['status', 'source_type']
    search_fields = ['name', 'user__email', 'user__name']
    ordering_fields = ['created_at', 'name', 'status']

    def get_queryset(self):
        return Project.objects.select_related('user') \
            .annotate(file_count=Count('files')) \
            .order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        stats = {
            'total':      queryset.count(),
            'done':       queryset.filter(status='done').count(),
            'processing': queryset.filter(status='processing').count(),
            'failed':     queryset.filter(status='failed').count(),
            'pending':    queryset.filter(status='pending').count(),
            'by_source':  list(
                queryset.values('source_type')
                .annotate(count=Count('id'))
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

class AdminProjectDetailView(RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProjectSerializer
    queryset = Project.objects.select_related('user').all()
    lookup_field = 'pk'
