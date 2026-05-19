import uuid
from django.db import models
from apps.users.models import User


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
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.FILE)

    # single file
    file      = models.FileField(upload_to='uploads/%Y/%m/%d/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)

    # folder / zip
    zip_file  = models.FileField(upload_to='zips/%Y/%m/%d/', blank=True, null=True)

    # github
    github_url    = models.URLField(blank=True, null=True)
    github_branch = models.CharField(max_length=100, blank=True, default='main')

    # results
    parsed_data    = models.JSONField(blank=True, null=True)
    generated_docs = models.TextField(blank=True, null=True)
    readme_docs    = models.TextField(blank=True, null=True)  # Generated README
    api_docs       = models.TextField(blank=True, null=True)  # API Documentation
    project_info   = models.JSONField(blank=True, null=True)  # Project structure info
    custom_details = models.JSONField(blank=True, null=True)  # Extra user-provided context
    error_message  = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.source_type}) — {self.user.email}'

    @property
    def is_done(self):
        return self.status == self.Status.DONE

    @property
    def is_failed(self):
        return self.status == self.Status.FAILED


class ProjectFile(models.Model):

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')

    file_path  = models.CharField(max_length=500)  # e.g. src/utils/helpers.py
    file_name  = models.CharField(max_length=255)
    file_size  = models.PositiveIntegerField(blank=True, null=True)
    content    = models.TextField(blank=True)       # raw source code

    parsed_data    = models.JSONField(blank=True, null=True)   # ast result
    generated_docs = models.TextField(blank=True, null=True)   # ai result

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_files'
        ordering = ['file_path']

    def __str__(self):
        return f'{self.project.name} / {self.file_path}'