from django.urls import path

from . import views

urlpatterns = [
    path('projects/<uuid:project_id>/', views.ProjectDetail.as_view(), name='internal-project'),
    path('projects/<uuid:project_id>/files/', views.ProjectFileList.as_view(), name='internal-project-files'),
    path('projects/<uuid:project_id>/parsed/', views.ReceiveParsedData.as_view(), name='internal-parsed'),
    path('projects/<uuid:project_id>/ai-docs/', views.ReceiveAIDocs.as_view(), name='internal-ai-docs'),
]
