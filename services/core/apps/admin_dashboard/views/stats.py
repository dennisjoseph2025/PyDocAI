from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.tasks import send_email_task
from apps.projects.models import Project
from apps.users.models import User


class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff and not request.user.is_admin:
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        now   = timezone.now()
        week  = now - timedelta(days=7)
        month = now - timedelta(days=30)

        stats = {
            'users': {
                'total':           User.objects.count(),
                'verified':        User.objects.filter(is_verified=True).count(),
                'github_connected': User.objects.exclude(github_token__isnull=True).exclude(github_token='').count(),
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
                User.objects.annotate(
                    project_count=Count('projects'),
                    published_count=Count('projects', filter=Q(projects__is_published=True)),
                )
                .order_by('-project_count')
                .values('id', 'email', 'name', 'project_count', 'published_count')[:10]
            ),
        }
        return Response(stats)
