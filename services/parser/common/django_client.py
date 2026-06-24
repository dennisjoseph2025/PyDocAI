import os
import httpx
from typing import Any

DJANGO_INTERNAL_URL = os.getenv(
    "DJANGO_INTERNAL_URL",
    "http://django:8000/api/internal",
)
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


def _headers() -> dict:
    return {
        "X-Internal-Api-Key": INTERNAL_API_KEY,
        "Content-Type": "application/json",
    }


def get_project(project_id: str) -> dict[str, Any] | None:
    resp = httpx.get(
        f"{DJANGO_INTERNAL_URL}/projects/{project_id}/",
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def update_project(project_id: str, data: dict) -> dict[str, Any]:
    resp = httpx.patch(
        f"{DJANGO_INTERNAL_URL}/projects/{project_id}/",
        headers=_headers(),
        json=data,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def create_project_file(project_id: str, file_data: dict) -> dict[str, Any]:
    resp = httpx.post(
        f"{DJANGO_INTERNAL_URL}/projects/{project_id}/files/",
        headers=_headers(),
        json=file_data,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def send_parsed_data(project_id: str, parsed: dict, file_count: int):
    resp = httpx.post(
        f"{DJANGO_INTERNAL_URL}/projects/{project_id}/parsed/",
        headers=_headers(),
        json={"parsed": parsed, "file_count": file_count},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
