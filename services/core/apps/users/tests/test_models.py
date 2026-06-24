
from apps.users.models import PasswordResetToken, User


class TestUserModel:
    def test_create_user(self, db):
        user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            name='Test User',
            username='testuser',
        )
        assert user.email == 'user@test.com'
        assert user.check_password('testpass123')
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_verified is False

    def test_create_superuser(self, db):
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='admin123',
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_email_as_username_field(self):
        assert User.USERNAME_FIELD == 'email'

    def test_str(self, user):
        assert str(user) == user.email


class TestPasswordResetToken:
    def test_create_token(self, user):
        token = PasswordResetToken.objects.create(user=user)
        assert token.user == user
        assert token.used is False
        assert token.is_valid() is True

    def test_used_token_invalid(self, user):
        token = PasswordResetToken.objects.create(user=user)
        token.used = True
        token.save()
        assert token.is_valid() is False

    def test_expired_token_invalid(self, user):
        from datetime import timedelta

        from django.utils import timezone
        token = PasswordResetToken.objects.create(user=user)
        token.created_at = timezone.now() - timedelta(hours=25)
        token.save()
        assert token.is_valid() is False
