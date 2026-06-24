import pytest

from apps.notifications.models import Notification


class TestNotificationModel:
    def test_create(self, user):
        notification = Notification.objects.create(
            user=user,
            message='Someone commented on your project',
        )
        assert notification.user == user
        assert notification.message == 'Someone commented on your project'
        assert notification.is_read is False

    def test_str(self, notification):
        assert notification.user.email in str(notification)
        assert notification.message[:50] in str(notification)

    def test_mark_read(self, notification):
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_ordering(self):
        assert Notification._meta.ordering == ['-created_at']

    def test_db_table(self):
        assert Notification._meta.db_table == 'notifications'

    def test_indexes(self):
        field_names = [list(idx.fields) for idx in Notification._meta.indexes]
        assert ['user', 'is_read', 'created_at'] in field_names
