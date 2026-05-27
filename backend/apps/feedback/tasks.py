from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_feedback_confirmation_task(feedback_id):
    from .models import Feedback
    from .email_utils import send_feedback_confirmation_email
    try:
        fb = Feedback.objects.select_related('user').get(id=feedback_id)
        send_feedback_confirmation_email(fb)
    except Exception as e:
        logger.error(f"send_feedback_confirmation_task failed for feedback {feedback_id}: {e}")


@shared_task
def send_feedback_reply_task(reply_id):
    from .models import FeedbackReply
    from .email_utils import send_feedback_reply_email
    try:
        reply = FeedbackReply.objects.select_related('user', 'feedback__user').get(id=reply_id)
        send_feedback_reply_email(reply)
    except Exception as e:
        logger.error(f"send_feedback_reply_task failed for reply {reply_id}: {e}")
