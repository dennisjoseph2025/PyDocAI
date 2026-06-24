from unittest.mock import patch

import pytest
from django.conf import settings


pytestmark = pytest.mark.django_db


class TestSendEmailTask:
    def test_sends_email(self):
        from apps.notifications.tasks import send_email_task
        with patch('django.conf.settings.EMAIL_HOST_USER', 'test@example.com'):
            with patch('apps.notifications.tasks.send_mail') as mock:
                send_email_task(
                    subject='Test',
                    message='Body',
                    recipient_list=['user@test.com'],
                    html_message='<p>Body</p>',
                )
                mock.assert_called_once_with(
                    subject='Test',
                    message='Body',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['user@test.com'],
                    html_message='<p>Body</p>',
                    fail_silently=True,
                )

    def test_skips_when_no_email_host(self):
        from apps.notifications.tasks import send_email_task
        with patch('django.conf.settings.EMAIL_HOST_USER', None):
            with patch('apps.notifications.tasks.send_mail') as mock:
                send_email_task('Test', 'Body', ['user@test.com'])
                mock.assert_not_called()
