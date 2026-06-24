import pytest

pytestmark = pytest.mark.django_db


class TestParseFolderTask:
    def test_missing_zip(self, project):
        from apps.parser.tasks import parse_folder_task
        result = parse_folder_task(project.id, ['main.py'], zip_base64=None)
        assert result['error'] == 'No ZIP data provided'
        project.refresh_from_db()
        assert project.status == 'failed'


class TestParseAndGenerateDocsTask:
    def test_project_not_found(self):
        from apps.parser.tasks import parse_and_generate_docs_task
        result = parse_and_generate_docs_task(999, 'print("x")', 'test.py', 10)
        assert 'error' in result
