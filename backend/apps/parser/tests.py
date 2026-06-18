from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.parser.ast_parser import parse_python_file
from apps.parser.validators import should_exclude, validate_python_code
from apps.projects.models import Project

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


class ParserTaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='tasktest@test.com', name='TaskTest', password='pwd')

    @patch('apps.parser.tasks._call_fastapi')
    def test_parse_and_generate_docs_task_success(self, mock_fastapi):
        """Test the celery task completes successfully for a single file."""
        from apps.parser.tasks import parse_and_generate_docs_task
        mock_fastapi.return_value = {"status": "done"}
        project = Project.objects.create(
            user=self.user, name='TestPy',
            source_type=Project.SourceType.FILE,
            status=Project.Status.PENDING,
        )
        result = parse_and_generate_docs_task(project.id, 'print("hello")', 'test.py', 14)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.DONE)
        self.assertEqual(result['project_id'], str(project.id))

    @patch('apps.parser.tasks._call_fastapi')
    def test_parse_task_sets_failed_on_fastapi_error(self, mock_fastapi):
        """Test the task sets failed status when FastAPI returns failure."""
        from apps.parser.tasks import parse_and_generate_docs_task
        mock_fastapi.return_value = {"status": "failed", "error_message": "AI error"}
        project = Project.objects.create(
            user=self.user, name='FailPy',
            source_type=Project.SourceType.FILE,
            status=Project.Status.PENDING,
        )
        parse_and_generate_docs_task(project.id, 'bad code', 'bad.py', 8)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.FAILED)

    @patch('apps.parser.tasks._call_fastapi')
    def test_parse_folder_task_creates_files(self, mock_fastapi):
        """Test parse_folder_task sends files to FastAPI and updates project."""
        import base64
        import io
        import zipfile

        from apps.parser.tasks import parse_folder_task
        mock_fastapi.return_value = {"status": "done"}
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('app/models.py', 'class Foo: pass\n')
            zf.writestr('app/views.py', 'def bar(): pass\n')
        zip_b64 = base64.b64encode(zip_buffer.getvalue()).decode()
        project = Project.objects.create(
            user=self.user, name='FolderProj',
            source_type=Project.SourceType.FOLDER,
            status=Project.Status.PENDING,
        )
        result = parse_folder_task(project.id, ['app/models.py', 'app/views.py'], zip_b64)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.DONE)
        self.assertEqual(result['files_parsed'], 2)

    def test_parse_folder_task_no_zip_returns_error(self):
        from apps.parser.tasks import parse_folder_task
        project = Project.objects.create(
            user=self.user, name='NoZip',
            source_type=Project.SourceType.FOLDER,
            status=Project.Status.PENDING,
        )
        result = parse_folder_task(project.id, ['main.py'], zip_base64=None)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.FAILED)
        self.assertIn('error', result)
