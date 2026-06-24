import pytest

from apps.feedback.serializers import FeedbackReplySerializer, FeedbackSerializer


class TestFeedbackSerializer:
    def test_serialize(self, feedback):
        serializer = FeedbackSerializer(feedback)
        assert serializer.data['id'] == str(feedback.id)
        assert serializer.data['message'] == feedback.message
        assert serializer.data['user_name'] == feedback.user.name
        assert serializer.data['category'] == feedback.category
        assert serializer.data['is_resolved'] is False

    def test_read_only_fields(self, feedback):
        serializer = FeedbackSerializer(feedback)
        read_only = ['id', 'user', 'user_name', 'is_resolved', 'replies', 'created_at', 'updated_at']
        for field in read_only:
            assert field in serializer.data

    def test_replies_included(self, feedback, user):
        reply = feedback.replies.create(user=user, message='Reply')
        serializer = FeedbackSerializer(feedback)
        assert len(serializer.data['replies']) == 1
        assert serializer.data['replies'][0]['message'] == 'Reply'


class TestFeedbackReplySerializer:
    def test_serialize(self, feedback, user):
        reply = feedback.replies.create(user=user, message='A reply')
        serializer = FeedbackReplySerializer(reply)
        assert serializer.data['message'] == 'A reply'
        assert serializer.data['user_name'] == user.name

    def test_is_admin(self, feedback, admin_user):
        reply = feedback.replies.create(user=admin_user, message='Admin reply')
        serializer = FeedbackReplySerializer(reply)
        assert serializer.data['is_admin'] is True

    def test_is_not_admin(self, feedback, user):
        reply = feedback.replies.create(user=user, message='User reply')
        serializer = FeedbackReplySerializer(reply)
        assert serializer.data['is_admin'] is False
