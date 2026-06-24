import io
import zipfile
from uuid import uuid4
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "")
    monkeypatch.setenv("DJANGO_INTERNAL_URL", "http://localhost:8000/api/internal")


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAnalyzeFile:
    def test_rejects_non_py_files(self):
        resp = client.post(
            "/api/parser/file/",
            data={"project_id": str(uuid4()), "name": "Test"},
            files={"file": ("test.txt", b"not python")},
        )
        assert resp.status_code == 400

    def test_rejects_invalid_python(self):
        resp = client.post(
            "/api/parser/file/",
            data={"project_id": str(uuid4()), "name": "Test"},
            files={"file": ("bad.py", b"def foo() pass")},
        )
        assert resp.status_code == 400

    @patch("api.routes.file.get_project")
    @patch("api.routes.file.create_project_file")
    @patch("api.routes.file.update_project")
    def test_parses_valid_file(self, mock_update, mock_create, mock_get):
        mock_get.return_value = {"id": str(uuid4()), "name": "Test"}
        mock_create.return_value = {"id": str(uuid4())}
        mock_update.return_value = {"id": str(uuid4())}

        pid = str(uuid4())
        resp = client.post(
            "/api/parser/file/",
            data={"project_id": pid, "name": "Test"},
            files={"file": ("test.py", b"def foo(): pass")},
        )
        assert resp.status_code == 200
        assert resp.json()["project_id"] == pid
        assert resp.json()["file_count"] == 1


class TestAnalyzeFolder:
    def test_rejects_non_zip(self):
        resp = client.post(
            "/api/parser/folder/",
            data={"project_id": str(uuid4()), "name": "Test"},
            files={"folder": ("test.txt", b"content")},
        )
        assert resp.status_code == 400

    @patch("api.routes.folder.should_exclude")
    @patch("api.routes.folder.get_project")
    @patch("api.routes.folder.create_project_file")
    @patch("api.routes.folder.update_project")
    def test_parses_zip(self, mock_update, mock_create, mock_get, mock_exclude):
        mock_exclude.return_value = False
        mock_get.return_value = {"id": str(uuid4()), "name": "Test"}
        mock_create.return_value = {"id": str(uuid4())}
        mock_update.return_value = {"id": str(uuid4())}

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("app/main.py", "def bar(): pass\n")
        zip_bytes = zip_buffer.getvalue()

        resp = client.post(
            "/api/parser/folder/",
            data={"project_id": str(uuid4()), "name": "Test"},
            files={"folder": ("proj.zip", zip_bytes, "application/zip")},
        )
        assert resp.status_code == 200
        assert resp.json()["files_parsed"] == 1


class TestParserStatus:
    @patch("api.routes.status.get_project")
    def test_returns_status(self, mock_get):
        mock_get.return_value = {
            "id": str(uuid4()),
            "status": "done",
            "files": [{"id": "f1"}, {"id": "f2"}, {"id": "f3"}],
        }

        resp = client.get(f"/api/parser/status/{uuid4()}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"
        assert resp.json()["files_count"] == 3

    @patch("api.routes.status.get_project")
    def test_404_for_unknown(self, mock_get):
        mock_get.return_value = None
        resp = client.get("/api/parser/status/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
