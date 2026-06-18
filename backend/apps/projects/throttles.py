from rest_framework.throttling import SimpleRateThrottle


class PublishRateThrottle(SimpleRateThrottle):
    scope = 'publish'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'publish:{request.user.pk}'
        return None


class PublicRateThrottle(SimpleRateThrottle):
    scope = 'public'

    def get_cache_key(self, request, view):
        return self.get_ident(request)
