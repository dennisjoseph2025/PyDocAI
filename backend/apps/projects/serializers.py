from rest_framework import serializers
from .models import Project, ProjectFile

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
            'file', 'file_name', 'file_size', 'zip_file', 'github_url',
            'github_branch', 'parsed_data', 'generated_docs', 'readme_docs',
            'api_docs', 'project_info', 'custom_details', 'error_message', 'created_at', 'updated_at', 'files'
        ]
        read_only_fields = ['user', 'status', 'parsed_data', 'generated_docs', 
                          'readme_docs', 'api_docs', 'project_info', 'error_message']

class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status', 'source_type', 'created_at']
