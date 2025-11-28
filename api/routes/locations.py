"""
Locations Router
Endpoints for retrieving tracked location information.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from api.models.schemas import LocationsResponse, LocationInfo, ErrorResponse
from api.services.location_service import LocationService


router = APIRouter(prefix="/locations", tags=["Locations"])

# Service instance
location_service = LocationService()


@router.get(
    "",
    response_model=LocationsResponse,
    summary="Get All Locations",
    description="Retrieve list of all tracked locations with case data.",
    responses={
        200: {"description": "List of locations retrieved successfully"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def get_all_locations(
    include_coordinates: bool = Query(
        True, 
        description="Include latitude/longitude in response"
    )
) -> LocationsResponse:
    """
    Get all tracked locations.
    
    Returns a list of all locations being tracked, including:
    - Location ID and name
    - Total historical cases
    - Last update timestamp
    - Coordinates (optional)
    """
    locations = await location_service.get_all_locations(include_coordinates)
    return LocationsResponse(
        locations=locations,
        count=len(locations)
    )


@router.get(
    "/{location_id}",
    response_model=LocationInfo,
    summary="Get Location by ID",
    description="Retrieve details for a specific location.",
    responses={
        200: {"description": "Location found"},
        404: {"description": "Location not found", "model": ErrorResponse}
    }
)
async def get_location(location_id: str) -> LocationInfo:
    """
    Get a specific location by ID.
    
    Args:
        location_id: Unique identifier for the location (e.g., "ncr")
    
    Returns:
        Location information including name, total cases, and coordinates.
    """
    location = await location_service.get_location_by_id(location_id)
    
    if not location:
        raise HTTPException(
            status_code=404,
            detail=f"Location not found: {location_id}"
        )
    
    return location
