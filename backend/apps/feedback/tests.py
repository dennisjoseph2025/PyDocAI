from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.feedback.models import Feedback

User = get_user_model()

class FeedbackAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='fb@test.com', name='FB', password='pwd')
        self.client.force_authenticate(user=self.user)

    @patch('apps.feedback.tasks.send_feedback_confirmation_task.delay')
    def test_submit_feedback(self, mock_email_task):
        """Test users can submit feedback and it triggers an email task."""
        response = self.client.post('/api/feedback/', {
            'category': 'bug',
            'message': 'The parser broke on my nested dictionary.'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Feedback.objects.count(), 1)
        mock_email_task.assert_called_once()

    def test_list_my_feedback(self):
        """Test users can view their feedback history."""
        Feedback.objects.create(user=self.user, category='ui_ux', message='Looks good')
        response = self.client.get('/api/feedback/my/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['message'], 'Looks good')
