import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestAdminUserListView:
    def test_non_admin_forbidden(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('admin-user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list(self, api_client, admin_user, user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_search(self, api_client, admin_user, user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-list') + '?search=test@example.com'
        response = api_client.get(url)
        assert len(response.data) >= 1
        assert response.data[0]['email'] == 'test@example.com'


class TestAdminUserDetailView:
    def test_admin_can_view(self, api_client, admin_user, user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-detail', args=[user.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_not_found(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-detail', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAdminUserDeleteView:
    def test_admin_can_delete(self, api_client, admin_user, user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-delete', args=[user.id])
        response = api_client.post(url, {'reason': 'Inactive'}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_not_found(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-delete', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.post(url, {'reason': 'Test'}, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAdminUserBlockView:
    def test_admin_can_block(self, api_client, admin_user, user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-block', args=[user.id])
        response = api_client.post(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False
        user.refresh_from_db()
        assert user.is_active is False

    def test_admin_can_unblock(self, api_client, admin_user, user):
        user.is_active = False
        user.save()
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-block', args=[user.id])
        response = api_client.post(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is True

    def test_cannot_block_self(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('admin-user-block', args=[admin_user.id])
        response = api_client.post(url, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
