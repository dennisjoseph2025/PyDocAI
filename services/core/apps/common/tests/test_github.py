from unittest.mock import patch

from github import GithubException

from apps.common.github import (
    download_zipball,
    fetch_public_repo_api,
    get_github_client,
)


class TestGetGithubClient:
    def test_with_token(self):
        client = get_github_client('test-token')
        assert client is not None

    def test_without_token(self):
        with patch('django.conf.settings.GITHUB_API_TOKEN', None):
            client = get_github_client()
            assert client is not None


class TestFetchPublicRepoApi:
    def test_success(self):
        with patch('apps.common.github.requests.get') as mock:
            mock.return_value.status_code = 200
            mock.return_value.json.return_value = {'id': 1, 'name': 'repo'}
            result = fetch_public_repo_api('owner/repo')
            assert result['id'] == 1
            assert result['name'] == 'repo'

    def test_not_found(self):
        with patch('apps.common.github.requests.get') as mock:
            mock.return_value.status_code = 404
            mock.return_value.json.return_value = {'message': 'Not Found'}
            import pytest
            with pytest.raises(GithubException) as exc:
                fetch_public_repo_api('owner/repo')
            assert exc.value.status == 404

    def test_forbidden(self):
        with patch('apps.common.github.requests.get') as mock:
            mock.return_value.status_code = 403
            mock.return_value.json.return_value = {'message': 'Forbidden'}
            import pytest
            with pytest.raises(GithubException) as exc:
                fetch_public_repo_api('owner/repo')
            assert exc.value.status == 403


class TestDownloadZipball:
    def test_basic_download(self):
        with patch('apps.common.github.requests.get') as mock_get:
            import io, zipfile
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as zf:
                zf.writestr('repo-owner-sha/file.py', 'print("hello")')
            buf.seek(0)
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = buf.read()

            files = download_zipball('http://example.com/zip', {}, '/')
            assert len(files) == 1
            assert files[0]['file_path'] == 'file.py'
            assert files[0]['content'] == 'print("hello")'

    def test_with_file_filter(self):
        with patch('apps.common.github.requests.get') as mock_get:
            import io, zipfile
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as zf:
                zf.writestr('repo/file.py', 'code')
                zf.writestr('repo/readme.txt', 'docs')
            buf.seek(0)
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = buf.read()

            files = download_zipball('http://example.com/zip', {}, '/', file_filter=lambda n: n.endswith('.py'))
            assert len(files) == 1
            assert files[0]['file_path'] == 'file.py'

    def test_folder_path_filter(self):
        with patch('apps.common.github.requests.get') as mock_get:
            import io, zipfile
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as zf:
                zf.writestr('repo/src/main.py', 'code')
                zf.writestr('repo/tests/test_main.py', 'test')
            buf.seek(0)
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = buf.read()

            files = download_zipball('http://example.com/zip', {}, 'src')
            assert len(files) == 1
            assert files[0]['file_path'] == 'src/main.py'
