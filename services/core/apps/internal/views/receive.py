import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.common.config import INTERNAL_API_KEY
from apps.projects.models import Project, ProjectFile
from apps.projects.serializers import ProjectSerializer, ProjectFileSerializer

logger = logging.getLogger(__name__)


class InternalAuthMixin:
    def _verify_key(self, request):
        key = request.META.get("HTTP_X_INTERNAL_API_KEY", "")
        if INTERNAL_API_KEY and key != INTERNAL_API_KEY:
            return Response({"error": "Forbidden"}, status=403)
        return None


class ProjectDetail(InternalAuthMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        forbidden = self._verify_key(request)
        if forbidden:
            return forbidden
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=404)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def patch(self, request, project_id):
        forbidden = self._verify_key(request)
        if forbidden:
            return forbidden
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=404)
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ProjectFileList(InternalAuthMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        forbidden = self._verify_key(request)
        if forbidden:
            return forbidden
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=404)
        files = project.files.all()
        serializer = ProjectFileSerializer(files, many=True)
        return Response(serializer.data)

    def post(self, request, project_id):
        forbidden = self._verify_key(request)
        if forbidden:
            return forbidden
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=404)
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data["project"] = str(project.id)
        serializer = ProjectFileSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ReceiveParsedData(InternalAuthMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, project_id):
        forbidden = self._verify_key(request)
        if forbidden:
            return forbidden
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

        logger.info("Internal: Parsed data received for project %s, %d files", project_id, file_count)

        return Response({"status": "ok", "project_id": project_id})


class ReceiveAIDocs(InternalAuthMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, project_id):
        forbidden = self._verify_key(request)
        if forbidden:
            return forbidden
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

        logger.info("Internal: AI docs received for project %s, status=%s", project_id, status_str)

        return Response({"status": "ok", "project_id": project_id})
