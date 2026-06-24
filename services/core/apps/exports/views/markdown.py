from django.http import Http404, HttpResponse
from rest_framework.views import APIView

from apps.exports.generators import export_project_as_markdown


class ExportProjectMarkdownView(APIView):

    def get(self, request, project_id):
        try:
            markdown = export_project_as_markdown(str(project_id))
        except Exception as e:
            raise Http404(f"Export failed: {e}") from e

        return HttpResponse(
            markdown,
            content_type='text/markdown',
            headers={'Content-Disposition': f'attachment; filename="project_{project_id}_docs.md"'}
        )
