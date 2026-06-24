from typing import Optional
from pydantic import BaseModel


class GenerateResponse(BaseModel):
    project_id: str
    status: str
    generated_docs: Optional[str] = None
    readme_docs: Optional[str] = None
    api_docs: Optional[str] = None
