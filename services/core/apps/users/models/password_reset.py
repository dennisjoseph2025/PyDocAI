import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class PasswordResetToken(models.Model):
    user  = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'

    def is_valid(self):
        expiry = self.created_at + timezone.timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
        return not self.used and timezone.now() < expiry

    def __str__(self):
        return f"Reset token for {self.user.email}"
