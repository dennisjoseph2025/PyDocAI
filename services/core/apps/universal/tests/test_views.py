import io
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestUniversalUploadView:
    def test_unauthenticated(self, api_client):
        url = reverse('universal-upload')
        response = api_client.post(url, {'name': 'Test'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_name(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('universal-upload')
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_mode(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('universal-upload')
        response = api_client.post(url, {'name': 'Test', 'mode': 'invalid'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_file(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('apps.universal.views.upload.generate_universal_docs_task.delay'):
            url = reverse('universal-upload')
            f = io.BytesIO(b'print("hello")')
            f.name = 'test.py'
            response = api_client.post(url, {'name': 'Test', 'file': f})
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_source_code(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('apps.universal.views.upload.generate_universal_docs_task.delay'):
            url = reverse('universal-upload')
            response = api_client.post(url, {'name': 'Test', 'source_code': 'print("hello")'})
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_no_input(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('universal-upload')
        response = api_client.post(url, {'name': 'Test'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUniversalStatusView:
    def test_unauthenticated(self, api_client):
        url = reverse('universal-status', args=['00000000-0000-0000-0000-000000000000'])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_own_project(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        url = reverse('universal-status', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == project.status
        assert response.data['name'] == project.name

    def test_not_own_project(self, api_client, other_user, project):
        api_client.force_authenticate(user=other_user)
        url = reverse('universal-status', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
