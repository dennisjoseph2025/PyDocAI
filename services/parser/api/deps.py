from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader

from config.config import settings

api_key_header = APIKeyHeader(name="X-Internal-Api-Key", auto_error=False)


def verify_internal_key(key: str = Depends(api_key_header)):
    if settings.INTERNAL_API_KEY and key != settings.INTERNAL_API_KEY:
        raise HTTPException(401, "Invalid or missing internal API key")
    return key
