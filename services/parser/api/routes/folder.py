import io
import json
import zipfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from ast_parser import parse_python_file
from validators import validate_python_code, should_exclude
from framework_detector import detect_framework
from common.django_client import get_project, update_project, create_project_file
from api.deps import verify_internal_key

router = APIRouter()


@router.post("/folder/")
async def analyze_folder(
    folder: UploadFile = File(...),
    _auth: str = Depends(verify_internal_key),
    project_id: str = Form(...),
    name: str = Form("Untitled Project"),
    description: str = Form(""),
    custom_info: str = Form(None),
):
    if not folder.filename.endswith(".zip"):
        raise HTTPException(400, "File must be a .zip")

    try:
        zip_content = await folder.read()
        zf = zipfile.ZipFile(io.BytesIO(zip_content))
    except zipfile.BadZipFile:
        raise HTTPException(400, "Invalid zip file")

    py_files = [
        f for f in zf.namelist()
        if f.endswith(".py") and not should_exclude(f)
    ]

    if not py_files:
        raise HTTPException(400, "No Python files found after filtering")

    project = get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    if custom_info:
        try:
            update_project(project_id, {"custom_details": json.loads(custom_info)})
        except json.JSONDecodeError:
            update_project(project_id, {"custom_details": {"details": custom_info}})

    all_imports: list[str] = []
    all_paths: list[str] = []
    all_sources: list[str] = []

    results = []
    for file_path in py_files:
        try:
            content = zf.read(file_path).decode("utf-8", errors="ignore")
            is_valid, _ = validate_python_code(content)
            if not is_valid:
                continue

            parsed = parse_python_file(content)
            create_project_file(project_id, {
                "file_path": file_path,
                "file_name": file_path.split("/")[-1],
                "file_size": len(content),
                "content": content,
                "parsed_data": parsed,
                "generated_docs": "",
            })

            imports = [imp.get("display", str(imp)) if isinstance(imp, dict) else str(imp) for imp in parsed.get("imports", [])]
            all_imports.extend(imports)
            all_paths.append(file_path)
            all_sources.append(content)
            results.append({"file_path": file_path, "parsed": parsed})
        except Exception:
            continue

    fw_info = detect_framework(all_imports, all_paths, all_sources)

    update_project(project_id, {
        "framework_info": fw_info,
        "parsed_data": results,
        "status": "processing",
    })

    return {
        "project_id": project_id,
        "files_parsed": len(results),
        "framework": fw_info,
    }
