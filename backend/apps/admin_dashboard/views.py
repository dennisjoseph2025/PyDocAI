from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.tasks import send_email_task
from apps.projects.models import Project
from apps.projects.serializers import ProjectListSerializer, ProjectSerializer
from apps.users.models import User
from apps.users.serializers import AdminUserSerializer, UserSerializer


class AdminStatsView(APIView):
    """Admin-only endpoint returning platform statistics."""
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
                User.objects.annotate(
                    project_count=Count('projects'),
                    published_count=Count('projects', filter=Q(projects__is_published=True)),
                )
                .order_by('-project_count')
                .values('id', 'email', 'name', 'project_count', 'published_count')[:10]
            ),
        }
        return Response(stats)


class AdminUserListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer
    filterset_fields = ['is_active', 'is_verified', 'role']
    search_fields = ['email', 'username', 'name']
    ordering_fields = ['created_at', 'email', 'username']

    def get_queryset(self):
        return User.objects.annotate(
            project_count=Count('projects'),
            published_count=Count('projects', filter=Q(projects__is_published=True)),
        ).order_by('-created_at')

class AdminUserDetailView(RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'pk'


class AdminUserDeleteView(APIView):
    """Delete a user (admin only). Sends a notification email with reason."""
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            target = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', 'No reason provided.')

        # Send deletion email
        if settings.EMAIL_HOST_USER:
            subject = 'Your PyDocAI account has been deleted'
            send_email_task.delay(
                subject=subject,
                message=f'Your PyDocAI account has been deleted.\n\nReason: {reason}',
                recipient_list=[target.email],
                html_message=f'''<!DOCTYPE html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#080e17;margin:0;padding:0">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:40px 20px">
<table width="560" cellpadding="0" cellspacing="0" style="background:#0b1320;border-radius:16px;overflow:hidden;border:1px solid #1e293b">
<tr><td style="padding:0;border-bottom:1px solid #1e293b">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td style="padding:20px 32px">
<span style="font-size:18px;font-weight:700;color:#e2e8f0">Py<span style="color:#3b82f6">Doc</span><span style="color:#6366f1">AI</span></span>
</td>
<td style="padding:20px 32px;text-align:right">
<span style="font-size:11px;color:#64748b;font-family:monospace">ACCOUNT_DELETED</span>
</td>
</tr></table>
</td></tr>
<tr><td style="padding:32px 32px 0">
<h2 style="margin:0 0 4px;font-size:20px;color:#e2e8f0;font-weight:600">Account Deleted</h2>
<p style="margin:0 0 24px;font-size:13px;color:#64748b">
Your PyDocAI account has been deleted by an administrator.
</p>
</td></tr>
<tr><td style="padding:0 32px">
<div style="background:#1a0a0a;border:1px solid #7f1d1d;border-radius:10px;padding:16px;font-size:14px;color:#fca5a5;line-height:1.6;margin-bottom:24px;font-family:monospace">
<strong style="font-size:11px;color:#ef4444;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px">Reason:</strong>
{reason}
</div>
</td></tr>
<tr><td style="padding:16px 32px;background:#0a0f1a;border-top:1px solid #1e293b">
<p style="margin:0;font-size:12px;color:#64748b;font-family:monospace">PyDocAI &middot; AI-generated documentation</p>
</td></tr>
</table>
</td></tr></table></body></html>''',
            )

        # Delete user's projects and the user
        target.projects.all().delete()
        target.delete()
        return Response({'detail': 'User deleted successfully.'}, status=status.HTTP_200_OK)


class AdminUserBlockView(APIView):
    """Block or unblock a user (admin only). Toggles is_active."""
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            target = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if target == request.user:
            return Response({'detail': 'You cannot block yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        target.is_active = not target.is_active
        target.save(update_fields=['is_active'])

        action = 'blocked' if not target.is_active else 'unblocked'

        if settings.EMAIL_HOST_USER:
            send_email_task.delay(
                subject=f'Your PyDocAI account has been {action}',
                message=f'Your PyDocAI account has been {action} by an administrator.',
                recipient_list=[target.email],
            )

        return Response({'detail': f'User {action} successfully.', 'is_active': target.is_active})

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

class AdminUserProjectsView(ListAPIView):
    """List published projects for a specific user (admin only)."""
    permission_classes = [IsAdminUser]
    serializer_class = ProjectListSerializer

    def get_queryset(self):
        return (Project.objects
                .filter(user_id=self.kwargs['pk'], is_published=True)
                .select_related('user')
                .annotate(file_count=Count('files'))
                .order_by('-updated_at'))


class AdminProjectDetailView(RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProjectSerializer
    queryset = Project.objects.select_related('user').all()
    lookup_field = 'pk'
