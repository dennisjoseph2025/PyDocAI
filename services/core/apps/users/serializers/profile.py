from rest_framework import serializers

from ..models import User


class UserSerializer(serializers.ModelSerializer):
    has_password = serializers.BooleanField(read_only=True)

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'name', 'username', 'role',
            'is_verified', 'has_password', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'role', 'is_verified',
            'has_password', 'created_at', 'updated_at'
        ]


class AdminUserSerializer(UserSerializer):
    project_count    = serializers.IntegerField(read_only=True)
    published_count  = serializers.IntegerField(read_only=True)
    github_connected = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['project_count', 'published_count', 'github_connected']

    def get_github_connected(self, obj):
        return bool(obj.github_token)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        user = self.context['request'].user

        if user.has_password:
            old_password = data.get('old_password')
            if not old_password:
                raise serializers.ValidationError(
                    {'old_password': 'Old password is required'}
                )
            if not user.check_password(old_password):
                raise serializers.ValidationError(
                    {'old_password': 'Old password is incorrect'}
                )

        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
