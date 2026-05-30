from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.parser.ast_parser import parse_python_file
from apps.parser.validators import should_exclude, validate_python_code

User = get_user_model()

class ParserLogicTests(APITestCase):
    def test_python_code_validator(self):
        """Test syntax validation logic."""
        valid, err = validate_python_code("def foo():\n    pass\n")
        self.assertTrue(valid)
        self.assertIsNone(err)

        valid, err = validate_python_code("def foo() pass")
        self.assertFalse(valid)
        self.assertIn("SyntaxError", err)

    def test_should_exclude_logic(self):
        """Test exclusion of virtual environments and cache directories."""
        self.assertTrue(should_exclude("venv/lib/site-packages/django/models.py"))
        self.assertTrue(should_exclude("__pycache__/views.py"))
        self.assertFalse(should_exclude("apps/core/models.py"))

    def test_ast_parser_function_extraction(self):
        """Test that the AST parser accurately identifies functions and args."""
        code = "def add(x, y):\n    return x + y"
        parsed = parse_python_file(code)
        self.assertFalse(parsed['error'])
        self.assertEqual(len(parsed['functions']), 1)
        self.assertEqual(parsed['functions'][0]['name'], 'add')
        self.assertEqual(parsed['functions'][0]['args'][0]['name'], 'x')

class ParserAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='parser@test.com', name='Parser', password='pwd')
        self.client.force_authenticate(user=self.user)

    @patch('apps.parser.tasks.parse_and_generate_docs_task.delay')
    def test_single_file_upload(self, mock_task):
        """Test uploading a single python file triggers the correct celery task."""
        file_content = b"def my_func(): pass"
        test_file = SimpleUploadedFile("test.py", file_content, content_type="text/x-python")

        response = self.client.post('/api/parser/file/', {
            'file': test_file,
            'name': 'Test Script'
        })
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('project_id', response.data)
        mock_task.assert_called_once()
