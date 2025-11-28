"""
Pandemic Outbreak Tracker API
Main FastAPI Application Entry Point

This API provides endpoints for:
- 7-day infection rate predictions
- Location data and statistics
- Danger zone visualization data for maps
- Model performance metrics
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from api.config import settings
from api.routes import (
    health_router,
    predictions_router,
    locations_router,
    danger_zones_router,
    metrics_router,
    simulations_router,
)


def create_app() -> FastAPI:
    """Application factory for creating the FastAPI app."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
## Pandemic Outbreak Tracker API

A REST API for accessing disease outbreak predictions and visualization data.

### Features

- **Predictions**: 7-day infection rate forecasts for tracked locations
- **Locations**: Information about tracked provinces/regions
- **Danger Zones**: Color-coded risk data for map visualization
- **Metrics**: Model performance statistics
- **Simulations**: Interactive SEIRD epidemic simulations

### For Frontend Developers

The main endpoints you'll need:

1. `GET /api/v1/danger-zones` - For rendering the map with color-coded zones
2. `GET /api/v1/danger-zones/geojson` - Direct GeoJSON for Mapbox/Leaflet
3. `GET /api/v1/predictions` - Raw prediction data for charts
4. `GET /api/v1/locations` - Location metadata

### Data Refresh

Predictions are updated daily at 6:00 AM UTC via automated pipeline.
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Register routers with /api/v1 prefix
    api_prefix = "/api/v1"
    
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(locations_router, prefix=api_prefix)
    app.include_router(predictions_router, prefix=api_prefix)
    app.include_router(danger_zones_router, prefix=api_prefix)
    app.include_router(metrics_router, prefix=api_prefix)
    app.include_router(simulations_router, prefix=api_prefix)
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
