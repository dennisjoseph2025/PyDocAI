from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['email', 'name', 'role', 'is_verified', 'github_connected', 'is_active', 'created_at']
    list_filter    = ['role', 'is_verified', 'is_active', 'created_at']
    search_fields  = ['email', 'name', 'username']
    ordering       = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'github_connected']
    actions        = ['verify_users', 'deactivate_users']

    fieldsets = (
        (None,       {'fields': ('email', 'password')}),
        ('Info',     {'fields': ('name', 'username', 'github_connected')}),
        ('Role',     {'fields': ('role', 'is_verified')}),
        ('Access',   {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates',    {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'name', 'password1', 'password2'),
        }),
    )

    @admin.display(boolean=True, description='GitHub')
    def github_connected(self, obj):
        return bool(obj.github_token)

    @admin.action(description='Mark selected users as verified')
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) verified.')

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display  = ['user', 'created_at', 'used', 'is_valid']
    list_filter   = ['used']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at']

    @admin.display(boolean=True)
    def is_valid(self, obj):
        return obj.is_valid()