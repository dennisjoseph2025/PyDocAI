import uuid

from django.http import Http404, HttpResponse
from rest_framework.views import APIView

from apps.projects.models import Project


class ExportFolderDocsView(APIView):

    def get(self, request, project_id):
        try:
            project_id_uuid = uuid.UUID(str(project_id))
            project = Project.objects.get(id=project_id_uuid)
        except (Project.DoesNotExist, ValueError):
            raise Http404("Project not found") from None

        doc_type = request.query_params.get('type', 'all')

        if doc_type == 'readme':
            if not project.readme_docs:
                raise Http404("README not available yet - folder may still be processing")
            content = project.readme_docs
            filename = "README.md"
        elif doc_type == 'summary':
            if not project.generated_docs:
                raise Http404("Summary not available yet - folder may still be processing")
            content = project.generated_docs
            filename = "project_summary.md"
        elif doc_type == 'api':
            if not project.api_docs:
                raise Http404("API docs not available yet - folder may still be processing")
            content = project.api_docs
            filename = "api_docs.md"
        else:
            if not project.readme_docs and not project.generated_docs and not project.api_docs:
                raise Http404("Project documentation not available - please ensure folder upload was completed")

            parts = []
            if project.readme_docs:
                parts.append(project.readme_docs)
            if project.generated_docs:
                parts.append(f"# Project Documentation\n\n{project.generated_docs}")
            if project.api_docs:
                parts.append(f"# API Documentation\n\n{project.api_docs}")

            content = "\n\n---\n\n".join(parts)
            filename = "project_docs.md"

        return HttpResponse(
            content,
            content_type='text/markdown',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
