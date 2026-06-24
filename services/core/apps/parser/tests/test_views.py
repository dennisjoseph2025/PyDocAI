import io
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status


pytestmark = pytest.mark.django_db


class TestAnalyseSingleFileView:
    def test_unauthenticated(self, api_client):
        url = reverse('analyse_file')
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_file(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('analyse_file')
        response = api_client.post(url, {'name': 'Test'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_py_file(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('analyse_file')
        f = io.BytesIO(b'print("hello")')
        f.name = 'test.js'
        response = api_client.post(url, {'file': f, 'name': 'Test'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_file(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('apps.parser.views.file.parse_and_generate_docs_task.delay'):
            url = reverse('analyse_file')
            f = io.BytesIO(b'print("hello")')
            f.name = 'test.py'
            response = api_client.post(url, {'file': f, 'name': 'Test'})
            assert response.status_code == status.HTTP_202_ACCEPTED
            assert 'project_id' in response.data

    def test_non_utf8(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('analyse_file')
        f = io.BytesIO(b'\xff\xfe\x00\x01')
        f.name = 'test.py'
        response = api_client.post(url, {'file': f, 'name': 'Test'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAnalyseFolderView:
    def test_unauthenticated(self, api_client):
        url = reverse('analyse_folder')
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_zip(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('analyse_folder')
        response = api_client.post(url, {'name': 'Test', 'custom_info': '{}'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_no_custom_info(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('analyse_folder')
        response = api_client.post(url, {'name': 'Test'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_zip(self, api_client, user):
        import zipfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        api_client.force_authenticate(user=user)
        with patch('apps.parser.views.folder.parse_folder_task.delay'):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as zf:
                zf.writestr('main.py', 'print("hello")')
            buf.seek(0)
            uploaded = SimpleUploadedFile('test.zip', buf.read(), content_type='application/zip')
            url = reverse('analyse_folder')
            response = api_client.post(url, {
                'folder': uploaded,
                'name': 'Test',
                'custom_info': '{"details": "test"}',
            })
            assert response.status_code == status.HTTP_202_ACCEPTED
            assert 'project_id' in response.data

    def test_invalid_zip(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('analyse_folder')
        f = io.BytesIO(b'not a zip file')
        f.name = 'test.zip'
        response = api_client.post(url, {
            'folder': f,
            'name': 'Test',
            'custom_info': '{"details": "test"}',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_no_py_files_in_zip(self, api_client, user):
        import zipfile
        api_client.force_authenticate(user=user)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('readme.txt', 'Hello')
        buf.seek(0)
        url = reverse('analyse_folder')
        response = api_client.post(url, {
            'folder': buf,
            'name': 'Test',
            'custom_info': '{"details": "test"}',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
