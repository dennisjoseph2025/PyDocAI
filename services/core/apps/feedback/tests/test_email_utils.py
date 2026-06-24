from unittest.mock import patch

import pytest


pytestmark = pytest.mark.django_db


class TestSendFeedbackConfirmationEmail:
    def test_sends_email(self, feedback):
        from apps.feedback.email_utils import send_feedback_confirmation_email
        with patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'noreply@test.com'):
            with patch('apps.feedback.email_utils.send_mail') as mock:
                send_feedback_confirmation_email(feedback)
                mock.assert_called_once()
                args = mock.call_args[1]
                assert 'We received your feedback' in args['subject']
                assert feedback.user.email in args['recipient_list']

    def test_logs_on_failure(self, feedback, caplog):
        import logging
        from apps.feedback.email_utils import send_feedback_confirmation_email
        with patch('apps.feedback.email_utils.send_mail', side_effect=Exception('SMTP error')):
            with caplog.at_level(logging.ERROR):
                send_feedback_confirmation_email(feedback)
                assert 'Failed to send feedback confirmation' in caplog.text


class TestSendFeedbackReplyEmail:
    def test_sends_email(self, feedback, user):
        from apps.feedback.email_utils import send_feedback_reply_email
        reply = feedback.replies.create(user=user, message='Reply')
        with patch('django.conf.settings.DEFAULT_FROM_EMAIL', 'noreply@test.com'):
            with patch('apps.feedback.email_utils.send_mail') as mock:
                send_feedback_reply_email(reply)
                mock.assert_called_once()
                assert 'New reply on your feedback' in mock.call_args[1]['subject']
