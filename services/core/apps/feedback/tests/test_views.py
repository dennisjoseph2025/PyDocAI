import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestFeedbackCreateView:
    def test_unauthenticated(self, api_client):
        url = reverse('feedback-create')
        response = api_client.post(url, {'message': 'Great app!', 'category': 'general'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_feedback(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('feedback-create')
        response = api_client.post(url, {'message': 'Awesome!', 'category': 'general'})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['message'] == 'Awesome!'

    def test_invalid_data(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('feedback-create')
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestFeedbackListView:
    def test_unauthenticated(self, api_client):
        url = reverse('feedback-my')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_own_feedback(self, api_client, user, feedback):
        api_client.force_authenticate(user=user)
        url = reverse('feedback-my')
        response = api_client.get(url)
        assert len(response.data) == 1
        assert response.data[0]['message'] == feedback.message

    def test_does_not_return_others_feedback(self, api_client, other_user, feedback):
        api_client.force_authenticate(user=other_user)
        url = reverse('feedback-my')
        response = api_client.get(url)
        assert response.data == []

    def test_filter_by_category(self, api_client, user):
        from apps.feedback.models import Feedback
        Feedback.objects.create(user=user, category='bug', message='Bug!')
        Feedback.objects.create(user=user, category='feature', message='Feature!')
        api_client.force_authenticate(user=user)
        url = reverse('feedback-my') + '?category=bug'
        response = api_client.get(url)
        assert len(response.data) == 1
        assert response.data[0]['category'] == 'bug'


class TestAdminFeedbackView:
    def test_non_admin_gets_empty_list(self, api_client, user, feedback):
        api_client.force_authenticate(user=user)
        url = reverse('feedback-admin')
        response = api_client.get(url)
        assert response.data == []

    def test_admin_views_all(self, api_client, admin_user, feedback):
        api_client.force_authenticate(user=admin_user)
        url = reverse('feedback-admin')
        response = api_client.get(url)
        assert len(response.data) >= 1


class TestAdminFeedbackResolveView:
    def test_resolve(self, api_client, admin_user, feedback):
        api_client.force_authenticate(user=admin_user)
        url = reverse('feedback-resolve', args=[feedback.id])
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_resolved'] is True

    def test_non_admin_cannot_resolve(self, api_client, user, feedback):
        api_client.force_authenticate(user=user)
        url = reverse('feedback-resolve', args=[feedback.id])
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestFeedbackReplyListCreateView:
    def test_get_replies(self, api_client, user, feedback):
        feedback.replies.create(user=user, message='Reply 1')
        api_client.force_authenticate(user=user)
        url = reverse('feedback-replies', args=[feedback.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_reply(self, api_client, user, feedback):
        api_client.force_authenticate(user=user)
        url = reverse('feedback-replies', args=[feedback.id])
        response = api_client.post(url, {'message': 'Thanks!'})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['message'] == 'Thanks!'
