import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestAdminProjectListView:
    def test_non_admin_forbidden(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('admin-project-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list(self, api_client, admin_user, project):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-project-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        assert 'stats' in response.data
        assert 'results' in response.data

    def test_search(self, api_client, admin_user, project):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-project-list') + '?search=Test Project'
        response = api_client.get(url)
        assert response.data['count'] >= 1

    def test_filter_by_status(self, api_client, admin_user, project):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-project-list') + '?status=done'
        response = api_client.get(url)
        assert response.data['count'] >= 1


class TestAdminUserProjectsView:
    def test_list_user_published_projects(self, api_client, admin_user, user, published_project):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-projects', args=[user.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_unpublished_not_included(self, api_client, admin_user, user, project):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-projects', args=[user.id])
        response = api_client.get(url)
        published = [p for p in response.data if p['is_published']]
        assert len(published) == 0


class TestAdminProjectDetailView:
    def test_admin_can_view(self, api_client, admin_user, project):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-project-detail', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(project.id)

    def test_not_found(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-project-detail', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
