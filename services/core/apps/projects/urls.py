from django.urls import path

from .views import (
    ProjectDetailView,
    ProjectListView,
    PublicProjectDetailView,
    PublicProjectListView,
    PublishProjectView,
)

urlpatterns = [
    path('', ProjectListView.as_view(), name='project_list'),
    path('<uuid:id>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<uuid:pk>/publish/', PublishProjectView.as_view(), name='project_publish'),
]

public_urlpatterns = [
    path('', PublicProjectListView.as_view(), name='public_project_list'),
    path('<uuid:slug>/', PublicProjectDetailView.as_view(), name='public_project_detail'),
]
