"""
Predictions Router
Endpoints for retrieving 7-day infection rate predictions.
"""

from datetime import datetime, UTC
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from api.models.schemas import (
    PredictionsResponse, 
    LocationPrediction, 
    PredictionStatus,
    ErrorResponse
)
from api.services.prediction_service import PredictionService


router = APIRouter(prefix="/predictions", tags=["Predictions"])

# Service instance
prediction_service = PredictionService()


@router.get(
    "",
    response_model=PredictionsResponse,
    summary="Get All Predictions",
    description="Retrieve 7-day predictions for all tracked locations.",
    responses={
        200: {"description": "Predictions retrieved successfully"},
        503: {"description": "Predictions not available", "model": ErrorResponse}
    }
)
async def get_all_predictions() -> PredictionsResponse:
    """
    Get 7-day predictions for all locations.
    
    Returns forecasted infection rates for the next 7 days
    for all tracked locations. Each prediction includes:
    - Daily predicted cases
    - Trend direction (increasing/decreasing/stable)
    - Comparison with previous 7 days
    - Data freshness status
    """
    predictions = await prediction_service.get_all_predictions()
    status = await prediction_service.get_prediction_status()
    generated_at = await prediction_service.get_last_generated_time()
    
    return PredictionsResponse(
        predictions=predictions,
        status=status,
        generated_at=generated_at or datetime.now(UTC),
        next_update=await prediction_service.get_next_update_time()
    )


@router.get(
    "/location/{location_id}",
    response_model=LocationPrediction,
    summary="Get Predictions for Location",
    description="Retrieve 7-day predictions for a specific location.",
    responses={
        200: {"description": "Predictions found"},
        404: {"description": "Location not found", "model": ErrorResponse}
    }
)
async def get_location_predictions(location_id: str) -> LocationPrediction:
    """
    Get 7-day predictions for a specific location.
    
    Args:
        location_id: Unique identifier for the location (e.g., "ncr")
    
    Returns:
        7-day forecast including daily predictions and trend analysis.
    """
    prediction = await prediction_service.get_prediction_by_location(location_id)
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for location: {location_id}"
        )
    
    return prediction


@router.get(
    "/summary",
    summary="Get Predictions Summary",
    description="Get a summary overview of all predictions."
)
async def get_predictions_summary():
    """
    Get a summary of predictions across all locations.
    
    Returns:
        Summary statistics including:
        - Total predicted cases across all locations
        - Locations with increasing trends
        - Locations with decreasing trends
        - Top 5 highest risk locations
    """
    return await prediction_service.get_predictions_summary()


@router.get(
    "/top-risk",
    response_model=List[LocationPrediction],
    summary="Get Top Risk Locations",
    description="Get locations with highest predicted cases."
)
async def get_top_risk_locations(
    limit: int = Query(5, ge=1, le=20, description="Number of locations to return")
) -> List[LocationPrediction]:
    """
    Get top risk locations sorted by predicted cases.
    
    Args:
        limit: Number of locations to return (1-20)
    
    Returns:
        List of locations sorted by predicted 7-day cases (highest first).
    """
    return await prediction_service.get_top_risk_locations(limit)
