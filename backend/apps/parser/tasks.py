import base64
import io
import logging
import shutil
import tempfile
import zipfile

from celery import shared_task

from apps.ai.generator import generate_file_docs, generate_folder_docs
from apps.parser.ast_parser import parse_python_file
from apps.parser.validators import should_exclude, validate_python_code
from apps.projects.models import Project, ProjectFile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=30, rate_limit='5/m')
def parse_folder_task(self, project_id, py_files, zip_base64=None, user_description=None, custom_info=None):
    """
    Async task to parse multiple Python files from a ZIP archive and generate AI docs.
    Uses a unified, one-shot AI generation flow for efficiency.
    """
    project = None
    try:
        project = Project.objects.get(id=project_id)
        project.status = Project.Status.PROCESSING
        project.save()

        if user_description:
            project.description = user_description

        if custom_info:
            project.custom_details = custom_info

        project.save()

        if not zip_base64:
            project.status = Project.Status.FAILED
            project.error_message = "No ZIP data provided"
            project.save()
            return {'error': 'No ZIP data provided'}

        zip_data = base64.b64decode(zip_base64)
        zf = zipfile.ZipFile(io.BytesIO(zip_data))

        # 1. Store individual files and parse AST (No AI yet)
        results = []
        for file_path in py_files:
            if should_exclude(file_path):
                continue
            try:
                content = zf.read(file_path).decode('utf-8', errors='ignore')
                is_valid, _ = validate_python_code(content)
                if not is_valid:
                    continue

                parsed = parse_python_file(content)
                ProjectFile.objects.create(
                    project=project,
                    file_path=file_path,
                    file_name=file_path.split('/')[-1],
                    file_size=len(content),
                    content=content,
                    parsed_data=parsed,
                    generated_docs='',
                )
                results.append({'file_path': file_path, 'parsed': parsed})
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")

        # 2. Unified Documentation Generation
        temp_dir = tempfile.mkdtemp()
        try:
            zf.extractall(temp_dir)

            project_docs = generate_folder_docs(
                folder_path=temp_dir,
                project_name=project.name,
                user_description=user_description,
                custom_info=custom_info,
                parsed_ast_data=results
            )

            project.generated_docs = project_docs.get('summary', '')
            project.readme_docs = project_docs.get('readme', '')
            project.api_docs = project_docs.get('api_docs', '')
            project.project_info = project_docs.get('project_info', {})
            project.status = Project.Status.DONE
            project.save()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return {
            'project_id': str(project.id),
            'files_count': len(results),
        }

    except Exception as e:
        logger.error(f"parse_folder_task error: {e}")
        if project:
            project.status = Project.Status.FAILED
            project.error_message = str(e)
            project.save()
        return {'error': str(e)}


@shared_task(bind=True, max_retries=5, default_retry_delay=60, rate_limit='5/m')
def parse_and_generate_docs_task(self, project_id, source_code, file_name, file_size):
    """Async task to parse a single Python file and generate AI documentation."""
    project = None
    try:
        project = Project.objects.get(id=project_id)
        project.status = Project.Status.PROCESSING
        project.save()

        is_valid, error_msg = validate_python_code(source_code)
        if not is_valid:
            project.status = Project.Status.FAILED
            project.error_message = error_msg
            project.save()
            return {'error': error_msg}

        parsed = parse_python_file(source_code)
        try:
            generated_docs = generate_file_docs(parsed, file_name)
        except Exception as e:
            if 'rate_limit' in str(e).lower():
                raise self.retry(exc=e, countdown=60)
            raise e

        ProjectFile.objects.create(
            project=project,
            file_name=file_name,
            file_path=file_name,
            file_size=file_size,
            content=source_code,
            parsed_data=parsed,
            generated_docs=generated_docs,
        )

        project.generated_docs = generated_docs
        project.status = Project.Status.DONE
        project.save()

        return {'project_id': str(project.id)}

    except Exception as e:
        if project:
            project.status = Project.Status.FAILED
            project.error_message = str(e)
            project.save()
        return {'error': str(e)}
