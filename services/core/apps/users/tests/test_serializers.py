import pytest

from apps.users.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


class TestRegisterSerializer:
    def test_valid_data(self):
        data = {
            'email': 'new@test.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'name': 'New User',
            'username': 'newuser',
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid()

    def test_password_mismatch(self):
        data = {
            'email': 'new@test.com',
            'password': 'pass123',
            'password2': 'pass456',
            'username': 'newuser',
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()

    def test_missing_email(self):
        serializer = RegisterSerializer(data={'password': 'pass123', 'password2': 'pass123'})
        assert not serializer.is_valid()


class TestLoginSerializer:
    def test_valid_credentials(self, user):
        data = {'email': user.email, 'password': 'testpass123'}
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['user'] == user

    def test_invalid_password(self, user):
        data = {'email': user.email, 'password': 'wrong'}
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()

    def test_nonexistent_user(self):
        data = {'email': 'nobody@test.com', 'password': 'pass123'}
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()


class TestUserSerializer:
    def test_serialize(self, user):
        serializer = UserSerializer(user)
        assert serializer.data['email'] == user.email
        assert serializer.data['name'] == user.name
        assert 'password' not in serializer.data

    def test_deserialize(self):
        data = {'email': 'test@test.com', 'name': 'Test', 'username': 'test'}
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()


class TestChangePasswordSerializer:
    def test_valid(self, user):
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewPass123!',
            'new_password2': 'NewPass123!',
        }
        serializer = ChangePasswordSerializer(data=data, context={'request': type('req', (), {'user': user})()})
        assert serializer.is_valid()
