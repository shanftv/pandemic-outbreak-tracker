"""
Pytest Configuration and Fixtures
Shared fixtures for API testing.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json
import os
import tempfile
from pathlib import Path

from api.main import app
from api.config import settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_predictions():
    """Sample prediction data for testing."""
    return {
        "NCR": [
            {"date": "2025-11-29", "predicted_cases": 125.5, "day_ahead": 1},
            {"date": "2025-11-30", "predicted_cases": 130.2, "day_ahead": 2},
            {"date": "2025-12-01", "predicted_cases": 128.0, "day_ahead": 3},
            {"date": "2025-12-02", "predicted_cases": 135.5, "day_ahead": 4},
            {"date": "2025-12-03", "predicted_cases": 140.0, "day_ahead": 5},
            {"date": "2025-12-04", "predicted_cases": 138.3, "day_ahead": 6},
            {"date": "2025-12-05", "predicted_cases": 142.0, "day_ahead": 7},
        ],
        "Calabarzon": [
            {"date": "2025-11-29", "predicted_cases": 85.0, "day_ahead": 1},
            {"date": "2025-11-30", "predicted_cases": 82.5, "day_ahead": 2},
            {"date": "2025-12-01", "predicted_cases": 80.0, "day_ahead": 3},
            {"date": "2025-12-02", "predicted_cases": 78.5, "day_ahead": 4},
            {"date": "2025-12-03", "predicted_cases": 75.0, "day_ahead": 5},
            {"date": "2025-12-04", "predicted_cases": 73.0, "day_ahead": 6},
            {"date": "2025-12-05", "predicted_cases": 70.0, "day_ahead": 7},
        ],
    }


@pytest.fixture
def mock_predictions_file(sample_predictions, tmp_path):
    """Create a temporary predictions file for testing."""
    predictions_file = tmp_path / "predictions.json"
    with open(predictions_file, 'w') as f:
        json.dump(sample_predictions, f)
    
    # Temporarily override settings
    original_path = settings.predictions_json
    settings.predictions_json = predictions_file
    
    yield predictions_file
    
    # Restore original setting
    settings.predictions_json = original_path


@pytest.fixture
def sample_metrics_csv(tmp_path):
    """Create a temporary metrics CSV for testing."""
    metrics_content = """location,val_mae,val_rmse,test_mae,test_rmse,test_r2,n_estimators
NCR,15.2,22.5,18.3,25.1,0.85,150
Calabarzon,12.8,19.3,14.5,21.2,0.88,145
Central Visayas,18.5,26.2,20.1,28.5,0.82,160
"""
    metrics_file = tmp_path / "metrics.csv"
    metrics_file.write_text(metrics_content)
    
    # Temporarily override settings
    original_path = settings.metrics_csv
    settings.metrics_csv = metrics_file
    
    yield metrics_file
    
    # Restore original setting
    settings.metrics_csv = original_path
