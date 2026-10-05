from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report that the API process is running. This does not check MySQL or Ollama."""
    return HealthResponse(status="ok")
