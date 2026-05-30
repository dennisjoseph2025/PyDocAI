from django.urls import path

from .views import (
    ImportPublicRepoView,
    ImportRepoView,
    PublicRepoFoldersView,
    PublicRepoInfoView,
    RepoFoldersView,
    UserReposView,
)

urlpatterns = [
    path('repos/',              UserReposView.as_view(),        name='github-repos'),
    path('repos/folders/',      RepoFoldersView.as_view(),      name='github-repo-folders'),
    path('repos/import/',       ImportRepoView.as_view(),       name='github-repo-import'),
    path('public-repo/info/',   PublicRepoInfoView.as_view(),   name='github-public-repo-info'),
    path('public-repo/folders/', PublicRepoFoldersView.as_view(), name='github-public-repo-folders'),
    path('public-repo/import/', ImportPublicRepoView.as_view(), name='github-public-repo-import'),
]
