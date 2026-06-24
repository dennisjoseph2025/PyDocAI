from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestExportProjectMarkdownView:
    def test_export_success(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        with patch('apps.exports.views.markdown.export_project_as_markdown', return_value='# Docs'):
            url = reverse('export-markdown', args=[project.id])
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert response.content.decode() == '# Docs'
            assert response['Content-Type'] == 'text/markdown'
            assert 'attachment' in response['Content-Disposition']

    def test_export_failure(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        with patch('apps.exports.views.markdown.export_project_as_markdown', side_effect=Exception('Error')):
            url = reverse('export-markdown', args=[project.id])
            response = api_client.get(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestExportFolderDocsView:
    def test_export_all(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        project.readme_docs = '# README'
        project.generated_docs = '# Summary'
        project.api_docs = '# API'
        project.save()
        url = reverse('export-folder', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        content = response.content.decode()
        assert '# README' in content
        assert '# Project Documentation' in content
        assert '# API Documentation' in content

    def test_export_readme_only(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        project.readme_docs = '# README'
        project.save()
        url = reverse('export-folder', args=[project.id]) + '?type=readme'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.content.decode() == '# README'

    def test_export_readme_not_found(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('export-folder', args=[project.id]) + '?type=readme'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_project_not_found(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('export-folder', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_none_available(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('export-folder', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
