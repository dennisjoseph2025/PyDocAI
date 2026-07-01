from rest_framework import serializers

from ..models import Project, ProjectFile


class ProjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    files = ProjectFileSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'user', 'name', 'description', 'status', 'source_type',
            'file_name', 'file_size', 'github_url',
            'github_branch', 'parsed_data', 'generated_docs', 'readme_docs',
            'api_docs', 'project_info', 'custom_details', 'framework_info', 'error_message',
            'is_published', 'public_slug', 'published_description',
            'created_at', 'updated_at', 'files',
        ]
        read_only_fields = [
            'user', 'status', 'parsed_data', 'generated_docs',
            'readme_docs', 'api_docs', 'project_info', 'error_message',
            'public_slug',
        ]


class ProjectListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    file_count = serializers.SerializerMethodField()

    def get_file_count(self, obj):
        count = getattr(obj, 'file_count', obj.files.count())
        if count:
            return count
        if isinstance(obj.project_info, dict):
            return obj.project_info.get('file_count', 0)
        return 0

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'source_type',
            'is_published', 'public_slug', 'published_description',
            'created_at', 'updated_at', 'user_name', 'user_email', 'file_count', 'framework_info',
        ]
