from django.contrib import admin
from django.urls import include, path

from apps.projects.urls import public_urlpatterns as public_project_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/public/projects/', include(public_project_urls)),
    path('api/parser/', include('apps.parser.urls')),
    path('api/ai/', include('apps.ai.urls')),
    path('api/github/', include('apps.github_integration.urls')),
    path('api/exports/', include('apps.exports.urls')),
    path('api/admin-dashboard/', include('apps.admin_dashboard.urls')),
    path('api/feedback/', include('apps.feedback.urls')),
    path('api/comments/', include('apps.comments.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    # Internal microservice communication endpoints
    path('api/internal/', include('apps.internal.urls')),
    path('api/universal/', include('apps.universal.urls')),
]
