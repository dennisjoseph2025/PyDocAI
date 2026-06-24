from django.urls import path

from .views import (
    AdminFeedbackResolveView,
    AdminFeedbackView,
    FeedbackCreateView,
    FeedbackListView,
    FeedbackReplyListCreateView,
)

urlpatterns = [
    path('',                   FeedbackCreateView.as_view(),          name='feedback-create'),
    path('my/',                FeedbackListView.as_view(),            name='feedback-my'),
    path('admin/',             AdminFeedbackView.as_view(),           name='feedback-admin'),
    path('admin/<uuid:pk>/resolve/', AdminFeedbackResolveView.as_view(), name='feedback-resolve'),
    path('<uuid:feedback_pk>/replies/', FeedbackReplyListCreateView.as_view(), name='feedback-replies'),
]
