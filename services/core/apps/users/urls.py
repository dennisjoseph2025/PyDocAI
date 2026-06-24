from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    GithubAuthView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    UserListView,
)

urlpatterns = [
    path('register/',              RegisterView.as_view(),             name='register'),
    path('login/',                 LoginView.as_view(),                name='login'),
    path('logout/',                LogoutView.as_view(),               name='logout'),
    path('token/refresh/',         TokenRefreshView.as_view(),         name='token_refresh'),
    path('profile/',               ProfileView.as_view(),              name='profile'),
    path('change-password/',       ChangePasswordView.as_view(),       name='change_password'),
    path('list/',                  UserListView.as_view(),             name='user_list'),
    path('auth/github/',           GithubAuthView.as_view(),           name='github-auth'),
    path('password-reset/',        PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/',PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
