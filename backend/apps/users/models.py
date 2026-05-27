import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('is_verified', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        ADMIN  = 'admin',  'Admin'
        USER = 'user', 'User'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email        = models.EmailField(unique=True)
    username     = models.CharField(max_length=50, unique=True, blank=True, null=True)
    role         = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    github_token = models.CharField(max_length=255, blank=True, null=True)
    name         = models.CharField(max_length=100)
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    is_verified  = models.BooleanField(default=False)

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def has_password(self):
        # Users who signed up via OAuth have an unusable password
        return self.password and not self.password.startswith('!')



class PasswordResetToken(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'

    def is_valid(self):
        from django.conf import settings
        expiry = self.created_at + timezone.timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
        return not self.used and timezone.now() < expiry

    def __str__(self):
        return f"Reset token for {self.user.email}"