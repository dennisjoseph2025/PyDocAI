from unittest.mock import patch

import pytest

pytestmark = pytest.mark.django_db


class TestSendFeedbackConfirmationTask:
    def test_calls_email_utils(self, feedback):
        from apps.feedback.tasks import send_feedback_confirmation_task
        with patch('apps.feedback.email_utils.send_feedback_confirmation_email') as mock:
            send_feedback_confirmation_task(feedback.id)
            mock.assert_called_once()
            assert mock.call_args[0][0] == feedback

    def test_handles_missing_feedback(self):
        from apps.feedback.tasks import send_feedback_confirmation_task
        with patch('apps.feedback.tasks.logger.error') as mock_log:
            send_feedback_confirmation_task(999)
            mock_log.assert_called_once()


class TestSendFeedbackReplyTask:
    def test_calls_email_utils(self, feedback, user):
        from apps.feedback.tasks import send_feedback_reply_task
        reply = feedback.replies.create(user=user, message='Reply')
        with patch('apps.feedback.email_utils.send_feedback_reply_email') as mock:
            send_feedback_reply_task(reply.id)
            mock.assert_called_once()
            assert mock.call_args[0][0] == reply
