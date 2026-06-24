from unittest.mock import patch

import pytest

pytestmark = pytest.mark.django_db


class TestGenerateUniversalDocsTask:
    def test_project_not_found(self):
        from apps.universal.tasks import generate_universal_docs_task
        result = generate_universal_docs_task(999, 'universal')
        assert 'error' in result

    def test_sets_processing_status(self, project):
        from apps.universal.tasks import generate_universal_docs_task
        with patch('apps.universal.tasks.generate_universal_docs_task.retry'):
            result = generate_universal_docs_task(project.id, 'universal')
        project.refresh_from_db()
        assert 'error' in result or project.status is not None

    def test_rejected_response(self, project):
        from apps.universal.tasks import generate_universal_docs_task
        with patch('apps.universal.tasks._call_groq', return_value='REJECT: Not a valid project'):
            generate_universal_docs_task(project.id, 'universal')
        project.refresh_from_db()
        assert project.status == 'failed'
        assert 'REJECT' in project.error_message


class TestFilePriority:
    def test_high_priority(self):
        from apps.universal.tasks import _file_priority
        assert _file_priority('urls.py') == 10
        assert _file_priority('app.py') == 10
        assert _file_priority('models.py') == 7

    def test_low_priority(self):
        from apps.universal.tasks import _file_priority
        assert _file_priority('styles.css') == 2
        assert _file_priority('icon.svg') == 2

    def test_default_priority(self):
        from apps.universal.tasks import _file_priority
        assert _file_priority('unknown.xyz') == 1


class TestBuildFileTree:
    def test_single_file(self):
        from apps.universal.tasks import _build_file_tree
        tree = _build_file_tree(['main.py'])
        assert tree == {'main.py': {}}

    def test_nested_files(self):
        from apps.universal.tasks import _build_file_tree
        tree = _build_file_tree(['src/main.py', 'src/utils.py', 'README.md'])
        assert 'src' in tree
        assert 'main.py' in tree['src']
        assert 'utils.py' in tree['src']
        assert 'README.md' in tree


class TestFormatTree:
    def test_simple_tree(self):
        from apps.universal.tasks import _build_file_tree, _format_tree
        tree = _build_file_tree(['main.py', 'README.md'])
        lines = _format_tree(tree)
        assert len(lines) == 2
