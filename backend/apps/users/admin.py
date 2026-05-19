from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['email', 'name', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter    = ['role', 'is_verified', 'is_active']
    search_fields  = ['email', 'name', 'username']
    ordering       = ['-created_at']
    fieldsets      = (
        (None,       {'fields': ('email', 'password')}),
        ('Info',     {'fields': ('name', 'username', 'github_token')}),
        ('Role',     {'fields': ('role', 'is_verified')}),
        ('Access',   {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates',    {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields     = ['created_at', 'updated_at']
    add_fieldsets       = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'name', 'password1', 'password2'),
        }),
    )