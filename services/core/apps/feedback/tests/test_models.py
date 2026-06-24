import pytest

from apps.feedback.models import Feedback, FeedbackReply


class TestFeedbackModel:
    def test_create(self, user):
        fb = Feedback.objects.create(user=user, category='bug', message='Found a bug')
        assert fb.user == user
        assert fb.category == 'bug'
        assert fb.message == 'Found a bug'
        assert fb.is_resolved is False

    def test_str(self, user):
        fb = Feedback.objects.create(user=user, message='Test')
        assert user.email in str(fb)
        assert fb.category in str(fb)

    def test_ordering(self):
        assert Feedback._meta.ordering == ['-created_at']

    def test_db_table(self):
        assert Feedback._meta.db_table == 'feedback'

    def test_categories(self):
        assert Feedback.Category.GENERAL == 'general'
        assert Feedback.Category.BUG == 'bug'
        assert Feedback.Category.FEATURE == 'feature'


class TestFeedbackReplyModel:
    def test_create(self, user, feedback):
        reply = FeedbackReply.objects.create(feedback=feedback, user=user, message='Thanks!')
        assert reply.feedback == feedback
        assert reply.user == user
        assert reply.message == 'Thanks!'

    def test_str(self, user, feedback):
        reply = FeedbackReply.objects.create(feedback=feedback, user=user, message='Thanks!')
        assert user.email in str(reply)

    def test_ordering(self):
        assert FeedbackReply._meta.ordering == ['created_at']

    def test_db_table(self):
        assert FeedbackReply._meta.db_table == 'feedback_replies'
