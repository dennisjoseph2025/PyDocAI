import json
import logging
import os

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.projects.models import Project

logger = logging.getLogger(__name__)

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


def _verify_internal_key(request):
    key = request.META.get("HTTP_X_INTERNAL_API_KEY", "")
    if INTERNAL_API_KEY and key != INTERNAL_API_KEY:
        return Response({"error": "Forbidden"}, status=403)
    return None


@api_view(["POST"])
@permission_classes([AllowAny])
def receive_parsed_data(request, project_id):
    forbidden = _verify_internal_key(request)
    if forbidden:
        return forbidden
    """
    Internal endpoint for FastAPI Parser service to POST parsed AST data.
    The Parser service calls this after it finishes parsing files.
    """
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Project not found"}, status=404)

    parsed_data = request.data.get("parsed_data") or request.data.get("parsed")
    file_count = request.data.get("file_count", 0)

    if parsed_data:
        project.parsed_data = parsed_data
    if file_count:
        project.project_info = {
            **(project.project_info or {}),
            "files_parsed": file_count,
        }

    project.status = Project.Status.PROCESSING
    project.save()

    logger.info(f"Internal: Parsed data received for project {project_id}, {file_count} files")

    return Response({"status": "ok", "project_id": project_id})


@api_view(["POST"])
@permission_classes([AllowAny])
def receive_ai_docs(request, project_id):
    forbidden = _verify_internal_key(request)
    if forbidden:
        return forbidden
    """
    Internal endpoint for FastAPI AI service to POST generated documentation.
    """
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Project not found"}, status=404)

    generated_docs = request.data.get("generated_docs")
    readme_docs = request.data.get("readme_docs")
    api_docs = request.data.get("api_docs")
    project_info = request.data.get("project_info")
    status_str = request.data.get("status", "done")
    error_message = request.data.get("error_message")

    if generated_docs:
        project.generated_docs = generated_docs
    if readme_docs:
        project.readme_docs = readme_docs
    if api_docs:
        project.api_docs = api_docs
    if project_info:
        project.project_info = project_info

    if status_str == "done":
        project.status = Project.Status.DONE
    elif status_str == "failed":
        project.status = Project.Status.FAILED
        project.error_message = error_message or "AI generation failed"

    project.save()

    logger.info(f"Internal: AI docs received for project {project_id}, status={status_str}")

    return Response({"status": "ok", "project_id": project_id})
