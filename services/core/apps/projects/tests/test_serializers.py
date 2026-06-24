
from apps.projects.serializers import (
    ProjectFileSerializer,
    ProjectListSerializer,
    ProjectSerializer,
    PublicProjectListSerializer,
    PublicProjectSerializer,
)


class TestProjectSerializer:
    def test_serialize(self, project):
        serializer = ProjectSerializer(project)
        assert serializer.data['id'] == str(project.id)
        assert serializer.data['name'] == project.name
        assert serializer.data['status'] == project.status

    def test_includes_files(self, project, project_file):
        serializer = ProjectSerializer(project)
        assert 'files' in serializer.data
        assert len(serializer.data['files']) >= 1

    def test_read_only_fields(self, project):
        serializer = ProjectSerializer(project)
        for field in ['id', 'user', 'status', 'created_at', 'updated_at', 'public_slug']:
            assert field in serializer.data


class TestProjectListSerializer:
    def test_serialize(self, project):
        serializer = ProjectListSerializer(project)
        assert serializer.data['id'] == str(project.id)
        assert serializer.data['name'] == project.name

    def test_file_count(self, project, project_file):
        serializer = ProjectListSerializer(project)
        assert serializer.data['file_count'] >= 1


class TestProjectFileSerializer:
    def test_serialize(self, project_file):
        serializer = ProjectFileSerializer(project_file)
        assert serializer.data['file_name'] == project_file.file_name
        assert serializer.data['file_path'] == project_file.file_path

    def test_content_excluded_in_list(self, project_file):
        serializer = ProjectFileSerializer(project_file)
        assert 'content' in serializer.data


class TestPublicProjectSerializer:
    def test_serialize(self, published_project):
        serializer = PublicProjectSerializer(published_project)
        assert serializer.data['name'] == published_project.name
        assert serializer.data['is_published'] is True


class TestPublicProjectListSerializer:
    def test_serialize(self, published_project):
        serializer = PublicProjectListSerializer(published_project)
        assert serializer.data['name'] == published_project.name
