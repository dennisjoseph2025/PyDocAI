from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.projects.models import Project

User = get_user_model()

class ExportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='export@test.com', name='Exp', password='pwd')
        self.project = Project.objects.create(
            user=self.user,
            name="Test Export Project",
            readme_docs="# Mock README",
            generated_docs="## Project Summary",
            api_docs="### API Reference"
        )
        self.client.force_authenticate(user=self.user)

    def test_export_project_as_markdown(self):
        """Test that the export API combines the document segments into a Markdown file download."""
        response = self.client.get(f'/api/exports/{self.project.id}/folder/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/markdown')

        content = response.content.decode('utf-8')
        self.assertIn('# Mock README', content)
        self.assertIn('## Project Summary', content)
        self.assertIn('### API Reference', content)
