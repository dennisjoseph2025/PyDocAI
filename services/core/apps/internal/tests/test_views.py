from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


INTERNAL_KEY = 'test-internal-key'


@pytest.fixture(autouse=True)
def internal_key():
    with patch('apps.internal.views.receive.INTERNAL_API_KEY', INTERNAL_KEY):
        yield


def _auth_header():
    return {'HTTP_X_INTERNAL_API_KEY': INTERNAL_KEY}


class TestProjectDetail:
    def test_get_project(self, api_client, project):
        url = reverse('internal-project', args=[project.id])
        response = api_client.get(url, **_auth_header())
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(project.id)
        assert response.data['name'] == project.name

    def test_get_not_found(self, api_client):
        url = reverse('internal-project', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url, **_auth_header())
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_project(self, api_client, project):
        url = reverse('internal-project', args=[project.id])
        response = api_client.patch(url, {'name': 'Updated'}, format='json', **_auth_header())
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated'

    def test_forbidden_without_key(self, api_client, project):
        url = reverse('internal-project', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_forbidden_with_wrong_key(self, api_client, project):
        url = reverse('internal-project', args=[project.id])
        response = api_client.get(url, HTTP_X_INTERNAL_API_KEY='wrong-key')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProjectFileList:
    def test_get_files(self, api_client, project, project_file):
        url = reverse('internal-project-files', args=[project.id])
        response = api_client.get(url, **_auth_header())
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['file_name'] == project_file.file_name

    def test_get_empty_file_list(self, api_client, project):
        url = reverse('internal-project-files', args=[project.id])
        response = api_client.get(url, **_auth_header())
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_post_file(self, api_client, project):
        url = reverse('internal-project-files', args=[project.id])
        data = {'file_name': 'test.py', 'file_path': 'src/test.py', 'content': 'print("hello")'}
        response = api_client.post(url, data, format='json', **_auth_header())
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['file_name'] == 'test.py'

    def test_forbidden_without_key(self, api_client, project):
        url = reverse('internal-project-files', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestReceiveParsedData:
    def test_receive_parsed_data(self, api_client, project):
        url = reverse('internal-parsed', args=[project.id])
        data = {'parsed_data': {'functions': ['foo']}, 'file_count': 5}
        response = api_client.post(url, data, format='json', **_auth_header())
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ok'
        project.refresh_from_db()
        assert project.parsed_data == {'functions': ['foo']}
        assert project.project_info['files_parsed'] == 5
        assert project.status == 'processing'

    def test_receive_with_parsed_key(self, api_client, project):
        url = reverse('internal-parsed', args=[project.id])
        data = {'parsed': {'classes': ['Bar']}, 'file_count': 3}
        response = api_client.post(url, data, format='json', **_auth_header())
        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.parsed_data == {'classes': ['Bar']}

    def test_project_not_found(self, api_client):
        url = reverse('internal-parsed', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.post(url, {}, format='json', **_auth_header())
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestReceiveAIDocs:
    def test_receive_docs_done(self, api_client, project):
        url = reverse('internal-ai-docs', args=[project.id])
        data = {
            'generated_docs': '# Docs',
            'readme_docs': '# README',
            'api_docs': '# API',
            'project_info': {'summary': 'A project'},
            'status': 'done',
        }
        response = api_client.post(url, data, format='json', **_auth_header())
        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.generated_docs == '# Docs'
        assert project.readme_docs == '# README'
        assert project.api_docs == '# API'
        assert project.status == 'done'

    def test_receive_docs_failed(self, api_client, project):
        url = reverse('internal-ai-docs', args=[project.id])
        data = {'status': 'failed', 'error_message': 'AI error'}
        response = api_client.post(url, data, format='json', **_auth_header())
        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.status == 'failed'
        assert project.error_message == 'AI error'

    def test_project_not_found(self, api_client):
        url = reverse('internal-ai-docs', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.post(url, {}, format='json', **_auth_header())
        assert response.status_code == status.HTTP_404_NOT_FOUND
