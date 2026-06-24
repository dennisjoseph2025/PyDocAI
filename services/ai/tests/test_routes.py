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
    monkeypatch.setenv("DJANGO_INTERNAL_URL", "http://localhost:8000/api/internal")


@pytest.fixture
def mock_db():
    session = MagicMock()

    def gen():
        yield session

    with patch("api.deps.get_db", return_value=gen()):
        yield session


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "ai"


class TestGenerateDocs:
    @patch("api.routes.generate.get_project")
    def test_404_for_missing_project(self, mock_get):
        mock_get.return_value = None
        resp = client.post(
            "/api/ai/generate/",
            json={"project_id": str(uuid4())},
        )
        assert resp.status_code == 404

    @patch("api.routes.generate.get_project")
    @patch("api.routes.generate.get_project_files")
    @patch("api.routes.generate.send_ai_docs")
    @patch("api.routes.generate.update_project")
    @patch("config.config.settings.GROQ_API_KEY", None)
    def test_no_groq_key_uses_mock(self, mock_update, mock_send, mock_files, mock_get, mock_db):
        pid = str(uuid4())
        mock_get.return_value = {"id": pid, "name": "Test", "source_type": "file", "framework_info": {}}
        mock_files.return_value = [{
            "file_name": "test.py",
            "file_path": "test.py",
            "parsed_data": {
                "functions": [{"name": "foo", "args": []}],
                "classes": [], "imports": [], "error": False,
            },
            "content": "def foo(): pass",
        }]

        resp = client.post(
            "/api/ai/generate/",
            json={"project_id": pid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"


class TestAIStatus:
    @patch("api.routes.status.get_project")
    def test_returns_project_status(self, mock_get):
        mock_get.return_value = {
            "id": str(uuid4()),
            "status": "done",
            "generated_docs": "# Docs",
        }

        resp = client.get(f"/api/ai/status/{uuid4()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["has_docs"] is True

    @patch("api.routes.status.get_project")
    def test_404_for_unknown(self, mock_get):
        mock_get.return_value = None
        resp = client.get("/api/ai/status/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
