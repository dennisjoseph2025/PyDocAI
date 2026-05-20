from rest_framework import serializers


class RepoImportSerializer(serializers.Serializer):
    full_name   = serializers.CharField()   
    folder_path = serializers.CharField(default='/')
    branch      = serializers.CharField(required=False, allow_blank=True)
    name        = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    custom_info = serializers.JSONField(required=False)