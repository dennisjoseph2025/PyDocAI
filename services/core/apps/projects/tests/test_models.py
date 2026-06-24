
from apps.projects.models import Project, ProjectFile


class TestProjectModel:
    def test_create(self, user):
        project = Project.objects.create(
            user=user,
            name='Test Project',
            source_type=Project.SourceType.FILE,
        )
        assert project.user == user
        assert project.name == 'Test Project'
        assert project.status == 'pending'
        assert project.is_published is False
        assert project.public_slug is not None

    def test_status_choices(self):
        assert Project.Status.PENDING == 'pending'
        assert Project.Status.PROCESSING == 'processing'
        assert Project.Status.DONE == 'done'
        assert Project.Status.FAILED == 'failed'

    def test_source_type_choices(self):
        assert Project.SourceType.FILE == 'file'
        assert Project.SourceType.FOLDER == 'folder'
        assert Project.SourceType.GITHUB == 'github'

    def test_str(self, project):
        expected = f'{project.name} ({project.source_type}) — {project.user.email}'
        assert str(project) == expected

    def test_ordering(self):
        assert Project._meta.ordering == ['-created_at']

    def test_db_table(self):
        assert Project._meta.db_table == 'projects'


class TestProjectFileModel:
    def test_create(self, project):
        pf = ProjectFile.objects.create(
            project=project,
            file_name='main.py',
            file_path='src/main.py',
            content='print("hello")',
        )
        assert pf.project == project
        assert pf.file_name == 'main.py'
        assert pf.file_path == 'src/main.py'
        assert pf.content == 'print("hello")'

    def test_str(self, project_file):
        assert project_file.file_name in str(project_file)

    def test_db_table(self):
        assert ProjectFile._meta.db_table == 'project_files'
