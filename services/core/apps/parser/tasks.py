import base64
import io
import logging
import os
import zipfile

from celery import shared_task

from apps.common.config import INTERNAL_API_KEY
from apps.parser.validators import should_exclude
from apps.projects.models import Project

logger = logging.getLogger(__name__)

PARSER_URL = os.getenv("PARSER_URL", "http://fastapi-parser:8002")
AI_URL = os.getenv("AI_URL", "http://fastapi-ai:8003")


def _call_fastapi(method: str, url: str, **kwargs):
    import requests
    headers = kwargs.pop("headers", {})
    headers["X-Internal-Api-Key"] = INTERNAL_API_KEY
    resp = requests.request(method, url, headers=headers, timeout=300, **kwargs)
    resp.raise_for_status()
    return resp.json()


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def parse_folder_task(self, project_id, py_files, zip_base64=None, user_description=None, custom_info=None):
    project = None
    try:
        project = Project.objects.get(id=project_id)
        project.status = Project.Status.PROCESSING
        project.save()

        if not zip_base64:
            project.status = Project.Status.FAILED
            project.error_message = "No ZIP data provided"
            project.save()
            return {"error": "No ZIP data provided"}

        zip_data = base64.b64decode(zip_base64)
        zf = zipfile.ZipFile(io.BytesIO(zip_data))

        parsed_count = 0
        for file_path in py_files:
            if should_exclude(file_path):
                continue
            try:
                content = zf.read(file_path).decode("utf-8", errors="ignore")
                files = {"file": (file_path.split("/")[-1], content.encode("utf-8"), "text/x-python")}
                data = {"project_id": str(project_id), "name": project.name, "file_path": file_path}
                _call_fastapi("POST", f"{PARSER_URL}/api/parser/file/", files=files, data=data)
                parsed_count += 1
            except Exception as e:
                logger.warning(f"Error sending {file_path} to parser: {e}")

        ai_resp = _call_fastapi("POST", f"{AI_URL}/api/ai/generate/", json={"project_id": str(project_id)})

        project.refresh_from_db()

        if ai_resp.get("status") == "failed":
            project.status = Project.Status.FAILED
            if not project.error_message:
                project.error_message = ai_resp.get("error_message", "AI generation failed")
        else:
            project.status = Project.Status.DONE
        project.save()

        return {"project_id": str(project.id), "files_parsed": parsed_count}

    except Exception as e:
        logger.error(f"parse_folder_task error: {e}")
        if project:
            project.status = Project.Status.FAILED
            project.error_message = str(e)
            project.save()
        return {"error": str(e)}


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def parse_and_generate_docs_task(self, project_id, source_code, file_name, file_size):
    project = None
    try:
        project = Project.objects.get(id=project_id)
        project.status = Project.Status.PROCESSING
        project.save()

        files = {"file": (file_name, source_code.encode("utf-8"), "text/x-python")}
        data = {"project_id": str(project_id), "name": project.name}
        _call_fastapi("POST", f"{PARSER_URL}/api/parser/file/", files=files, data=data)

        ai_resp = _call_fastapi("POST", f"{AI_URL}/api/ai/generate/", json={"project_id": str(project_id)})

        project.refresh_from_db()

        if ai_resp.get("status") == "failed":
            project.status = Project.Status.FAILED
            if not project.error_message:
                project.error_message = ai_resp.get("error_message", "AI generation failed")
        else:
            project.status = Project.Status.DONE
        project.save()

        return {"project_id": str(project.id)}

    except Exception as e:
        if "rate_limit" in str(e).lower():
            raise self.retry(exc=e, countdown=60)
        logger.error(f"parse_and_generate_docs_task error: {e}")
        if project:
            project.status = Project.Status.FAILED
            project.error_message = str(e)
            project.save()
        return {"error": str(e)}
