from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from ast_parser import parse_python_file
from validators import validate_python_code
from framework_detector import detect_framework
from common.django_client import get_project, update_project, create_project_file
from api.deps import verify_internal_key

router = APIRouter()


@router.post("/file/")
async def analyze_file(
    _auth: str = Depends(verify_internal_key),
    file: UploadFile = File(...),
    project_id: str = Form(...),
    name: str = Form("Untitled Project"),
    description: str = Form(""),
    file_path: str = Form(None),
):
    if not file.filename.endswith(".py"):
        raise HTTPException(400, "Only .py files are allowed")

    try:
        source_code = (await file.read()).decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "File must be UTF-8 encoded")

    is_valid, err = validate_python_code(source_code)
    if not is_valid:
        raise HTTPException(400, err)

    parsed = parse_python_file(source_code)

    project = get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    imports = [imp.get("display", str(imp)) if isinstance(imp, dict) else str(imp) for imp in parsed.get("imports", [])]
    fw_info = detect_framework(imports, [file_path or file.filename], [source_code])

    final_path = file_path or file.filename
    create_project_file(project_id, {
        "file_path": final_path,
        "file_name": file.filename.split("/")[-1],
        "file_size": len(source_code),
        "content": source_code,
        "parsed_data": parsed,
        "generated_docs": "",
    })

    update_project(project_id, {
        "framework_info": fw_info,
        "parsed_data": parsed,
        "status": "processing",
    })

    return {
        "project_id": project_id,
        "parsed": parsed,
        "file_count": 1,
        "framework": fw_info,
    }
