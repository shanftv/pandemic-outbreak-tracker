"""
Health Check Router
Provides system health and status endpoints.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from api.models.schemas import HealthResponse
from api.config import settings


router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API is running and models are loaded."
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns the current status of the API including:
    - Service status
    - API version
    - Model availability status
    - Current timestamp
    """
    # Check if models are available
    model_status = "loaded"
    if not settings.models_dir.exists():
        model_status = "not_found"
    elif not any(settings.models_dir.glob("*.pkl")):
        model_status = "no_models"
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
        model_status=model_status
    )


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if the API is ready to serve requests."
)
async def readiness_check():
    """
    Readiness check for load balancers and orchestration systems.
    
    Returns 200 if ready, 503 if not ready.
    """
    checks = {
        "models_directory": settings.models_dir.exists(),
        "predictions_available": settings.predictions_json.exists(),
    }
    
    is_ready = all(checks.values())
    
    return {
        "ready": is_ready,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
