"""
Danger Zones Router
Endpoints for map visualization data with color-coded danger levels.
"""

from datetime import datetime, UTC
from fastapi import APIRouter, Query
from api.models.schemas import DangerZonesResponse, DangerZone, DangerLevel
from api.services.prediction_service import PredictionService
from api.config import settings, LOCATION_COORDINATES


router = APIRouter(prefix="/danger-zones", tags=["Danger Zones"])

# Service instance
prediction_service = PredictionService()


def get_danger_level(risk_score: float) -> DangerLevel:
    """Classify risk score into danger level."""
    if risk_score >= settings.danger_high_threshold:
        return DangerLevel.CRITICAL
    elif risk_score >= settings.danger_moderate_threshold:
        return DangerLevel.HIGH
    elif risk_score >= settings.danger_low_threshold:
        return DangerLevel.MODERATE
    else:
        return DangerLevel.LOW


def get_danger_color(danger_level: DangerLevel) -> str:
    """Get hex color for danger level."""
    color_map = {
        DangerLevel.LOW: settings.danger_color_low,
        DangerLevel.MODERATE: settings.danger_color_moderate,
        DangerLevel.HIGH: settings.danger_color_high,
        DangerLevel.CRITICAL: settings.danger_color_critical,
    }
    return color_map[danger_level]


@router.get(
    "",
    response_model=DangerZonesResponse,
    summary="Get Danger Zones",
    description="""
    Get danger zone data for map visualization.
    
    Returns color-coded zones based on predicted infection rates.
    Use this data to render circles/polygons on Mapbox/Leaflet maps.
    
    **Color Legend:**
    - 🟢 Green (#4CAF50): Low Risk (0-25)
    - 🟡 Yellow (#FFC107): Moderate Risk (25-50)
    - 🟠 Orange (#FF9800): High Risk (50-75)
    - 🔴 Red (#F44336): Critical Risk (75-100)
    """
)
async def get_danger_zones(
    min_risk: float = Query(0, ge=0, le=100, description="Minimum risk score to include"),
    include_low_risk: bool = Query(True, description="Include low-risk zones")
) -> DangerZonesResponse:
    """
    Get all danger zones for map rendering.
    
    Returns a list of danger zones with:
    - Coordinates (lat/lng)
    - Risk classification and score
    - Suggested color and radius for map display
    - Predicted cases and trend data
    """
    predictions = await prediction_service.get_all_predictions()
    danger_zones = []
    
    for pred in predictions:
        # Get coordinates for location
        coords = LOCATION_COORDINATES.get(pred.location_name, {})
        if not coords:
            continue
        
        # Calculate risk score (normalized 0-100)
        # Using percent change and total predicted cases
        risk_score = min(100, max(0, 
            (pred.total_predicted / 100) + (pred.percent_change or 0) * 0.5
        ))
        
        danger_level = get_danger_level(risk_score)
        
        # Skip low risk if requested
        if not include_low_risk and danger_level == DangerLevel.LOW:
            continue
        
        # Skip if below minimum risk
        if risk_score < min_risk:
            continue
        
        zone = DangerZone(
            location_id=pred.location_id,
            location_name=pred.location_name,
            latitude=coords["latitude"],
            longitude=coords["longitude"],
            danger_level=danger_level,
            risk_score=round(risk_score, 1),
            predicted_cases_7d=pred.total_predicted,
            percent_change=pred.percent_change or 0,
            color_hex=get_danger_color(danger_level),
            radius_meters=coords.get("radius", 40000)
        )
        danger_zones.append(zone)
    
    # Sort by risk score (highest first)
    danger_zones.sort(key=lambda x: x.risk_score, reverse=True)
    
    return DangerZonesResponse(
        danger_zones=danger_zones,
        legend={
            "low": {"color": settings.danger_color_low, "label": "Low Risk (0-25)"},
            "moderate": {"color": settings.danger_color_moderate, "label": "Moderate Risk (25-50)"},
            "high": {"color": settings.danger_color_high, "label": "High Risk (50-75)"},
            "critical": {"color": settings.danger_color_critical, "label": "Critical Risk (75-100)"}
        },
        generated_at=datetime.now(UTC)
    )


@router.get(
    "/geojson",
    summary="Get Danger Zones as GeoJSON",
    description="Get danger zones in GeoJSON format for direct map integration."
)
async def get_danger_zones_geojson(
    min_risk: float = Query(0, ge=0, le=100, description="Minimum risk score to include"),
    include_low_risk: bool = Query(True, description="Include low-risk zones")
):
    """
    Get danger zones in GeoJSON format.
    
    Returns a GeoJSON FeatureCollection that can be directly
    loaded into Mapbox/Leaflet maps using:
    
    ```javascript
    map.addSource('danger-zones', {
        type: 'geojson',
        data: response.data
    });
    ```
    """
    response = await get_danger_zones(min_risk=min_risk, include_low_risk=include_low_risk)
    
    features = []
    for zone in response.danger_zones:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [zone.longitude, zone.latitude]
            },
            "properties": {
                "id": zone.location_id,
                "name": zone.location_name,
                "dangerLevel": zone.danger_level.value,
                "riskScore": zone.risk_score,
                "predictedCases7d": zone.predicted_cases_7d,
                "percentChange": zone.percent_change,
                "color": zone.color_hex,
                "radius": zone.radius_meters
            }
        }
        features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "generatedAt": response.generated_at.isoformat(),
            "legend": response.legend
        }
    }
