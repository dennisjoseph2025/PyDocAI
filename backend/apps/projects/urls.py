from django.urls import path

from .views import ProjectDetailView, ProjectListView

urlpatterns = [
    path('', ProjectListView.as_view(), name='project_list'),
    path('<uuid:id>/', ProjectDetailView.as_view(), name='project_detail'),
]
