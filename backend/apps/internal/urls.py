from django.urls import path
from . import views

urlpatterns = [
    path('projects/<uuid:project_id>/parsed/', views.receive_parsed_data, name='internal-parsed'),
    path('projects/<uuid:project_id>/ai-docs/', views.receive_ai_docs, name='internal-ai-docs'),
]
