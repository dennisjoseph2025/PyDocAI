from django.urls import path

from apps.universal.views import UniversalUploadView, UniversalStatusView

urlpatterns = [
    path('upload/', UniversalUploadView.as_view(), name='universal-upload'),
    path('status/<uuid:project_id>/', UniversalStatusView.as_view(), name='universal-status'),
]
