from fastapi import APIRouter, HTTPException, Depends
from common.django_client import get_project
from api.deps import verify_internal_key

router = APIRouter()


@router.get("/status/{project_id}")
def parser_status(project_id: str, _auth: str = Depends(verify_internal_key)):
    project = get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    files = project.get("files", [])
    return {
        "project_id": project_id,
        "status": project.get("status"),
        "files_count": len(files),
    }
