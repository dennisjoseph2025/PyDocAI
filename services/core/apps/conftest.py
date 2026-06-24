import uuid

import pytest
from rest_framework.test import APIClient

from apps.projects.models import Project, ProjectFile
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        name='Test User',
        username='testuser',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email='other@example.com',
        password='otherpass123',
        name='Other User',
        username='otheruser',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email='admin@example.com',
        password='adminpass123',
        name='Admin User',
        username='admin',
        role='admin',
        is_staff=True,
    )


@pytest.fixture
def project(db, user):
    return Project.objects.create(
        user=user,
        name='Test Project',
        description='A test project',
        source_type=Project.SourceType.FILE,
        status=Project.Status.DONE,
    )


@pytest.fixture
def published_project(db, user, project):
    project.is_published = True
    project.public_slug = uuid.uuid4()
    project.save(update_fields=['is_published', 'public_slug'])
    return project


@pytest.fixture
def project_file(db, project):
    return ProjectFile.objects.create(
        project=project,
        file_name='main.py',
        file_path='src/main.py',
        content='print("hello")',
    )


@pytest.fixture
def comment(db, published_project, user):
    from apps.comments.models import Comment
    return Comment.objects.create(
        project=published_project,
        user=user,
        content='Great project!',
    )


@pytest.fixture
def notification(db, user):
    from apps.notifications.models import Notification
    return Notification.objects.create(
        user=user,
        message='Someone commented on your project',
    )


@pytest.fixture
def notification_with_comment(db, user, comment):
    from apps.notifications.models import Notification
    return Notification.objects.create(
        user=user,
        comment=comment,
        message='Someone commented on your project',
    )


@pytest.fixture
def feedback(db, user):
    from apps.feedback.models import Feedback
    return Feedback.objects.create(
        user=user,
        category='bug',
        message='Found a bug in the export feature',
    )
