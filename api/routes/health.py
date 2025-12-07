"""
Health Check Router
Provides system health and status endpoints.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from api.models.schemas import HealthResponse
from api.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


def _check_azure_models() -> str:
    """Check if models are available in Azure Blob Storage."""
    if not settings.use_azure_storage:
        return "azure_not_configured"
    
    try:
        from azure.storage.blob import BlobServiceClient
        blob_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        container_client = blob_client.get_container_client(settings.azure_models_container)
        blobs = list(container_client.list_blobs())
        model_blobs = [b for b in blobs if b.name.endswith('.pkl')]
        
        if model_blobs:
            return f"loaded ({len(model_blobs)} models)"
        return "no_models"
    except Exception as e:
        logger.error(f"Failed to check Azure models: {e}")
        return "azure_error"


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
    # Check Azure Storage first if configured
    if settings.use_azure_storage:
        model_status = _check_azure_models()
    else:
        # Fallback to local file check
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
    checks = {}
    
    if settings.use_azure_storage:
        checks["azure_storage"] = settings.azure_storage_connection_string is not None
        checks["storage_mode"] = "azure"
    else:
        checks["models_directory"] = settings.models_dir.exists()
        checks["predictions_available"] = settings.predictions_json.exists()
        checks["storage_mode"] = "local"
    
    is_ready = all(v for k, v in checks.items() if k != "storage_mode")
    
    return {
        "ready": is_ready,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
