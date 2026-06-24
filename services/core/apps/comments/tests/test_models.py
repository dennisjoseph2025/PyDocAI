import pytest
from django.db import models as db_models

from apps.comments.models import Comment


class TestCommentModel:
    def test_fields(self):
        fields = [f.name for f in Comment._meta.get_fields()]
        assert 'id' in fields
        assert 'project' in fields
        assert 'user' in fields
        assert 'parent' in fields
        assert 'content' in fields
        assert 'created_at' in fields
        assert 'updated_at' in fields

    def test_str(self, comment):
        assert comment.user.email in str(comment)
        assert comment.project.name in str(comment)

    def test_ordering(self):
        assert Comment._meta.ordering == ['created_at']

    def test_db_table(self):
        assert Comment._meta.db_table == 'comments'

    def test_indexes(self):
        field_names = [list(idx.fields) for idx in Comment._meta.indexes]
        assert ['project', 'created_at'] in field_names
        assert ['user', 'created_at'] in field_names

    def test_parent_relation(self, comment, user, project):
        reply = Comment.objects.create(project=project, user=user, parent=comment, content='A reply')
        assert reply.parent == comment
        assert list(comment.replies.all()) == [reply]

    def test_content_max_length(self):
        field = Comment._meta.get_field('content')
        assert isinstance(field, db_models.TextField)
