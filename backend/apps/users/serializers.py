from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['email', 'name', 'username', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled')
        data['user'] = user
        return data


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
    project_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['project_count']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        user = self.context['request'].user

        if user.has_password:
            # normal user — must provide old password
            old_password = data.get('old_password')
            if not old_password:
                raise serializers.ValidationError(
                    {'old_password': 'Old password is required'}
                )
            if not user.check_password(old_password):
                raise serializers.ValidationError(
                    {'old_password': 'Old password is incorrect'}
                )
        # github user — no old password needed, just set the new one

        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        

class GithubAuthSerializer(serializers.Serializer):
    code = serializers.CharField()
    

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=8)
        