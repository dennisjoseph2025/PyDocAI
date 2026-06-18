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

    def gen():
        yield session

    with patch("main.get_db", return_value=gen()):
        yield session


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "ai"


class TestGenerateDocs:
    def test_404_for_missing_project(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        resp = client.post(
            "/api/ai/generate/",
            json={"project_id": str(uuid4())},
        )
        assert resp.status_code == 404

    @patch("main.GROQ_API_KEY", None)
    def test_no_groq_key_uses_mock(self, mock_db):
        mock_project = MagicMock()
        mock_project.id = uuid4()
        mock_project.source_type = "file"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [
            MagicMock(file_name="test.py", parsed_data={
                "functions": [{"name": "foo", "args": []}],
                "classes": [], "imports": [], "error": False,
            }, content="def foo(): pass")
        ]

        resp = client.post(
            "/api/ai/generate/",
            json={"project_id": str(mock_project.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert "Mock documentation" in (data.get("generated_docs") or "")


class TestAIStatus:
    def test_returns_project_status(self, mock_db):
        mock_project = MagicMock()
        mock_project.id = uuid4()
        mock_project.status = "done"
        mock_project.generated_docs = "# Docs"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        resp = client.get(f"/api/ai/status/{mock_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["has_docs"] is True

    def test_404_for_unknown(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/ai/status/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestSanitizeMarkdown:
    @patch("main.GROQ_API_KEY", None)
    def test_generated_docs_is_sanitized(self, mock_db):
        mock_project = MagicMock()
        mock_project.id = uuid4()
        mock_project.source_type = "file"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [
            MagicMock(file_name="test.py", parsed_data={
                "functions": [], "classes": [], "imports": [], "error": False,
            }, content="# code")
        ]

        resp = client.post(
            "/api/ai/generate/",
            json={"project_id": str(mock_project.id)},
        )
        assert resp.status_code == 200
        docs = resp.json().get("generated_docs", "")
        assert "\n\n\n" not in docs
