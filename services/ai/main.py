import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import create_tables, engine
from config.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI service — creating tables if needed")
    create_tables()
    yield
    logger.info("Shutting down AI service — disposing connection pool")
    engine.dispose()


app = FastAPI(
    title="PyDocAI AI Generator Service",
    version="0.2.0",
    lifespan=lifespan,
)

origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


from api.routes.health import router as health_router
from api.routes.generate import router as generate_router
from api.routes.status import router as status_router

app.include_router(health_router)
app.include_router(generate_router, prefix="/api/ai")
app.include_router(status_router, prefix="/api/ai")
