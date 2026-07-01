from typing import Optional
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    project_id: str
    file_path: Optional[str] = None
    use_ai: bool = True
    files_data: Optional[list] = None
