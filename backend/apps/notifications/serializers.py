from rest_framework import serializers

from .models import Notification
from apps.comments.serializers import CommentSerializer


class NotificationSerializer(serializers.ModelSerializer):
    comment = CommentSerializer(read_only=True)
    project_slug = serializers.CharField(source='comment.project.public_slug', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'comment', 'project_slug', 'created_at']
