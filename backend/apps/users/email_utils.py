import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """Send welcome email after successful registration."""
    subject = 'Welcome to PyDocAI!'
    message = render_to_string('emails/welcome.txt', {
        'user': user,
        'frontend_url': settings.FRONTEND_URL,
    })
    html_message = render_to_string('emails/welcome.html', {
        'user': user,
        'frontend_url': settings.FRONTEND_URL,
    })
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")


def send_password_reset_email(user, reset_token):
    """Send password reset email with token link."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}&email={user.email}"
    subject = 'Reset Your PyDocAI Password'
    message = render_to_string('emails/password_reset.txt', {
        'user': user,
        'reset_url': reset_url,
        'timeout_hours': settings.PASSWORD_RESET_TIMEOUT // 3600,
    })
    html_message = render_to_string('emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
        'timeout_hours': settings.PASSWORD_RESET_TIMEOUT // 3600,
    })
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
