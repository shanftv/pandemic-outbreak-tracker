"""
Prediction Service
Business logic for accessing and processing prediction data.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from api.models.schemas import (
    LocationPrediction, 
    PredictionData, 
    PredictionStatus
)
from api.config import settings, LOCATION_COORDINATES


class PredictionService:
    """Service for managing prediction data access and processing."""
    
    def __init__(self):
        self._cache = None
        self._cache_time = None
        self._cache_ttl = 300  # 5 minutes
    
    def _load_predictions(self) -> dict:
        """Load predictions from JSON file with caching."""
        now = datetime.now(timezone.utc)
        
        # Check cache validity
        if (self._cache is not None and 
            self._cache_time is not None and
            (now - self._cache_time).seconds < self._cache_ttl):
            return self._cache
        
        # Load from file
        if not settings.predictions_json.exists():
            return {}
        
        try:
            with open(settings.predictions_json, 'r') as f:
                self._cache = json.load(f)
                self._cache_time = now
                return self._cache
        except Exception:
            return {}
    
    def _calculate_trend(self, predictions: List[dict]) -> str:
        """Calculate trend based on prediction values."""
        if len(predictions) < 2:
            return "stable"
        
        first_half = sum(p["predicted_cases"] for p in predictions[:3])
        second_half = sum(p["predicted_cases"] for p in predictions[4:])
        
        diff_pct = ((second_half - first_half) / max(first_half, 1)) * 100
        
        if diff_pct > 10:
            return "increasing"
        elif diff_pct < -10:
            return "decreasing"
        else:
            return "stable"
    
    async def get_all_predictions(self) -> List[LocationPrediction]:
        """Get predictions for all locations."""
        data = self._load_predictions()
        predictions = []
        
        for location_name, preds in data.items():
            location_id = location_name.lower().replace(" ", "_")
            
            prediction_data = [
                PredictionData(
                    date=p["date"],
                    predicted_cases=p["predicted_cases"],
                    day_ahead=p["day_ahead"]
                )
                for p in preds
            ]
            
            total_predicted = sum(p["predicted_cases"] for p in preds)
            trend = self._calculate_trend(preds)
            
            location_pred = LocationPrediction(
                location_id=location_id,
                location_name=location_name,
                predictions=prediction_data,
                total_predicted=round(total_predicted, 2),
                trend=trend,
                last_7_day_actual=None,  # Would come from features data
                percent_change=None,
                generated_at=datetime.now(timezone.utc)
            )
            predictions.append(location_pred)
        
        return predictions
    
    async def get_prediction_by_location(self, location_id: str) -> Optional[LocationPrediction]:
        """Get predictions for a specific location."""
        all_predictions = await self.get_all_predictions()
        
        for pred in all_predictions:
            if pred.location_id == location_id.lower().replace(" ", "_"):
                return pred
            if pred.location_name.lower() == location_id.lower():
                return pred
        
        return None
    
    async def get_prediction_status(self) -> PredictionStatus:
        """Check prediction data freshness."""
        if not settings.predictions_json.exists():
            return PredictionStatus.UNAVAILABLE
        
        try:
            mtime = datetime.fromtimestamp(settings.predictions_json.stat().st_mtime)
            age = datetime.now(timezone.utc).replace(tzinfo=None) - mtime
            
            if age.days < 1:
                return PredictionStatus.FRESH
            else:
                return PredictionStatus.STALE
        except Exception:
            return PredictionStatus.UNAVAILABLE
    
    async def get_last_generated_time(self) -> Optional[datetime]:
        """Get the last time predictions were generated."""
        if not settings.predictions_json.exists():
            return None
        
        try:
            return datetime.fromtimestamp(settings.predictions_json.stat().st_mtime)
        except Exception:
            return None
    
    async def get_next_update_time(self) -> Optional[datetime]:
        """Get the next scheduled prediction update time."""
        last_update = await self.get_last_generated_time()
        if not last_update:
            return None
        
        # Assuming daily updates at 6 AM UTC
        next_update = last_update.replace(hour=6, minute=0, second=0, microsecond=0)
        if next_update <= datetime.now(timezone.utc).replace(tzinfo=None):
            next_update += timedelta(days=1)
        
        return next_update
    
    async def get_predictions_summary(self) -> dict:
        """Get summary statistics for all predictions."""
        predictions = await self.get_all_predictions()
        
        if not predictions:
            return {
                "total_locations": 0,
                "total_predicted_cases": 0,
                "increasing_locations": 0,
                "decreasing_locations": 0,
                "stable_locations": 0,
                "top_5_risk": []
            }
        
        total_cases = sum(p.total_predicted for p in predictions)
        increasing = sum(1 for p in predictions if p.trend == "increasing")
        decreasing = sum(1 for p in predictions if p.trend == "decreasing")
        stable = sum(1 for p in predictions if p.trend == "stable")
        
        # Sort by total predicted cases
        sorted_predictions = sorted(predictions, key=lambda x: x.total_predicted, reverse=True)
        top_5 = [
            {
                "location": p.location_name,
                "predicted_cases": p.total_predicted,
                "trend": p.trend
            }
            for p in sorted_predictions[:5]
        ]
        
        return {
            "total_locations": len(predictions),
            "total_predicted_cases": round(total_cases, 2),
            "increasing_locations": increasing,
            "decreasing_locations": decreasing,
            "stable_locations": stable,
            "top_5_risk": top_5,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_top_risk_locations(self, limit: int = 5) -> List[LocationPrediction]:
        """Get top risk locations sorted by predicted cases."""
        predictions = await self.get_all_predictions()
        sorted_predictions = sorted(predictions, key=lambda x: x.total_predicted, reverse=True)
        return sorted_predictions[:limit]
