from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_email_task(subject, message, recipient_list, html_message=None):
    if not settings.EMAIL_HOST_USER:
        return
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=True,
    )
