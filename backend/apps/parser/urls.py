from django.urls import path
from .views import AnalyseSingleFileView, AnalyseFolderView

urlpatterns = [
    path('file/',   AnalyseSingleFileView.as_view(), name='analyse_file'),
    path('folder/', AnalyseFolderView.as_view(),     name='analyse_folder'),
]