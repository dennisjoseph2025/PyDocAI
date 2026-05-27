from django.urls import path
from .views import (
    AdminStatsView, AdminProjectDetailView, AdminUserDetailView,
    AdminProjectListView, AdminUserListView,
)

urlpatterns = [
    path('stats/',              AdminStatsView.as_view(),         name='admin-stats'),
    path('users/',              AdminUserListView.as_view(),       name='admin-user-list'),
    path('users/<uuid:pk>/',    AdminUserDetailView.as_view(),     name='admin-user-detail'),
    path('projects/',           AdminProjectListView.as_view(),    name='admin-project-list'),
    path('projects/<uuid:pk>/', AdminProjectDetailView.as_view(),  name='admin-project-detail'),
]