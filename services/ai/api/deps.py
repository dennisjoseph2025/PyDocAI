from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..config.config import settings
from ..database import get_db as _get_db

api_key_header = APIKeyHeader(name="X-Internal-Api-Key", auto_error=False)


def verify_internal_key(key: str = Depends(api_key_header)):
    if settings.INTERNAL_API_KEY and key != settings.INTERNAL_API_KEY:
        raise HTTPException(401, "Invalid or missing internal API key")
    return key


def get_db() -> Session:
    """Returns DB session for AI service's own pgvector storage only.
    Project/file data is fetched from Django via internal API.
    """
    yield from _get_db()
