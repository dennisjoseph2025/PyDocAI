import uuid

from django.db import models


class Project(models.Model):

    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE       = 'done',       'Done'
        FAILED     = 'failed',     'Failed'

    class SourceType(models.TextChoices):
        FILE   = 'file',   'Single File'
        FOLDER = 'folder', 'Folder / ZIP'
        GITHUB = 'github', 'GitHub Link'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='projects')
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.FILE)

    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)

    github_url    = models.URLField(blank=True, null=True)
    github_branch = models.CharField(max_length=100, blank=True, default='main')

    parsed_data    = models.JSONField(blank=True, null=True)
    generated_docs = models.TextField(blank=True, null=True)
    readme_docs    = models.TextField(blank=True, null=True)
    api_docs       = models.TextField(blank=True, null=True)
    project_info   = models.JSONField(blank=True, null=True)
    custom_details = models.JSONField(blank=True, null=True)
    framework_info = models.JSONField(blank=True, null=True)
    error_message  = models.TextField(blank=True, null=True)

    is_published           = models.BooleanField(default=False)
    public_slug            = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    published_description  = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['source_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['is_published', 'created_at']),
        ]

    def __str__(self):
        return f'{self.name} ({self.source_type}) \u2014 {self.user.email}'

    @property
    def is_done(self):
        return self.status == self.Status.DONE

    @property
    def is_failed(self):
        return self.status == self.Status.FAILED
