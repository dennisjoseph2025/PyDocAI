from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status


pytestmark = pytest.mark.django_db


class TestProjectListView:
    def test_unauthenticated(self, api_client):
        url = reverse('project_list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_own_projects(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('project_list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        assert 'stats' in response.data
        assert 'results' in response.data

    def test_does_not_show_others_projects(self, api_client, other_user, project):
        api_client.force_authenticate(user=other_user)
        url = reverse('project_list')
        response = api_client.get(url)
        assert response.data['count'] == 0

    def test_filter_by_status(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('project_list') + '?status=done'
        response = api_client.get(url)
        assert response.data['count'] >= 1


class TestProjectDetailView:
    def test_get_own_project(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('project_detail', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(project.id)

    def test_cannot_get_others_project(self, api_client, other_user, project):
        api_client.force_authenticate(user=other_user)
        url = reverse('project_detail', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_not_found(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('project_detail', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('project_detail', args=[project.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_200_OK


class TestPublishProjectView:
    def test_publish(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('project_publish', args=[project.id])
        response = api_client.patch(url, {'is_published': True, 'published_description': 'My docs'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_published'] is True

    def test_unpublish(self, api_client, user, project):
        project.is_published = True
        project.save()
        api_client.force_authenticate(user=user)
        url = reverse('project_publish', args=[project.id])
        response = api_client.patch(url, {'is_published': False}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_published'] is False

    def test_missing_field(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('project_publish', args=[project.id])
        response = api_client.patch(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_not_owner(self, api_client, other_user, project):
        api_client.force_authenticate(user=other_user)
        url = reverse('project_publish', args=[project.id])
        response = api_client.patch(url, {'is_published': True}, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPublicProjectListView:
    def test_list_published(self, api_client, published_project):
        url = reverse('public_project_list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_unpublished_not_listed(self, api_client, project):
        url = reverse('public_project_list')
        response = api_client.get(url)
        for p in response.data['results']:
            assert p['is_published'] is True

    def test_search(self, api_client, published_project):
        url = reverse('public_project_list') + '?search=Test'
        response = api_client.get(url)
        assert len(response.data['results']) >= 1


class TestPublicProjectDetailView:
    def test_get_published(self, api_client, published_project):
        url = reverse('public_project_detail', args=[published_project.public_slug])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == published_project.name

    def test_not_found(self, api_client):
        url = reverse('public_project_detail', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
