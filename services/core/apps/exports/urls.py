from django.urls import path

from apps.exports.views import ExportFolderDocsView, ExportProjectMarkdownView

urlpatterns = [
    path('<uuid:project_id>/markdown/', ExportProjectMarkdownView.as_view(), name='export-markdown'),
    path('<uuid:project_id>/folder/', ExportFolderDocsView.as_view(), name='export-folder'),
]
