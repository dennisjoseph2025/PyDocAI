from django.test import TestCase
from apps.ai.generator import _sanitize_markdown
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AILogicTests(TestCase):
    def test_markdown_sanitization(self):
        """Test that AI artifacts are stripped and code blocks are fixed."""
        dirty_markdown = "code\nCopy\n```python\ndef test(): pass\n```"
        clean = _sanitize_markdown(dirty_markdown)
        self.assertNotIn("Copy", clean)
        self.assertIn("```python", clean)

    def test_mermaid_diagram_formatting(self):
        """Ensure mermaid boundaries are injected if missing."""
        dirty = "mermaid\ngraph TD\nA-->B"
        clean = _sanitize_markdown(dirty)
        self.assertIn("```mermaid\ngraph TD\nA-->B\n```", clean)

class AIApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='ai@test.com', name='AI', password='pwd')
        self.client.force_authenticate(user=self.user)

    def test_ai_status_endpoint(self):
        """Test the AI status endpoint returns the configured provider layout."""
        response = self.client.get('/api/ai/status/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('providers', response.data)
        self.assertIn('groq_primary', response.data['providers'])