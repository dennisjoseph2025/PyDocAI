from django.urls import path

from .views import CommentCreateView, CommentDeleteView, CommentListView

urlpatterns = [
    path('<uuid:project_id>/comments/', CommentListView.as_view(), name='comment_list'),
    path('<uuid:project_id>/comments/create/', CommentCreateView.as_view(), name='comment_create'),
    path('comments/<uuid:pk>/', CommentDeleteView.as_view(), name='comment_delete'),
]
