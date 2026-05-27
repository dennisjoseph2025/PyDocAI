from django.contrib import admin
from .models import Feedback, FeedbackReply


class FeedbackReplyInline(admin.TabularInline):
    model = FeedbackReply
    extra = 0
    readonly_fields = ['user', 'message', 'created_at']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display  = ['user', 'category', 'project', 'is_resolved', 'created_at']
    list_filter   = ['category', 'is_resolved', 'created_at']
    search_fields = ['user__email', 'message']
    ordering      = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines       = [FeedbackReplyInline]
    actions       = ['mark_resolved']

    @admin.action(description='Mark selected feedback as resolved')
    def mark_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} feedback item(s) marked as resolved.')


@admin.register(FeedbackReply)
class FeedbackReplyAdmin(admin.ModelAdmin):
    list_display  = ['feedback', 'user', 'created_at']
    list_filter   = ['created_at']
    search_fields = ['user__email', 'message']
    readonly_fields = ['feedback', 'user', 'message', 'created_at']
