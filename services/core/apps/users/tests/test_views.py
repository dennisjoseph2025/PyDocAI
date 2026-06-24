from unittest.mock import patch

import pytest
import requests
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestRegisterView:
    def test_register_success(self, api_client):
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'name': 'New User',
            'username': 'newuser',
        }
        with patch('apps.users.tasks.send_welcome_email_task.delay'):
            response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'

    def test_register_password_mismatch(self, api_client):
        url = reverse('register')
        data = {
            'email': 'test@example.com',
            'password': 'pass123',
            'password2': 'pass456',
            'username': 'testuser',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client, user):
        url = reverse('register')
        data = {
            'email': user.email,
            'password': 'Pass123!',
            'password2': 'Pass123!',
            'username': 'another',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLoginView:
    def test_login_success(self, api_client, user):
        url = reverse('login')
        response = api_client.post(url, {'email': user.email, 'password': 'testpass123'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']

    def test_login_wrong_password(self, api_client, user):
        url = reverse('login')
        response = api_client.post(url, {'email': user.email, 'password': 'wrong'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent(self, api_client):
        url = reverse('login')
        response = api_client.post(url, {'email': 'nobody@test.com', 'password': 'pass'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogoutView:
    def test_logout_success(self, api_client, user):
        api_client.force_authenticate(user=user)
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        url = reverse('logout')
        response = api_client.post(url, {'refresh': str(token)}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_logout_unauthenticated(self, api_client):
        url = reverse('logout')
        response = api_client.post(url, {'refresh': 'some-token'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_no_token(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('logout')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestProfileView:
    def test_get_profile(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_update_profile(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('profile')
        response = api_client.patch(url, {'name': 'Updated Name'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'

    def test_unauthenticated(self, api_client):
        url = reverse('profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePasswordView:
    def test_change_password(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('change_password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewPass123!',
            'new_password2': 'NewPass123!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_wrong_old_password(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('change_password')
        data = {
            'old_password': 'wrong',
            'new_password': 'NewPass123!',
            'new_password2': 'NewPass123!',
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGithubAuthView:
    def test_missing_code(self, api_client):
        url = reverse('github-auth')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_github_error(self, api_client):
        url = reverse('github-auth')
        with patch('apps.users.views.auth.exchange_code_for_token', side_effect=requests.RequestException('Network error')):
            response = api_client.post(url, {'code': 'bad-code'}, format='json')
            assert response.status_code == status.HTTP_502_BAD_GATEWAY


class TestUserListView:
    def test_non_admin_returns_empty(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('user_list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []
