from django.urls import path

from .views import (
    AdminProjectDetailView,
    AdminProjectListView,
    AdminStatsView,
    AdminUserBlockView,
    AdminUserDeleteView,
    AdminUserDetailView,
    AdminUserListView,
    AdminUserProjectsView,
)

urlpatterns = [
    path('stats/',                  AdminStatsView.as_view(),           name='admin-stats'),
    path('users/',                  AdminUserListView.as_view(),         name='admin-user-list'),
    path('users/<uuid:pk>/',          AdminUserDetailView.as_view(),      name='admin-user-detail'),
    path('users/<uuid:pk>/publish/',   AdminUserProjectsView.as_view(),   name='admin-user-projects'),
    path('users/<uuid:pk>/delete/',    AdminUserDeleteView.as_view(),     name='admin-user-delete'),
    path('users/<uuid:pk>/block/',     AdminUserBlockView.as_view(),      name='admin-user-block'),
    path('projects/',               AdminProjectListView.as_view(),      name='admin-project-list'),
    path('projects/<uuid:pk>/',     AdminProjectDetailView.as_view(),    name='admin-project-detail'),
]
