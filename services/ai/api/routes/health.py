from fastapi import APIRouter
from ...config.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai",
        "groq_configured": bool(settings.GROQ_API_KEY),
        "embedding_model": settings.EMBEDDING_MODEL,
    }
