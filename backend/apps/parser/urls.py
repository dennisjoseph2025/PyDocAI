from django.urls import path

from .views import AnalyseFolderView, AnalyseSingleFileView

urlpatterns = [
    path('file/',   AnalyseSingleFileView.as_view(), name='analyse_file'),
    path('folder/', AnalyseFolderView.as_view(),     name='analyse_folder'),
]
