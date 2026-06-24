from unittest.mock import Mock

from apps.comments.throttles import CommentRateThrottle


class TestCommentRateThrottle:
    def test_get_cache_key_authenticated(self):
        throttle = CommentRateThrottle()
        request = Mock()
        request.user.is_authenticated = True
        request.user.pk = 'user-123'
        view = Mock()
        key = throttle.get_cache_key(request, view)
        assert key == 'comment_create:user-123'

    def test_get_cache_key_unauthenticated(self):
        throttle = CommentRateThrottle()
        request = Mock()
        request.user.is_authenticated = False
        view = Mock()
        key = throttle.get_cache_key(request, view)
        assert key is None

    def test_scope(self):
        assert CommentRateThrottle.scope == 'comment_create'
