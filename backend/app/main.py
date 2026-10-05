import logging

from fastapi import FastAPI, HTTPException

from app.api.health import router as health_router
from app.api.ollama import router as ollama_router
from app.core.config import get_settings
from app.core.errors import http_exception_handler, unhandled_exception_handler
from app.core.logging import RequestIdMiddleware, setup_logging
from app.db.session import get_engine

logger = logging.getLogger("app.main")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()
    get_engine()
    logger.info("application starting env=%s", settings.app_env)

    app = FastAPI(title="Local AI Assistant")
    app.add_middleware(RequestIdMiddleware)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(health_router, prefix="/api")
    app.include_router(ollama_router, prefix="/api")
    return app


app = create_app()
