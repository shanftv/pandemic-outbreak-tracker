"""
API Configuration
Centralized configuration management for the API.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Settings
    app_name: str = "Pandemic Outbreak Tracker API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS Settings (for frontend access)
    cors_origins: list = ["*"]  # Configure for production
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Data Paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    models_dir: Path = data_dir / "models"
    predictions_json: Path = data_dir / "predictions" / "predictions.json"
    predictions_csv: Path = data_dir / "predictions" / "predictions.csv"
    features_csv: Path = data_dir / "processed" / "features.csv"
    metrics_csv: Path = data_dir / "models" / "metrics.csv"
    
    # Model Settings
    prediction_horizon: int = 7  # Days to forecast
    
    # Danger Zone Thresholds
    danger_low_threshold: float = 25.0
    danger_moderate_threshold: float = 50.0
    danger_high_threshold: float = 75.0
    
    # Danger Zone Colors
    danger_color_low: str = "#4CAF50"       # Green
    danger_color_moderate: str = "#FFC107"  # Yellow
    danger_color_high: str = "#FF9800"      # Orange
    danger_color_critical: str = "#F44336"  # Red
    
    model_config = ConfigDict(
        env_prefix="PANDEMIC_API_",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()


# Philippine province coordinates (sample data)
# In production, this would come from a database
LOCATION_COORDINATES = {
    "NCR": {"latitude": 14.5995, "longitude": 120.9842, "radius": 30000},
    "Calabarzon": {"latitude": 14.1008, "longitude": 121.0794, "radius": 50000},
    "Central Visayas": {"latitude": 10.3157, "longitude": 123.8854, "radius": 40000},
    "Central Luzon": {"latitude": 15.4755, "longitude": 120.5963, "radius": 50000},
    "Western Visayas": {"latitude": 10.7202, "longitude": 122.5621, "radius": 45000},
    "Davao Region": {"latitude": 7.0731, "longitude": 125.6128, "radius": 45000},
    "Northern Mindanao": {"latitude": 8.4542, "longitude": 124.6319, "radius": 40000},
    "Zamboanga Peninsula": {"latitude": 6.9214, "longitude": 122.0790, "radius": 40000},
    "Ilocos Region": {"latitude": 16.0832, "longitude": 120.6200, "radius": 45000},
    "Bicol Region": {"latitude": 13.1391, "longitude": 123.7438, "radius": 40000},
}
