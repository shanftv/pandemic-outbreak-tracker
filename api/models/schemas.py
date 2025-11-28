"""
Pydantic Schemas for API Request/Response Models

These schemas define the structure of data exchanged between the API
and clients (frontend applications).
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class DangerLevel(str, Enum):
    """Risk level classification for danger zones."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class PredictionStatus(str, Enum):
    """Status of prediction data freshness."""
    FRESH = "fresh"          # Updated within last 24 hours
    STALE = "stale"          # Updated more than 24 hours ago
    UNAVAILABLE = "unavailable"  # No predictions available


# ============================================================================
# Health Check Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server timestamp")
    model_status: str = Field(..., description="ML model availability status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-28T12:00:00Z",
                "model_status": "loaded"
            }
        }
    )


# ============================================================================
# Location Schemas
# ============================================================================

class LocationInfo(BaseModel):
    """Information about a tracked location."""
    id: str = Field(..., description="Unique location identifier")
    name: str = Field(..., description="Location display name")
    total_cases: int = Field(..., description="Total historical cases")
    last_updated: datetime = Field(..., description="Last data update timestamp")
    latitude: Optional[float] = Field(None, description="Location latitude")
    longitude: Optional[float] = Field(None, description="Location longitude")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ncr",
                "name": "NCR",
                "total_cases": 150000,
                "last_updated": "2025-11-28T06:00:00Z",
                "latitude": 14.5995,
                "longitude": 120.9842
            }
        }
    )


class LocationsResponse(BaseModel):
    """Response containing list of all tracked locations."""
    locations: List[LocationInfo] = Field(..., description="List of tracked locations")
    count: int = Field(..., description="Total number of locations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "locations": [
                    {
                        "id": "ncr",
                        "name": "NCR",
                        "total_cases": 150000,
                        "last_updated": "2025-11-28T06:00:00Z",
                        "latitude": 14.5995,
                        "longitude": 120.9842
                    }
                ],
                "count": 1
            }
        }
    )


# ============================================================================
# Prediction Schemas
# ============================================================================

class PredictionData(BaseModel):
    """Single day prediction data."""
    date: str = Field(..., description="Prediction date (YYYY-MM-DD)")
    predicted_cases: float = Field(..., description="Predicted new cases")
    day_ahead: int = Field(..., description="Days ahead from today (1-7)")
    confidence_lower: Optional[float] = Field(None, description="Lower confidence bound")
    confidence_upper: Optional[float] = Field(None, description="Upper confidence bound")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-11-29",
                "predicted_cases": 125.5,
                "day_ahead": 1,
                "confidence_lower": 100.0,
                "confidence_upper": 150.0
            }
        }
    )


class LocationPrediction(BaseModel):
    """7-day prediction for a specific location."""
    location_id: str = Field(..., description="Location identifier")
    location_name: str = Field(..., description="Location display name")
    predictions: List[PredictionData] = Field(..., description="7-day forecast")
    total_predicted: float = Field(..., description="Sum of predicted cases for 7 days")
    trend: str = Field(..., description="Trend direction: increasing/decreasing/stable")
    last_7_day_actual: Optional[float] = Field(None, description="Actual cases from last 7 days")
    percent_change: Optional[float] = Field(None, description="Percent change from last 7 days")
    generated_at: datetime = Field(..., description="When prediction was generated")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location_id": "ncr",
                "location_name": "NCR",
                "predictions": [
                    {"date": "2025-11-29", "predicted_cases": 125.5, "day_ahead": 1}
                ],
                "total_predicted": 875.5,
                "trend": "increasing",
                "last_7_day_actual": 800.0,
                "percent_change": 9.4,
                "generated_at": "2025-11-28T06:00:00Z"
            }
        }
    )


class PredictionsResponse(BaseModel):
    """Response containing predictions for all or specific locations."""
    predictions: List[LocationPrediction] = Field(..., description="Predictions by location")
    status: PredictionStatus = Field(..., description="Data freshness status")
    generated_at: datetime = Field(..., description="Batch generation timestamp")
    next_update: Optional[datetime] = Field(None, description="Next scheduled update time")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "predictions": [],
                "status": "fresh",
                "generated_at": "2025-11-28T06:00:00Z",
                "next_update": "2025-11-29T06:00:00Z"
            }
        }
    )


# ============================================================================
# Danger Zone Schemas (for Map Visualization)
# ============================================================================

class DangerZone(BaseModel):
    """
    Danger zone data for map visualization.
    Used by frontend to render color-coded regions on the map.
    """
    location_id: str = Field(..., description="Location identifier")
    location_name: str = Field(..., description="Location display name")
    latitude: float = Field(..., description="Center latitude")
    longitude: float = Field(..., description="Center longitude")
    danger_level: DangerLevel = Field(..., description="Risk classification")
    risk_score: float = Field(..., description="Numeric risk score (0-100)")
    predicted_cases_7d: float = Field(..., description="Predicted cases next 7 days")
    percent_change: float = Field(..., description="Percent change from last week")
    color_hex: str = Field(..., description="Suggested color for map")
    radius_meters: int = Field(..., description="Suggested circle radius for map")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location_id": "ncr",
                "location_name": "NCR",
                "latitude": 14.5995,
                "longitude": 120.9842,
                "danger_level": "high",
                "risk_score": 75.5,
                "predicted_cases_7d": 875.5,
                "percent_change": 15.2,
                "color_hex": "#FF6B6B",
                "radius_meters": 50000
            }
        }
    )


class DangerZonesResponse(BaseModel):
    """Response containing all danger zones for map rendering."""
    danger_zones: List[DangerZone] = Field(..., description="List of danger zones")
    legend: dict = Field(..., description="Color legend for map")
    generated_at: datetime = Field(..., description="Data generation timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "danger_zones": [],
                "legend": {
                    "low": {"color": "#4CAF50", "label": "Low Risk (0-25)"},
                    "moderate": {"color": "#FFC107", "label": "Moderate Risk (25-50)"},
                    "high": {"color": "#FF9800", "label": "High Risk (50-75)"},
                    "critical": {"color": "#F44336", "label": "Critical Risk (75-100)"}
                },
                "generated_at": "2025-11-28T06:00:00Z"
            }
        }
    )


# ============================================================================
# Model Metrics Schemas
# ============================================================================

class ModelMetrics(BaseModel):
    """Performance metrics for a location's prediction model."""
    location: str = Field(..., description="Location name")
    validation_mae: float = Field(..., description="Validation Mean Absolute Error")
    validation_rmse: float = Field(..., description="Validation Root Mean Squared Error")
    test_mae: float = Field(..., description="Test Mean Absolute Error")
    test_rmse: float = Field(..., description="Test Root Mean Squared Error")
    test_r2: float = Field(..., description="Test R-squared score")
    n_estimators: int = Field(..., description="Number of estimators used")
    trained_at: Optional[datetime] = Field(None, description="Model training timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": "NCR",
                "validation_mae": 15.2,
                "validation_rmse": 22.5,
                "test_mae": 18.3,
                "test_rmse": 25.1,
                "test_r2": 0.85,
                "n_estimators": 150,
                "trained_at": "2025-11-28T06:00:00Z"
            }
        }
    )


class MetricsResponse(BaseModel):
    """Response containing model performance metrics."""
    metrics: List[ModelMetrics] = Field(..., description="Metrics for all models")
    average_mae: float = Field(..., description="Average MAE across all models")
    average_r2: float = Field(..., description="Average R² across all models")
    last_training: datetime = Field(..., description="Last model training timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metrics": [],
                "average_mae": 17.5,
                "average_r2": 0.82,
                "last_training": "2025-11-28T06:00:00Z"
            }
        }
    )


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "NotFoundError",
                "message": "Location not found",
                "detail": "No data available for location_id: xyz"
            }
        }
    )
