from celery import shared_task
import base64
import io
import zipfile
import logging

from apps.projects.models import Project
from apps.parser.tasks import parse_folder_task
from apps.parser.validators import should_exclude

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def import_github_repo_task(self, project_id, github_token, full_name, folder_path, branch, description, custom_info):
    try:
        from .fetcher import import_folder_from_repo

        project = Project.objects.get(id=project_id)

        files = import_folder_from_repo(github_token, full_name, folder_path, branch)

        if not files:
            project.status = Project.Status.FAILED
            project.save(update_fields=['status'])
            logger.warning(f"No Python files found in {full_name}/{folder_path}")
            return

        # Build zip in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.writestr(f['file_path'], f['content'])
        zip_buffer.seek(0)
        zip_base64 = base64.b64encode(zip_buffer.read()).decode('utf-8')

        py_files = [f['file_path'] for f in files if not should_exclude(f['file_path'])]

        parse_folder_task.delay(
            project.id,
            py_files,
            zip_base64,
            user_description=description,
            custom_info=custom_info,
        )

    except Exception as e:
        logger.exception(f"import_github_repo_task failed for project {project_id}: {e}")
        try:
            Project.objects.filter(id=project_id).update(status=Project.Status.FAILED)
        except Exception:
            pass
        raise self.retry(exc=e, countdown=10)