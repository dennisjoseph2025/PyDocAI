import io
import json
import os
import base64
import zipfile
import uuid
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, engine, Base, create_tables
from models import Project, ProjectFile
from ast_parser import parse_python_file
from validators import validate_python_code, should_exclude
from framework_detector import detect_framework

create_tables()

app = FastAPI(title="PyDocAI Parser Service", version="0.2.0")

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
api_key_header = APIKeyHeader(name="X-Internal-Api-Key", auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_internal_key(key: str = Depends(api_key_header)):
    if INTERNAL_API_KEY and key != INTERNAL_API_KEY:
        raise HTTPException(401, "Invalid or missing internal API key")
    return key


@app.get("/health")
def health():
    return {"status": "ok", "service": "parser"}


@app.post("/api/parser/file/")
async def analyze_file(
    _auth: str = Depends(verify_internal_key),
    file: UploadFile = File(...),
    project_id: str = Form(...),
    name: str = Form("Untitled Project"),
    description: str = Form(""),
    file_path: str = Form(None),
    db: Session = Depends(get_db),
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

    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(404, "Project not found")

    imports = [imp.get("display", str(imp)) if isinstance(imp, dict) else str(imp) for imp in parsed.get("imports", [])]
    fw_info = detect_framework(imports, [file_path or file.filename], [source_code])
    project.framework_info = fw_info

    project.parsed_data = parsed
    project.status = "processing"
    project.updated_at = datetime.utcnow()
    db.commit()

    final_path = file_path or file.filename
    db.add(ProjectFile(
        project_id=project.id,
        file_path=final_path,
        file_name=file.filename.split("/")[-1],
        file_size=len(source_code),
        content=source_code,
        parsed_data=parsed,
        generated_docs="",
    ))
    db.commit()

    return {
        "project_id": project_id,
        "parsed": parsed,
        "file_count": 1,
        "framework": fw_info,
    }


@app.post("/api/parser/folder/")
async def analyze_folder(
    folder: UploadFile = File(...),
    _auth: str = Depends(verify_internal_key),
    project_id: str = Form(...),
    name: str = Form("Untitled Project"),
    description: str = Form(""),
    custom_info: str = Form(None),
    db: Session = Depends(get_db),
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

    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(404, "Project not found")

    if custom_info:
        try:
            project.custom_details = json.loads(custom_info)
        except json.JSONDecodeError:
            project.custom_details = {"details": custom_info}

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
            db.add(ProjectFile(
                project_id=project.id,
                file_path=file_path,
                file_name=file_path.split("/")[-1],
                file_size=len(content),
                content=content,
                parsed_data=parsed,
                generated_docs="",
            ))

            imports = [imp.get("display", str(imp)) if isinstance(imp, dict) else str(imp) for imp in parsed.get("imports", [])]
            all_imports.extend(imports)
            all_paths.append(file_path)
            all_sources.append(content)
            results.append({"file_path": file_path, "parsed": parsed})
        except Exception:
            continue

    fw_info = detect_framework(all_imports, all_paths, all_sources)
    project.framework_info = fw_info
    project.parsed_data = results
    project.status = "processing"
    project.updated_at = datetime.utcnow()
    db.commit()

    return {
        "project_id": project_id,
        "files_parsed": len(results),
        "framework": fw_info,
    }


@app.get("/api/parser/status/{project_id}")
def parser_status(project_id: str, db: Session = Depends(get_db), _auth: str = Depends(verify_internal_key)):
    project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return {
        "project_id": str(project.id),
        "status": project.status,
        "files_count": db.query(ProjectFile).filter(
            ProjectFile.project_id == project.id
        ).count(),
    }
