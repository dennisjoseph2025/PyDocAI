from django.conf import settings
from django.db.models import Count, Q
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.tasks import send_email_task
from apps.users.models import User
from apps.users.serializers import AdminUserSerializer, UserSerializer


class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = User.objects.annotate(
            project_count=Count('projects'),
            published_count=Count('projects', filter=Q(projects__is_published=True)),
        )

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(name__icontains=search)
            )

        for field in ['is_active', 'is_verified', 'role']:
            val = request.query_params.get(field)
            if val is not None:
                qs = qs.filter(**{field: val})

        ordering = request.query_params.get('ordering', '-created_at')
        allowed = ['created_at', 'email', 'username', '-created_at', '-email', '-username']
        if ordering not in allowed:
            ordering = '-created_at'
        qs = qs.order_by(ordering)

        serializer = AdminUserSerializer(qs, many=True)
        return Response(serializer.data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class AdminUserDeleteView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            target = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason', 'No reason provided.')

        if settings.EMAIL_HOST_USER:
            subject = 'Your PyDocAI account has been deleted'
            send_email_task.delay(
                subject=subject,
                message=f'Your PyDocAI account has been deleted.\n\nReason: {reason}',
                recipient_list=[target.email],
                html_message=render_to_string('emails/account_deleted.html', {
                    'reason': reason,
                }),
            )

        target.projects.all().delete()
        target.delete()
        return Response({'detail': 'User deleted successfully.'}, status=status.HTTP_200_OK)


class AdminUserBlockView(APIView):
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
                html_message=render_to_string('emails/account_blocked.html', {
                    'action': action,
                }),
            )

        return Response({'detail': f'User {action} successfully.', 'is_active': target.is_active})
