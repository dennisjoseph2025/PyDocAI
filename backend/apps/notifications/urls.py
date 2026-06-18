from django.urls import path

from .views import ClearAllNotificationsView, MarkAllReadView, MarkReadView, NotificationDeleteView, NotificationListView, UnreadCountView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('unread-count/', UnreadCountView.as_view(), name='notification_unread_count'),
    path('<uuid:pk>/read/', MarkReadView.as_view(), name='notification_mark_read'),
    path('read-all/', MarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('<uuid:pk>/', NotificationDeleteView.as_view(), name='notification_delete'),
    path('clear-all/', ClearAllNotificationsView.as_view(), name='notification_clear_all'),
]
