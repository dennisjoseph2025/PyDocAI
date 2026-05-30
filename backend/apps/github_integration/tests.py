from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.github_integration.views import parse_github_url

User = get_user_model()

class GithubUtilsTests(TestCase):
    def test_parse_github_url(self):
        """Ensure standard GitHub URLs extract the 'owner/repo' format."""
        self.assertEqual(parse_github_url("https://github.com/django/django"), "django/django")
        self.assertEqual(parse_github_url("https://github.com/astral-sh/uv.git"), "astral-sh/uv")
        self.assertEqual(parse_github_url("https://github.com/owner/repo/"), "owner/repo")
        self.assertIsNone(parse_github_url("invalid_url"))

class GithubAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='git@test.com', name='Git', password='pwd')
        self.client.force_authenticate(user=self.user)

    @patch('apps.github_integration.tasks.import_public_repo_task.delay')
    def test_import_public_repo(self, mock_task):
        """Test importing a public repo triggers the background task."""
        response = self.client.post('/api/github/public-repo/import/', {
            'url': 'https://github.com/pallets/flask',
            'name': 'Flask Docs'
        })
        self.assertEqual(response.status_code, 202)
        self.assertIn('project_id', response.data)
        mock_task.assert_called_once()
