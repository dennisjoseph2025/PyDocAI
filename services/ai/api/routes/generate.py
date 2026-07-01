import os
import tempfile
import shutil
import logging
import time as _time

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from schemas.requests import GenerateRequest
from schemas.responses import GenerateResponse
from services.groq import call_groq
from services.markdown import sanitize_markdown
from services.generation import generate_file_docs, generate_project_summary, mock_docs, retrieve_project_context
from services.docs_builder import build_api_docs
from common.django_client import get_project, get_project_files, send_ai_docs, update_project
from rag import embed_and_store_chunks
from api.deps import get_db, verify_internal_key
from config.config import settings

router = APIRouter()
logger = logging.getLogger("ai.generate")


def _call_ai_section(prompt_body: str, key_offset: int, label: str, max_tokens: int = 4096) -> str:
    plen = len(prompt_body)
    if plen > 12000:
        prompt_body = prompt_body[:12000] + "\n... (truncated)"
    return call_groq(prompt_body, max_tokens=max_tokens, model="llama-3.3-70b-versatile", key_start=key_offset)


def _build_project_context(
    project: dict, summary: dict, fw_name: str, fw_block: str,
    tree_trunc: str, deps: list, clone_hint: str, db: Session,
) -> str:
    return (
        f"Project Name: {project.get('name')}\n"
        f"Description: {project.get('description') or 'No description provided'}\n"
        f"Framework: {fw_name}\n"
        f"Architecture: {summary.get('architecture', 'monolith')}\n"
        f"Total Files: {summary['file_count']}{fw_block}\n\n"
        f"Project Structure:\n{tree_trunc}\n\n"
        f"Dependencies:\n{chr(10).join(deps)}\n\n"
        f"Apps/Modules: {', '.join(summary.get('apps', [])) or 'None detected'}\n"
        f"Package Manager: {summary.get('package_manager', 'pip')}\n"
        f"Relevant Code Context:\n{retrieve_project_context(str(project.get('id')), project.get('name', ''), db)}\n"
        f"{clone_hint}\n"
    )


@router.post("/generate/", response_model=GenerateResponse)
def generate_docs(req: GenerateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _auth: str = Depends(verify_internal_key)):
    project = get_project(req.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    update_project(req.project_id, {"status": "processing"})

    files_data = req.files_data
    if not files_data:
        files_data = get_project_files(req.project_id)
    if not files_data:
        raise HTTPException(400, "No parsed files found. Run parser first.")

    try:
        fw_info = project.get("framework_info") or {}
        source_type = project.get("source_type", "file")

        if source_type == "file" and len(files_data) == 1:
            f = files_data[0]
            parsed = f.get("parsed_data") or {}
            file_name = f.get("file_name", "untitled.py")

            if req.use_ai and settings.GROQ_API_KEY:
                try:
                    embed_and_store_chunks(req.project_id, files_data, db)
                except Exception as e:
                    logger.warning("Embedding failed (continuing without RAG): %s", e)
                docs = generate_file_docs(parsed, file_name, fw_info, db, req.project_id)
            else:
                docs = mock_docs(parsed, file_name, fw_info)

            send_ai_docs(req.project_id, {
                "generated_docs": sanitize_markdown(docs),
                "status": "done",
            })
        else:
            temp_dir = tempfile.mkdtemp()
            try:
                for f in files_data:
                    content = f.get("content") or ""
                    if content:
                        fp = os.path.join(temp_dir, f["file_path"])
                        os.makedirs(os.path.dirname(fp), exist_ok=True)
                        with open(fp, "w") as fh:
                            fh.write(content)

                summary = generate_project_summary(temp_dir, project.get("name"))
                update_project(req.project_id, {"project_info": summary})

                if req.use_ai and settings.GROQ_API_KEY:
                    try:
                        embed_and_store_chunks(req.project_id, files_data, db)
                    except Exception as e:
                        logger.warning("Embedding failed (continuing without RAG): %s", e)

                    fw_name = fw_info.get("primary_framework", summary.get("framework", "python"))
                    fw_summary = fw_info.get("summary", "")
                    fw_block = f"\nDetected Frameworks: {fw_summary}\n" if fw_summary else ""

                    tree_lines = (summary.get("project_tree") or "").splitlines()
                    if len(tree_lines) > 30:
                        tree_lines = tree_lines[:28] + ["... (truncated)"]
                    tree_trunc = "\n".join(tree_lines)

                    deps = summary.get("dependencies", [])
                    if len(deps) > 20:
                        deps = deps[:18] + ["... (truncated)"]

                    clone_url = (project.get("github_url") or "").strip()
                    repo_dir = project.get("name", "project")
                    clone_hint = ""
                    if clone_url:
                        clone_hint = f"\nClone URL: {clone_url}"
                        repo_dir = clone_url.rstrip("/").split("/")[-1].replace(".git", "") or repo_dir

                    api_docs = build_api_docs(files_data)
                    update_project(req.project_id, {"api_docs": api_docs})
                    _time.sleep(3)

                    has_root_req = any(f.get("file_path") == "requirements.txt" for f in files_data)
                    has_root_manage = any(f.get("file_path") == "manage.py" for f in files_data)
                    cd_dir = "." if (has_root_req or has_root_manage) else (repo_dir or ".")
                    pm_cmd = "pip install -r requirements.txt"

                    project_context = _build_project_context(
                        project, summary, fw_name, fw_block, tree_trunc,
                        deps, clone_hint, db,
                    )

                    detected_apps = summary.get("apps", [])
                    app_labels = [a.split(".")[-1].replace("_", " ").title() for a in detected_apps]
                    mermaid_lines = ["flowchart TD", "    A[Client] --> B[Backend]"]
                    for i, label in enumerate(app_labels):
                        node = chr(67 + i) if i < 24 else f"N{i}"
                        mermaid_lines.append(f"    B --> {node}[{label}]")
                    mermaid_block = "\n".join(mermaid_lines)
                    app_list_str = ", ".join(f"`{a}`" for a in detected_apps) if detected_apps else "the detected modules"

                    summary_prompt = f"""{project_context}

Generate a project summary with two parts.

Part 1 — Overview: 2-3 paragraphs on the project's purpose, architecture, data flow. Include exactly ONE detailed mermaid flowchart based on the actual apps above (do NOT add a second simplified version):

```mermaid
{mermaid_block}
```

Part 2 — App-by-App Breakdown: For EACH app/module detected in this project, write one paragraph explaining what that app does, its key files, and how it fits the architecture. Include ALL of: {app_list_str}. Do NOT skip any.

Output ONLY the summary content."""
                    summary_result = _call_ai_section(summary_prompt, 1, "SUMMARY", max_tokens=2048)
                    tree_block = "\n\n---\n\n## Project Structure\n\n```\n" + summary.get("project_tree", "") + "\n```\n"
                    generated = sanitize_markdown(summary_result + tree_block) if summary_result else tree_block.strip()

                    _time.sleep(3)

                    readme_prompt = f"""{project_context}

Write a README with:

## Title & Description
What the project is and who it's for (3-4 sentences).

## Key Features
5-7 bullet features from the app modules.

## Quick Start
```bash
git clone {clone_url or '<CLONE_URL>'}
cd {cd_dir}
{pm_cmd}
```
Then run: `python manage.py migrate && python manage.py runserver` (or equivalent for the framework).

## Architecture & Project Structure
Describe the monolithic layout, the apps under `backend/apps/`, and the data flow (2-3 paragraphs).

Output ONLY the README content."""
                    readme_result = _call_ai_section(readme_prompt, 0, "README", max_tokens=2048)
                    readme = sanitize_markdown(readme_result) if readme_result else f"# {project.get('name')}\n\nNo README generated."

                    send_ai_docs(req.project_id, {
                        "generated_docs": generated,
                        "readme_docs": readme,
                        "api_docs": api_docs,
                        "status": "done",
                    })
                else:
                    fallback = f"""# {project.get('name')}

## Overview
Mock project documentation for {project.get('name')}.

## Project Structure
{summary['project_tree']}

## Dependencies
{' '.join(summary.get('dependencies', [])) or 'Not detected'}

> Configure GROQ_API_KEY to generate AI-powered documentation."""
                    send_ai_docs(req.project_id, {
                        "generated_docs": sanitize_markdown(fallback),
                        "readme_docs": sanitize_markdown(fallback),
                        "status": "done",
                    })

            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        project = get_project(req.project_id)
        return GenerateResponse(
            project_id=req.project_id,
            status="done",
            generated_docs=project.get("generated_docs"),
            readme_docs=project.get("readme_docs"),
            api_docs=project.get("api_docs"),
        )

    except Exception as e:
        import traceback
        logger.error("Generation failed: %s\n%s", str(e), traceback.format_exc())
        send_ai_docs(req.project_id, {
            "status": "failed",
            "error_message": str(e),
        })
        return GenerateResponse(
            project_id=req.project_id,
            status="failed",
        )
