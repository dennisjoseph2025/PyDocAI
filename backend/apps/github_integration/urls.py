from django.urls import path
from .views import UserReposView, RepoFoldersView, ImportRepoView

urlpatterns = [
    path('repos/',         UserReposView.as_view(),   name='github-repos'),
    path('repos/folders/', RepoFoldersView.as_view(), name='github-repo-folders'),
    path('repos/import/',  ImportRepoView.as_view(),  name='github-repo-import'),
]