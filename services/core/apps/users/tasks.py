import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email_task(user_id):
    from .email_utils import send_welcome_email
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        send_welcome_email(user)
    except Exception as e:
        logger.error(f"send_welcome_email_task failed for user {user_id}: {e}")


@shared_task
def send_password_reset_email_task(user_id, token_str):
    from .email_utils import send_password_reset_email
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        send_password_reset_email(user, token_str)
    except Exception as e:
        logger.error(f"send_password_reset_email_task failed for user {user_id}: {e}")
