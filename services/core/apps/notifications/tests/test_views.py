import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestNotificationListView:
    def test_unauthenticated(self, api_client):
        url = reverse('notification_list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_user_notifications(self, api_client, user, notification):
        api_client.force_authenticate(user=user)
        url = reverse('notification_list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['message'] == notification.message

    def test_does_not_return_other_user_notifications(self, api_client, other_user, notification):
        api_client.force_authenticate(user=other_user)
        url = reverse('notification_list')
        response = api_client.get(url)
        assert response.data == []

    def test_limit_param(self, api_client, user):
        for i in range(5):
            from apps.notifications.models import Notification
            Notification.objects.create(user=user, message=f'Notification {i}')
        api_client.force_authenticate(user=user)
        url = reverse('notification_list') + '?limit=2'
        response = api_client.get(url)
        assert len(response.data) == 2


class TestUnreadCountView:
    def test_unauthenticated(self, api_client):
        url = reverse('notification_unread_count')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_count(self, api_client, user, notification):
        api_client.force_authenticate(user=user)
        url = reverse('notification_unread_count')
        response = api_client.get(url)
        assert response.data['unread_count'] == 1

    def test_zero_when_all_read(self, api_client, user, notification):
        notification.is_read = True
        notification.save()
        api_client.force_authenticate(user=user)
        url = reverse('notification_unread_count')
        response = api_client.get(url)
        assert response.data['unread_count'] == 0


class TestMarkReadView:
    def test_mark_read(self, api_client, user, notification):
        api_client.force_authenticate(user=user)
        url = reverse('notification_mark_read', args=[notification.id])
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        notification.refresh_from_db()
        assert notification.is_read is True


class TestMarkAllReadView:
    def test_mark_all_read(self, api_client, user):
        from apps.notifications.models import Notification
        Notification.objects.create(user=user, message='N1')
        Notification.objects.create(user=user, message='N2')
        api_client.force_authenticate(user=user)
        url = reverse('notification_mark_all_read')
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Notification.objects.filter(user=user, is_read=False).count() == 0


class TestNotificationDeleteView:
    def test_delete(self, api_client, user, notification):
        api_client.force_authenticate(user=user)
        url = reverse('notification_delete', args=[notification.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not type(notification).objects.filter(id=notification.id).exists()


class TestClearAllNotificationsView:
    def test_clear_all(self, api_client, user):
        from apps.notifications.models import Notification
        Notification.objects.create(user=user, message='N1')
        Notification.objects.create(user=user, message='N2')
        api_client.force_authenticate(user=user)
        url = reverse('notification_clear_all')
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Notification.objects.filter(user=user).count() == 0
