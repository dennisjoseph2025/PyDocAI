from django.urls import path
from .views import AIStatusView

urlpatterns = [
    path('status/', AIStatusView.as_view(), name='ai-status'),
]
