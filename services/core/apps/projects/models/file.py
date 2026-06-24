import uuid

from django.db import models


class ProjectFile(models.Model):

    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='files')

    file_path  = models.CharField(max_length=500)
    file_name  = models.CharField(max_length=255)
    file_size  = models.PositiveIntegerField(blank=True, null=True)
    content    = models.TextField(blank=True)

    parsed_data    = models.JSONField(blank=True, null=True)
    generated_docs = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_files'
        ordering = ['file_path']

    def __str__(self):
        return f'{self.project.name} / {self.file_path}'
