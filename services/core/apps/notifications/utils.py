from django.conf import settings
from django.template.loader import render_to_string

from .models import Notification
from .tasks import send_email_task


def _snippet(text, maxlen=80):
    if not text:
        return ''
    return text[:maxlen] + ('...' if len(text) > maxlen else '')


def notify_comment(comment):
    project = comment.project
    owner = project.user
    if owner == comment.user:
        return

    commenter = comment.user.name or comment.user.email
    snippet = _snippet(comment.content)
    message = f'{commenter} commented on "{project.name}": "{snippet}"'
    Notification.objects.create(user=owner, comment=comment, message=message)

    if settings.EMAIL_HOST_USER:
        public_url = f'{settings.SITE_URL}/public/{project.public_slug}#comment-{comment.id}'
        send_email_task.delay(
            subject=f'New comment on "{project.name}"',
            message=comment.content,
            recipient_list=[owner.email],
            html_message=render_to_string('emails/notification_comment.html', {
                'project_name': project.name,
                'commenter': commenter,
                'comment_content': comment.content,
                'public_url': public_url,
            }),
        )


def notify_reply(comment):
    parent = comment.parent
    if not parent or not parent.user:
        return
    if parent.user == comment.user:
        return

    project = comment.project
    replier = comment.user.name or comment.user.email
    snippet = _snippet(comment.content)
    message = f'{replier} replied to your comment on "{project.name}": "{snippet}"'
    Notification.objects.create(user=parent.user, comment=comment, message=message)

    if settings.EMAIL_HOST_USER:
        public_url = f'{settings.SITE_URL}/public/{project.public_slug}#comment-{comment.id}'
        send_email_task.delay(
            subject=f'New reply on "{project.name}"',
            message=comment.content,
            recipient_list=[parent.user.email],
            html_message=render_to_string('emails/notification_reply.html', {
                'project_name': project.name,
                'replier': replier,
                'parent_content': parent.content,
                'reply_content': comment.content,
                'public_url': public_url,
            }),
        )
