"""
Location Service
Business logic for accessing location data.
"""

from datetime import datetime, UTC
from typing import List, Optional
import pandas as pd
from api.models.schemas import LocationInfo
from api.config import settings, LOCATION_COORDINATES


class LocationService:
    """Service for managing location data access."""
    
    def __init__(self):
        self._cache = None
        self._cache_time = None
        self._cache_ttl = 600  # 10 minutes
    
    def _load_locations(self) -> pd.DataFrame:
        """Load location data from features CSV."""
        now = datetime.now(UTC)
        
        # Check cache
        if (self._cache is not None and 
            self._cache_time is not None and
            (now - self._cache_time).seconds < self._cache_ttl):
            return self._cache
        
        if not settings.features_csv.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(settings.features_csv, parse_dates=['date'])
            self._cache = df
            self._cache_time = now
            return df
        except Exception:
            return pd.DataFrame()
    
    async def get_all_locations(self, include_coordinates: bool = True) -> List[LocationInfo]:
        """Get all tracked locations."""
        df = self._load_locations()
        
        if df.empty:
            # Return sample data if no data available
            return self._get_sample_locations(include_coordinates)
        
        locations = []
        
        for location_name in df['location'].unique():
            loc_data = df[df['location'] == location_name]
            total_cases = int(loc_data['new_cases'].sum())
            last_date = loc_data['date'].max()
            
            location_id = location_name.lower().replace(" ", "_")
            coords = LOCATION_COORDINATES.get(location_name, {})
            
            location = LocationInfo(
                id=location_id,
                name=location_name,
                total_cases=total_cases,
                last_updated=last_date.to_pydatetime() if pd.notna(last_date) else datetime.now(UTC),
                latitude=coords.get("latitude") if include_coordinates else None,
                longitude=coords.get("longitude") if include_coordinates else None
            )
            locations.append(location)
        
        # Sort by total cases descending
        locations.sort(key=lambda x: x.total_cases, reverse=True)
        return locations
    
    async def get_location_by_id(self, location_id: str) -> Optional[LocationInfo]:
        """Get a specific location by ID."""
        locations = await self.get_all_locations()
        
        for loc in locations:
            if loc.id == location_id.lower():
                return loc
            if loc.name.lower() == location_id.lower():
                return loc
        
        return None
    
    def _get_sample_locations(self, include_coordinates: bool) -> List[LocationInfo]:
        """Return sample locations when no data is available."""
        sample_locations = []
        
        for name, coords in LOCATION_COORDINATES.items():
            location = LocationInfo(
                id=name.lower().replace(" ", "_"),
                name=name,
                total_cases=0,
                last_updated=datetime.now(UTC),
                latitude=coords["latitude"] if include_coordinates else None,
                longitude=coords["longitude"] if include_coordinates else None
            )
            sample_locations.append(location)
        
        return sample_locations
