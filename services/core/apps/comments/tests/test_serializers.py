
from apps.comments.serializers import CommentCreateSerializer, CommentSerializer


class TestCommentSerializer:
    def test_serialize(self, comment):
        serializer = CommentSerializer(comment)
        assert serializer.data['id'] == str(comment.id)
        assert serializer.data['content'] == comment.content
        assert serializer.data['user_name'] == comment.user.name
        assert serializer.data['user_email'] == comment.user.email
        assert 'replies' in serializer.data
        assert 'parent_content' in serializer.data

    def test_serialize_with_replies(self, comment, user, project):
        comment.replies.create(project=project, user=user, content='Reply')
        serializer = CommentSerializer(comment)
        assert len(serializer.data['replies']) == 1
        assert serializer.data['replies'][0]['content'] == 'Reply'

    def test_serialize_depth_limit(self, comment):
        serializer = CommentSerializer(comment, context={'depth': 3})
        assert 'replies' not in serializer.data

    def test_parent_content(self, comment, user, project):
        reply = comment.replies.create(project=project, user=user, content='Reply')
        serializer = CommentSerializer(reply)
        assert serializer.data['parent_content'] == comment.content

    def test_no_parent_content(self, comment):
        serializer = CommentSerializer(comment)
        assert serializer.data['parent_content'] is None


class TestCommentCreateSerializer:
    def test_validate_valid_data(self):
        serializer = CommentCreateSerializer(data={'content': 'Nice project!'})
        assert serializer.is_valid()

    def test_validate_empty_content(self):
        serializer = CommentCreateSerializer(data={'content': ''})
        assert not serializer.is_valid()

    def test_serialize_created(self, comment):
        serializer = CommentCreateSerializer(comment)
        assert serializer.data['content'] == comment.content
