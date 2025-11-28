"""
API Models/Schemas
Pydantic models for request and response validation.
"""

from .schemas import (
    HealthResponse,
    LocationInfo,
    LocationsResponse,
    PredictionData,
    LocationPrediction,
    PredictionsResponse,
    DangerZone,
    DangerZonesResponse,
    ModelMetrics,
    MetricsResponse,
    ErrorResponse,
)

__all__ = [
    "HealthResponse",
    "LocationInfo",
    "LocationsResponse",
    "PredictionData",
    "LocationPrediction",
    "PredictionsResponse",
    "DangerZone",
    "DangerZonesResponse",
    "ModelMetrics",
    "MetricsResponse",
    "ErrorResponse",
]
