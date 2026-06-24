from apps.projects.models import Project, ProjectFile


def export_project_as_markdown(project_id: str) -> str:
    project = Project.objects.get(id=project_id)

    # Check if project-level docs exist (new feature)
    if project.readme_docs or project.project_info:
        combined = ""

        # Add README if available
        if project.readme_docs:
            combined += f"# {project.name} — README\n\n"
            combined += project.readme_docs
            combined += "\n\n---\n\n"

        # Add project summary/documentation if available
        if project.project_info and project.project_info.get('summary'):
            combined += f"# {project.name} — Project Documentation\n\n"
            combined += project.project_info.get('summary')
            combined += "\n\n---\n\n"

        # Add project info as JSON if available
        if project.project_info and not project.project_info.get('summary'):
            combined += f"# {project.name} — Project Information\n\n"
            combined += "## Project Details\n\n"
            import json
            combined += "```json\n"
            combined += json.dumps(project.project_info, indent=2)
            combined += "\n```\n\n"

        if combined:
            return combined

    # Fallback to per-file docs (legacy behavior)
    all_files = ProjectFile.objects.filter(project=project)

    combined = f"# {project.name} — Documentation\n\n"

    if not all_files.exists():
        combined += "_No files found for this project._\n"
        return combined

    for pf in all_files:
        combined += f"---\n\n## {pf.file_path}\n\n"
        if pf.generated_docs:
            combined += pf.generated_docs + "\n\n"
        else:
            combined += f"_No documentation generated. parsed_data present: {bool(pf.parsed_data)}_\n\n"

    return combined
