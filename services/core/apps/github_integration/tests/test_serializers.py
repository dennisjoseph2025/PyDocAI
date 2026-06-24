from apps.github_integration.serializers import RepoImportSerializer


class TestRepoImportSerializer:
    def test_valid_data(self):
        serializer = RepoImportSerializer(data={'full_name': 'owner/repo'})
        assert serializer.is_valid()
        assert serializer.validated_data['full_name'] == 'owner/repo'
        assert serializer.validated_data['folder_path'] == '/'

    def test_all_fields(self):
        data = {
            'full_name': 'owner/repo',
            'folder_path': 'src/',
            'branch': 'main',
            'name': 'My Repo',
            'description': 'A test repo',
            'custom_info': {'key': 'value'},
        }
        serializer = RepoImportSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_full_name(self):
        serializer = RepoImportSerializer(data={})
        assert not serializer.is_valid()
        assert 'full_name' in serializer.errors
