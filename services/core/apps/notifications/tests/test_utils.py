from unittest.mock import patch

import pytest

from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


class TestNotifyComment:
    def test_creates_notification_for_project_owner(self, project, other_user):
        from apps.comments.models import Comment
        comment = Comment.objects.create(project=project, user=other_user, content='Nice!')
        from apps.notifications.utils import notify_comment
        notify_comment(comment)
        assert Notification.objects.filter(user=project.user).count() == 1

    def test_skips_when_commenter_is_owner(self, project, user):
        from apps.comments.models import Comment
        comment = Comment.objects.create(project=project, user=user, content='Self comment')
        from apps.notifications.utils import notify_comment
        notify_comment(comment)
        assert Notification.objects.filter(user=project.user).count() == 0

    def test_message_format(self, project, other_user):
        from apps.comments.models import Comment
        comment = Comment.objects.create(project=project, user=other_user, content='Nice project!')
        from apps.notifications.utils import notify_comment
        notify_comment(comment)
        notification = Notification.objects.get(user=project.user)
        assert comment.user.name in notification.message
        assert project.name in notification.message
        assert comment.content[:80] in notification.message

    def test_sends_email_when_configured(self, project, other_user):
        from apps.comments.models import Comment
        comment = Comment.objects.create(project=project, user=other_user, content='Nice!')
        from apps.notifications.utils import notify_comment
        with (
            patch('django.conf.settings.EMAIL_HOST_USER', 'test@example.com'),
            patch('apps.notifications.utils.send_email_task.delay') as mock,
        ):
            notify_comment(comment)
            mock.assert_called_once()
            args = mock.call_args[1]
            assert 'New comment' in args['subject']
            assert project.user.email in args['recipient_list']

    def test_skips_email_when_not_configured(self, project, other_user):
        from apps.comments.models import Comment
        comment = Comment.objects.create(project=project, user=other_user, content='Nice!')
        from apps.notifications.utils import notify_comment
        with (
            patch('django.conf.settings.EMAIL_HOST_USER', None),
            patch('apps.notifications.utils.send_email_task.delay') as mock,
        ):
                notify_comment(comment)
                mock.assert_not_called()

    def test_links_comment_to_notification(self, project, other_user):
        from apps.comments.models import Comment
        comment = Comment.objects.create(project=project, user=other_user, content='Nice!')
        from apps.notifications.utils import notify_comment
        notify_comment(comment)
        notification = Notification.objects.get(user=project.user)
        assert notification.comment == comment


class TestNotifyReply:
    def test_creates_notification_for_parent_author(self, project, other_user):
        from apps.comments.models import Comment
        parent = Comment.objects.create(project=project, user=other_user, content='Original')
        reply = Comment.objects.create(project=project, user=project.user, parent=parent, content='A reply')
        from apps.notifications.utils import notify_reply
        notify_reply(reply)
        assert Notification.objects.filter(user=other_user).count() == 1

    def test_skips_if_no_parent(self, project, other_user):
        from apps.comments.models import Comment
        comment = Comment.objects.create(project=project, user=other_user, content='No parent')
        from apps.notifications.utils import notify_reply
        notify_reply(comment)
        assert Notification.objects.count() == 0

    def test_skips_if_replier_is_parent(self, project, user):
        from apps.comments.models import Comment
        parent = Comment.objects.create(project=project, user=user, content='My comment')
        reply = Comment.objects.create(project=project, user=user, parent=parent, content='Self reply')
        from apps.notifications.utils import notify_reply
        notify_reply(reply)
        assert Notification.objects.count() == 0

    def test_sends_email_when_configured(self, project, other_user):
        from apps.comments.models import Comment
        parent = Comment.objects.create(project=project, user=other_user, content='Original')
        reply = Comment.objects.create(project=project, user=project.user, parent=parent, content='Reply')
        from apps.notifications.utils import notify_reply
        with (
            patch('django.conf.settings.EMAIL_HOST_USER', 'test@example.com'),
            patch('apps.notifications.utils.send_email_task.delay') as mock,
        ):
                notify_reply(reply)
                mock.assert_called_once()
                assert 'New reply' in mock.call_args[1]['subject']
