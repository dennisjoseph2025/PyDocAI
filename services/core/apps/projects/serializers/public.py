from rest_framework import serializers

from ..models import Project


class PublicProjectSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    file_count = serializers.SerializerMethodField()

    def get_file_count(self, obj):
        return getattr(obj, 'file_count', obj.files.count())

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'published_description',
            'generated_docs', 'readme_docs', 'api_docs',
            'user_name', 'file_count', 'is_published', 'public_slug', 'source_type',
            'github_url', 'github_branch',
            'created_at', 'updated_at',
        ]


class PublicProjectListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    file_count = serializers.SerializerMethodField()

    def get_file_count(self, obj):
        return getattr(obj, 'file_count', obj.files.count())

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'published_description',
            'user_name', 'file_count', 'public_slug', 'source_type',
            'created_at', 'updated_at',
        ]
