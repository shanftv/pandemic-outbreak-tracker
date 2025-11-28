"""
Metrics Router
Endpoints for model performance metrics and statistics.
"""

from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException
from api.models.schemas import MetricsResponse, ModelMetrics, ErrorResponse
from api.config import settings
import pandas as pd


router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get(
    "",
    response_model=MetricsResponse,
    summary="Get Model Metrics",
    description="Retrieve performance metrics for all trained models.",
    responses={
        200: {"description": "Metrics retrieved successfully"},
        503: {"description": "Metrics not available", "model": ErrorResponse}
    }
)
async def get_all_metrics() -> MetricsResponse:
    """
    Get performance metrics for all prediction models.
    
    Returns:
        Metrics including MAE, RMSE, R² for each location model,
        plus aggregate statistics across all models.
    """
    if not settings.metrics_csv.exists():
        raise HTTPException(
            status_code=503,
            detail="Model metrics not available. Models may not be trained yet."
        )
    
    try:
        df = pd.read_csv(settings.metrics_csv)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error reading metrics: {str(e)}"
        )
    
    metrics_list = []
    for _, row in df.iterrows():
        metrics = ModelMetrics(
            location=row["location"],
            validation_mae=round(row["val_mae"], 2),
            validation_rmse=round(row["val_rmse"], 2),
            test_mae=round(row["test_mae"], 2),
            test_rmse=round(row["test_rmse"], 2),
            test_r2=round(row["test_r2"], 4),
            n_estimators=int(row["n_estimators"]),
            trained_at=datetime.now(UTC)  # Would come from model metadata
        )
        metrics_list.append(metrics)
    
    avg_mae = round(df["test_mae"].mean(), 2)
    avg_r2 = round(df["test_r2"].mean(), 4)
    
    return MetricsResponse(
        metrics=metrics_list,
        average_mae=avg_mae,
        average_r2=avg_r2,
        last_training=datetime.now(UTC)  # Would come from model metadata
    )


@router.get(
    "/location/{location_name}",
    response_model=ModelMetrics,
    summary="Get Metrics for Location",
    description="Retrieve performance metrics for a specific location's model."
)
async def get_location_metrics(location_name: str) -> ModelMetrics:
    """
    Get metrics for a specific location's model.
    
    Args:
        location_name: Name of the location (e.g., "NCR")
    
    Returns:
        Model performance metrics for the specified location.
    """
    if not settings.metrics_csv.exists():
        raise HTTPException(
            status_code=503,
            detail="Model metrics not available."
        )
    
    try:
        df = pd.read_csv(settings.metrics_csv)
        row = df[df["location"].str.lower() == location_name.lower()]
        
        if row.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No metrics found for location: {location_name}"
            )
        
        row = row.iloc[0]
        return ModelMetrics(
            location=row["location"],
            validation_mae=round(row["val_mae"], 2),
            validation_rmse=round(row["val_rmse"], 2),
            test_mae=round(row["test_mae"], 2),
            test_rmse=round(row["test_rmse"], 2),
            test_r2=round(row["test_r2"], 4),
            n_estimators=int(row["n_estimators"]),
            trained_at=datetime.now(UTC)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading metrics: {str(e)}"
        )
