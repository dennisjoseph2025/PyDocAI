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
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def mock_db():
    session = MagicMock()
    gen = mock_get_db(session)
    with patch("main.get_db", return_value=gen):
        yield session


def mock_get_db(session):
    yield session


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

    @patch("main.validate_python_code")
    @patch("main.parse_python_file")
    @patch("main.detect_framework")
    def test_parses_valid_file(self, mock_detect, mock_parse, mock_validate, mock_db):
        mock_validate.return_value = (True, None)
        mock_parse.return_value = {
            "functions": [{"name": "foo", "args": []}],
            "classes": [], "imports": [], "error": False,
        }
        mock_detect.return_value = {"primary_framework": "python"}
        mock_project = MagicMock()
        mock_project.id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

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

    @patch("main.should_exclude")
    @patch("main.validate_python_code")
    @patch("main.parse_python_file")
    def test_parses_zip(self, mock_parse, mock_validate, mock_exclude, mock_db):
        mock_exclude.return_value = False
        mock_validate.return_value = (True, None)
        mock_parse.return_value = {
            "functions": [], "classes": [], "imports": [], "error": False,
        }
        mock_project = MagicMock()
        mock_project.id = uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

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
    def test_returns_status(self, mock_db):
        mock_project = MagicMock()
        mock_project.id = uuid4()
        mock_project.status = "done"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.count.return_value = 3

        resp = client.get(f"/api/parser/status/{mock_project.id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"
        assert resp.json()["files_count"] == 3

    def test_404_for_unknown(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/parser/status/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
