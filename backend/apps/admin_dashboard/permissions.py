from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Grant access if user is staff OR has admin role."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or getattr(request.user, 'is_admin', False))
        )
