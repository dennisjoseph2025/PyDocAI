import pytest

from apps.exports.generators import export_project_as_markdown

pytestmark = pytest.mark.django_db


class TestExportProjectAsMarkdown:
    def test_project_with_readme(self, project):
        project.readme_docs = '# Project README'
        project.save()
        result = export_project_as_markdown(str(project.id))
        assert '# Project README' in result
        assert project.name in result

    def test_project_with_summary(self, project):
        project.project_info = {'summary': 'Project summary'}
        project.save()
        result = export_project_as_markdown(str(project.id))
        assert 'Project summary' in result

    def test_project_with_info_json(self, project):
        project.project_info = {'key': 'value'}
        project.save()
        result = export_project_as_markdown(str(project.id))
        assert 'key' in result
        assert 'value' in result

    def test_fallback_to_per_file_docs(self, project, project_file):
        project_file.generated_docs = '## Function docs'
        project_file.save()
        result = export_project_as_markdown(str(project.id))
        assert project_file.file_path in result
        assert 'Function docs' in result

    def test_no_files(self, project):
        result = export_project_as_markdown(str(project.id))
        assert '_No files found for this project._' in result

    def test_project_with_parsed_no_docs(self, project, project_file):
        project_file.parsed_data = {'functions': ['foo']}
        project_file.generated_docs = None
        project_file.save()
        result = export_project_as_markdown(str(project.id))
        assert 'parsed_data present: True' in result
