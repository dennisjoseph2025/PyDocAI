from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/parser/', include('apps.parser.urls')),
    path('api/ai/', include('apps.ai.urls')),
    path('api/github/', include('apps.github_integration.urls')),
    path('api/exports/', include('apps.exports.urls')),
    path('api/admin-dashboard/', include('apps.admin_dashboard.urls')),
    path('api/feedback/', include('apps.feedback.urls')),
]
