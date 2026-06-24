from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.utils import notify_comment, notify_reply
from apps.projects.models import Project

from ..models import Comment
from ..serializers import CommentCreateSerializer, CommentSerializer
from ..throttles import CommentRateThrottle


class CommentListView(APIView):
    permission_classes = []

    def get(self, request, project_id):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if not project.is_published and not request.user.is_authenticated:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if not project.is_published and request.user.is_authenticated and project.user != request.user:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        offset = int(request.query_params.get('offset', 0))
        limit = min(int(request.query_params.get('limit', 20)), 50)

        top_level = Comment.objects.filter(
            project=project, parent__isnull=True
        ).select_related('user').order_by('created_at')[offset:offset + limit]

        comments = CommentSerializer(top_level, many=True, context={'depth': 0}).data
        has_next = Comment.objects.filter(
            project=project, parent__isnull=True
        ).count() > offset + limit

        return Response({
            'comments': comments,
            'has_next': has_next,
            'total': offset + len(comments),
        })


class CommentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CommentRateThrottle]

    def post(self, request, project_id):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save(user=request.user, project=project)
        if comment.parent:
            notify_reply(comment)
        else:
            notify_comment(comment)

        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk, user=request.user)
        except Comment.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        comment.content = '[deleted]'
        comment.save(update_fields=['content'])
        return Response(status=status.HTTP_204_NO_CONTENT)
