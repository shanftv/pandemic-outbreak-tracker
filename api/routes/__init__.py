"""
API Routes
Organized endpoint routers for the Pandemic Outbreak Tracker.
"""

from .health import router as health_router
from .predictions import router as predictions_router
from .locations import router as locations_router
from .danger_zones import router as danger_zones_router
from .metrics import router as metrics_router

__all__ = [
    "health_router",
    "predictions_router",
    "locations_router",
    "danger_zones_router",
    "metrics_router",
]
