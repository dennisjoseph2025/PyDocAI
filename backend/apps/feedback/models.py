import uuid
from django.db import models
from apps.users.models import User
from apps.projects.models import Project


class Feedback(models.Model):

    class Category(models.TextChoices):
        GENERAL     = 'general',     'General'
        DOCS_QUALITY= 'docs_quality','Documentation Quality'
        UI_UX       = 'ui_ux',       'UI / UX'
        PERFORMANCE = 'performance', 'Performance'
        BUG         = 'bug',         'Bug Report'
        FEATURE     = 'feature',     'Feature Request'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    project    = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
    category   = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    message    = models.TextField()
    is_resolved   = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'feedback'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — ({self.category})"


class FeedbackReply(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedback   = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='replies')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_replies')
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback_replies'
        ordering = ['created_at']

    def __str__(self):
        return f"Reply by {self.user.email} on {self.feedback.id}"
