from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_feedback_confirmation_email(feedback):
    """Send confirmation email after user submits feedback."""
    user = feedback.user
    subject = 'We received your feedback — PyDocAI'
    message = render_to_string('emails/feedback_confirmation.txt', {
        'user': user,
        'feedback': feedback,
        'frontend_url': settings.FRONTEND_URL,
    })
    html_message = render_to_string('emails/feedback_confirmation.html', {
        'user': user,
        'feedback': feedback,
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
        logger.info(f"Feedback confirmation email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send feedback confirmation to {user.email}: {e}")


def send_feedback_reply_email(reply):
    """Send notification to feedback owner when someone replies."""
    feedback = reply.feedback
    user = feedback.user
    subject = f'New reply on your feedback — PyDocAI'
    message = render_to_string('emails/feedback_reply.txt', {
        'user': user,
        'feedback': feedback,
        'reply': reply,
        'frontend_url': settings.FRONTEND_URL,
    })
    html_message = render_to_string('emails/feedback_reply.html', {
        'user': user,
        'feedback': feedback,
        'reply': reply,
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
        logger.info(f"Feedback reply email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send feedback reply to {user.email}: {e}")
