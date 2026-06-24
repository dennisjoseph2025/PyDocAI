import pytest

from apps.notifications.serializers import NotificationSerializer


class TestNotificationSerializer:
    def test_serialize(self, notification):
        serializer = NotificationSerializer(notification)
        assert serializer.data['id'] == str(notification.id)
        assert serializer.data['message'] == notification.message
        assert serializer.data['is_read'] is False
        assert 'comment' in serializer.data
        assert 'created_at' in serializer.data

    def test_serialize_with_comment(self, notification_with_comment):
        serializer = NotificationSerializer(notification_with_comment)
        assert serializer.data['comment'] is not None
        assert serializer.data['comment']['content'] == 'Great project!'
        assert serializer.data['project_slug'] == str(notification_with_comment.comment.project.public_slug)

    def test_read_only_fields(self, notification):
        serializer = NotificationSerializer(notification)
        for field in ['id', 'message', 'is_read', 'created_at']:
            assert field in serializer.data

    def test_project_slug_with_comment(self, notification_with_comment):
        serializer = NotificationSerializer(notification_with_comment)
        assert 'project_slug' in serializer.data
        assert serializer.data['project_slug'] == str(notification_with_comment.comment.project.public_slug)
