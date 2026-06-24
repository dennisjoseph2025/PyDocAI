import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Parser service")
    yield
    logger.info("Shutting down Parser service")


app = FastAPI(
    title="PyDocAI Parser Service",
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
from api.routes.file import router as file_router
from api.routes.folder import router as folder_router
from api.routes.status import router as status_router

app.include_router(health_router)
app.include_router(file_router, prefix="/api/parser")
app.include_router(folder_router, prefix="/api/parser")
app.include_router(status_router, prefix="/api/parser")
