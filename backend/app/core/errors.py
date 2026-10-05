import logging

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("app.errors")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Map expected failures to the public error shape. Log the status, not the message."""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        error = {"code": str(detail["code"]), "message": str(detail["message"])}
    else:
        error = {"code": "http_error", "message": "Request failed."}
    logger.error("http error status=%s path=%s", exc.status_code, request.url.path)
    return JSONResponse(status_code=exc.status_code, content={"error": error})


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a generic JSON error. Do not log the exception text; it may contain the database URL."""
    logger.error("unhandled error type=%s path=%s", type(exc).__name__, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred.",
            }
        },
    )
