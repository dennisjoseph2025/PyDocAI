from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status


pytestmark = pytest.mark.django_db


class TestAIStatusView:
    def test_unauthenticated(self, api_client):
        url = reverse('ai-status')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_keys_configured(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('django.conf.settings.GROQ_API_KEY', None):
            with patch('django.conf.settings.GROQ_API_KEY_2', None):
                url = reverse('ai-status')
                response = api_client.get(url)
                assert response.status_code == status.HTTP_200_OK
                assert response.data['providers']['groq_primary']['configured'] is False
                assert response.data['providers']['groq_fallback']['configured'] is False

    def test_primary_key_configured(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('django.conf.settings.GROQ_API_KEY', 'test-key-1'):
            with patch('django.conf.settings.GROQ_API_KEY_2', None):
                url = reverse('ai-status')
                response = api_client.get(url)
                assert response.data['providers']['groq_primary']['configured'] is True
                assert response.data['providers']['groq_fallback']['configured'] is False

    def test_both_keys_configured(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('django.conf.settings.GROQ_API_KEY', 'test-key-1'):
            with patch('django.conf.settings.GROQ_API_KEY_2', 'test-key-2'):
                url = reverse('ai-status')
                response = api_client.get(url)
                assert response.data['providers']['groq_primary']['configured'] is True
                assert response.data['providers']['groq_fallback']['configured'] is True

    @patch('groq.Groq')
    def test_primary_active(self, mock_groq, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('django.conf.settings.GROQ_API_KEY', 'test-key-1'):
            with patch('django.conf.settings.GROQ_API_KEY_2', None):
                url = reverse('ai-status')
                response = api_client.get(url)
                assert response.data['providers']['groq_primary']['status'] == 'active'

    @patch('groq.Groq')
    def test_primary_invalid(self, mock_groq, api_client, user):
        mock_groq.side_effect = Exception('Invalid API key')
        api_client.force_authenticate(user=user)
        with patch('django.conf.settings.GROQ_API_KEY', 'bad-key'):
            with patch('django.conf.settings.GROQ_API_KEY_2', None):
                url = reverse('ai-status')
                response = api_client.get(url)
                assert response.data['providers']['groq_primary']['status'] == 'invalid'

    def test_response_structure(self, api_client, user):
        api_client.force_authenticate(user=user)
        with patch('django.conf.settings.GROQ_API_KEY', None):
            with patch('django.conf.settings.GROQ_API_KEY_2', None):
                url = reverse('ai-status')
                response = api_client.get(url)
                assert 'providers' in response.data
                assert 'fallback_order' in response.data
                assert response.data['fallback_order'] == ['groq_primary', 'groq_fallback']
