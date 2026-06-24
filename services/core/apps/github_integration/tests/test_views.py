from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status


pytestmark = pytest.mark.django_db


class TestUserReposView:
    def test_unauthenticated(self, api_client):
        url = reverse('github-repos')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_token(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('github-repos')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'GitHub account not connected' in response.data['detail']

    def test_with_token(self, api_client, user):
        user.github_token = 'test-token'
        user.save()
        api_client.force_authenticate(user=user)
        with patch('apps.github_integration.views.user.get_user_repos', return_value=[{'id': 1, 'name': 'repo1'}]):
            url = reverse('github-repos')
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert response.data[0]['name'] == 'repo1'

    def test_github_error(self, api_client, user):
        user.github_token = 'bad-token'
        user.save()
        api_client.force_authenticate(user=user)
        with patch('apps.github_integration.views.user.get_user_repos', side_effect=Exception('API error')):
            url = reverse('github-repos')
            response = api_client.get(url)
            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRepoFoldersView:
    def test_missing_repo_param(self, api_client, user):
        user.github_token = 'token'
        user.save()
        api_client.force_authenticate(user=user)
        url = reverse('github-repo-folders')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_folders(self, api_client, user):
        user.github_token = 'token'
        user.save()
        api_client.force_authenticate(user=user)
        with patch('apps.github_integration.views.user.get_repo_folders', return_value=[{'path': '/', 'type': 'tree'}]):
            url = reverse('github-repo-folders') + '?repo=owner/repo'
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK


class TestImportRepoView:
    def test_import(self, api_client, user):
        user.github_token = 'token'
        user.save()
        api_client.force_authenticate(user=user)
        with patch('apps.github_integration.views.user.import_github_repo_task.delay'):
            url = reverse('github-repo-import')
            response = api_client.post(url, {'full_name': 'owner/repo', 'name': 'My Repo'}, format='json')
            assert response.status_code == status.HTTP_202_ACCEPTED
            assert 'project_id' in response.data


class TestParseGithubUrl:
    def test_valid_url(self):
        from apps.github_integration.views.user import parse_github_url
        result = parse_github_url('https://github.com/owner/repo')
        assert result == 'owner/repo'

    def test_valid_url_with_git(self):
        from apps.github_integration.views.user import parse_github_url
        result = parse_github_url('https://github.com/owner/repo.git')
        assert result == 'owner/repo'

    def test_invalid_url(self):
        from apps.github_integration.views.user import parse_github_url
        result = parse_github_url('https://example.com/not-github')
        assert result is None

    def test_empty_url(self):
        from apps.github_integration.views.user import parse_github_url
        result = parse_github_url('')
        assert result is None


class TestPublicRepoInfoView:
    def test_with_url(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('apps.github_integration.views.public.get_public_repo', return_value={'id': 1, 'name': 'repo'}):
            url = reverse('github-public-repo-info') + '?url=https://github.com/owner/repo'
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK

    def test_with_full_name(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('apps.github_integration.views.public.get_public_repo', return_value={'id': 1, 'name': 'repo'}):
            url = reverse('github-public-repo-info') + '?full_name=owner/repo'
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK


class TestImportPublicRepoView:
    def test_import(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('apps.github_integration.views.public.import_public_repo_task.delay'):
            url = reverse('github-public-repo-import')
            response = api_client.post(url, {'full_name': 'owner/repo'}, format='json')
            assert response.status_code == status.HTTP_202_ACCEPTED
