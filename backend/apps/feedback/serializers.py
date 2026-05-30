from rest_framework import serializers

from .models import Feedback, FeedbackReply


class FeedbackReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    is_admin  = serializers.SerializerMethodField()

    class Meta:
        model = FeedbackReply
        fields = ['id', 'feedback', 'user', 'user_name', 'is_admin', 'message', 'created_at']
        read_only_fields = ['id', 'feedback', 'user', 'user_name', 'is_admin', 'created_at']

    def get_is_admin(self, obj):
        return obj.user.is_staff or getattr(obj.user, 'is_admin', False)


class FeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    replies   = FeedbackReplySerializer(many=True, read_only=True)

    class Meta:
        model = Feedback
        fields = [
            'id', 'user', 'user_name', 'project', 'category',
            'message', 'is_resolved',
            'replies', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'user_name', 'is_resolved', 'replies', 'created_at', 'updated_at']

