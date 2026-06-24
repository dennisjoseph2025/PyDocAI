from typing import Optional
from pydantic import BaseModel


class AnalyzeFileResponse(BaseModel):
    project_id: str
    parsed: dict
    file_count: int
    framework: dict


class AnalyzeFolderResponse(BaseModel):
    project_id: str
    files_parsed: int
    framework: dict


class ParserStatusResponse(BaseModel):
    project_id: str
    status: str
    files_count: int
