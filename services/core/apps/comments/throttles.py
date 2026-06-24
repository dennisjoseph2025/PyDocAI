from rest_framework.throttling import SimpleRateThrottle


class CommentRateThrottle(SimpleRateThrottle):
    scope = 'comment_create'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'comment_create:{request.user.pk}'
        return None
