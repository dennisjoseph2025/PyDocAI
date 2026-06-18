from rest_framework import serializers

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    replies = serializers.SerializerMethodField()
    parent_content = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'project', 'user', 'user_name', 'user_email',
            'parent', 'parent_content', 'content', 'replies', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'project']

    def get_replies(self, obj):
        replies = obj.replies.all()[:3]
        return CommentSerializer(replies, many=True).data

    def get_parent_content(self, obj):
        if obj.parent:
            return obj.parent.content
        return None

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('depth', 0) >= 3:
            fields.pop('replies', None)
        return fields


class CommentCreateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    parent_content = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'parent', 'parent_content', 'user_name', 'user_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'parent_content', 'user_name', 'user_email', 'created_at', 'updated_at']

    def get_parent_content(self, obj):
        if obj.parent:
            return obj.parent.content
        return None
