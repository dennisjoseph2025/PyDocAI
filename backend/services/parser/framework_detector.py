from typing import Any

TYPE_PRIORITY = {
    "web": 10,
    "api": 8,
    "server": 6,
    "pdf": 5,
    "cli": 4,
    "ai": 4,
    "task_queue": 3,
    "orm": 2,
    "migration": 1,
    "testing": 1,
    "validation": 1,
    "middleware": 1,
    "http": 0,
}

FRAMEWORK_PATTERNS = [
    {
        "name": "Django",
        "imports": ["django", "django.db", "django.urls", "django.shortcuts"],
        "files": ["manage.py", "wsgi.py", "asgi.py", "settings.py"],
        "dirs": ["migrations", "templates"],
        "type": "web",
    },
    {
        "name": "FastAPI",
        "imports": ["fastapi", "fastapi.routing"],
        "config": ["FastAPI("],
        "type": "web",
    },
    {
        "name": "Flask",
        "imports": ["flask", "flask.blueprints"],
        "config": ["Flask("],
        "type": "web",
    },
    {
        "name": "Django REST Framework",
        "imports": ["rest_framework"],
        "type": "api",
    },
    {
        "name": "Celery",
        "imports": ["celery", "celery.task"],
        "files": ["celery.py"],
        "type": "task_queue",
    },
    {
        "name": "SQLAlchemy",
        "imports": ["sqlalchemy", "sqlalchemy.orm", "sqlalchemy.ext"],
        "type": "orm",
    },
    {
        "name": "Alembic",
        "imports": ["alembic", "alembic.config"],
        "files": ["alembic.ini"],
        "dirs": ["alembic"],
        "type": "migration",
    },
    {
        "name": "Pydantic",
        "imports": ["pydantic"],
        "type": "validation",
    },
    {
        "name": "Pytest",
        "imports": ["pytest"],
        "files": ["pytest.ini", "conftest.py"],
        "type": "testing",
    },
    {
        "name": "Groq",
        "imports": ["groq"],
        "type": "ai",
    },
    {
        "name": "PydanticAI",
        "imports": ["pydantic_ai"],
        "type": "ai",
    },
    {
        "name": "LangChain",
        "imports": ["langchain", "langchain_core", "langchain_groq"],
        "type": "ai",
    },
    {
        "name": "WeasyPrint",
        "imports": ["weasyprint"],
        "type": "pdf",
    },
    {
        "name": "Gunicorn",
        "imports": ["gunicorn"],
        "files": ["gunicorn.conf.py"],
        "type": "server",
    },
    {
        "name": "httpx",
        "imports": ["httpx"],
        "type": "http",
    },
    {
        "name": "requests",
        "imports": ["requests"],
        "type": "http",
    },
    {
        "name": "Click",
        "imports": ["click"],
        "type": "cli",
    },
    {
        "name": "Typer",
        "imports": ["typer"],
        "type": "cli",
    },
    {
        "name": "CORS",
        "imports": ["corsheaders"],
        "type": "middleware",
    },
]


def detect_framework(
    imports: list[str], file_paths: list[str], source_codes: list[str]
) -> dict[str, Any]:
    detected = {}
    file_set = set(file_paths)
    all_source = "\n".join(source_codes)

    for fw in FRAMEWORK_PATTERNS:
        score = 0
        reasons = []

        for imp in fw.get("imports", []):
            if any(imp in i for i in imports):
                score += 2
                reasons.append(f"import:{imp}")

        for pat in fw.get("config", []):
            if pat.lower() in all_source.lower():
                score += 3
                reasons.append(f"config:{pat}")

        for fn in fw.get("files", []):
            if fn in file_set:
                score += 3
                reasons.append(f"file:{fn}")

        for dn in fw.get("dirs", []):
            if any(f"/{dn}/" in f or f.startswith(f"{dn}/") for f in file_paths):
                score += 2
                reasons.append(f"dir:{dn}")

        if score > 0:
            detected[fw["name"]] = {
                "score": score,
                "type": fw.get("type", "unknown"),
                "reasons": reasons,
            }

    primary = (
        max(
            detected.items(),
            key=lambda x: (x[1]["score"] * 2 + TYPE_PRIORITY.get(x[1]["type"], 0)),
        )
        if detected
        else None
    )

    return {
        "frameworks": detected,
        "primary_framework": primary[0] if primary else None,
        "primary_type": primary[1]["type"] if primary else None,
        "summary": _build_summary(detected),
    }


def _build_summary(detected: dict) -> str:
    if not detected:
        return "No known frameworks detected"
    parts = []
    weighted = sorted(
        detected.items(),
        key=lambda x: (
            x[1]["score"] * 2 + TYPE_PRIORITY.get(x[1]["type"], 0)
        ),
        reverse=True,
    )
    for name, info in weighted:
        parts.append(f"{name}:{info['type']}")
    return ", ".join(parts)
