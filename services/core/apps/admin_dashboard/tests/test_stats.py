import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestAdminStatsView:
    def test_non_admin_forbidden(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('admin-stats')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-stats')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'users' in response.data
        assert 'projects' in response.data
        assert 'top_users' in response.data

    def test_user_stats(self, api_client, admin_user, user, other_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-stats')
        response = api_client.get(url)
        assert response.data['users']['total'] >= 3

    def test_project_stats(self, api_client, admin_user, project):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-stats')
        response = api_client.get(url)
        assert response.data['projects']['total'] >= 1
