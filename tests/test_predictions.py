"""
Tests for Prediction Endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestPredictionEndpoints:
    """Test suite for prediction endpoints."""
    
    def test_get_all_predictions(self, client):
        """Test retrieving all predictions."""
        response = client.get("/api/v1/predictions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "predictions" in data
        assert "status" in data
        assert "generated_at" in data
        
        # Status should be one of the valid values
        valid_statuses = ["fresh", "stale", "unavailable"]
        assert data["status"] in valid_statuses
    
    def test_predictions_response_structure(self, client, mock_predictions_file):
        """Test prediction response has correct structure."""
        response = client.get("/api/v1/predictions")
        
        assert response.status_code == 200
        data = response.json()
        
        for prediction in data["predictions"]:
            assert "location_id" in prediction
            assert "location_name" in prediction
            assert "predictions" in prediction
            assert "total_predicted" in prediction
            assert "trend" in prediction
            assert "generated_at" in prediction
    
    def test_predictions_have_7_days(self, client, mock_predictions_file):
        """Test that predictions contain 7 days of data."""
        response = client.get("/api/v1/predictions")
        
        assert response.status_code == 200
        data = response.json()
        
        for prediction in data["predictions"]:
            assert len(prediction["predictions"]) == 7
            
            # Check day_ahead values are 1-7
            day_aheads = [p["day_ahead"] for p in prediction["predictions"]]
            assert sorted(day_aheads) == [1, 2, 3, 4, 5, 6, 7]
    
    def test_get_prediction_by_location(self, client, mock_predictions_file):
        """Test retrieving prediction for specific location."""
        response = client.get("/api/v1/predictions/location/ncr")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "location_id" in data
        assert "predictions" in data
        assert len(data["predictions"]) == 7
    
    def test_get_prediction_invalid_location(self, client):
        """Test retrieving prediction for non-existent location."""
        response = client.get("/api/v1/predictions/location/nonexistent_xyz")
        
        assert response.status_code == 404
    
    def test_predictions_summary(self, client):
        """Test predictions summary endpoint."""
        response = client.get("/api/v1/predictions/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_locations" in data
        assert "total_predicted_cases" in data
        assert "increasing_locations" in data
        assert "decreasing_locations" in data
        assert "stable_locations" in data
    
    def test_top_risk_locations(self, client, mock_predictions_file):
        """Test top risk locations endpoint."""
        response = client.get("/api/v1/predictions/top-risk?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of predictions
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_top_risk_locations_default_limit(self, client, mock_predictions_file):
        """Test top risk locations with default limit."""
        response = client.get("/api/v1/predictions/top-risk")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 5  # Default limit


class TestPredictionDataValidation:
    """Test suite for prediction data validation."""
    
    def test_predicted_cases_non_negative(self, client, mock_predictions_file):
        """Test that predicted cases are non-negative."""
        response = client.get("/api/v1/predictions")
        
        assert response.status_code == 200
        data = response.json()
        
        for prediction in data["predictions"]:
            for daily in prediction["predictions"]:
                assert daily["predicted_cases"] >= 0
    
    def test_trend_valid_values(self, client, mock_predictions_file):
        """Test that trend has valid values."""
        response = client.get("/api/v1/predictions")
        
        assert response.status_code == 200
        data = response.json()
        
        valid_trends = ["increasing", "decreasing", "stable"]
        
        for prediction in data["predictions"]:
            assert prediction["trend"] in valid_trends
    
    def test_date_format(self, client, mock_predictions_file):
        """Test that dates are in YYYY-MM-DD format."""
        response = client.get("/api/v1/predictions")
        
        assert response.status_code == 200
        data = response.json()
        
        import re
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        for prediction in data["predictions"]:
            for daily in prediction["predictions"]:
                assert date_pattern.match(daily["date"]), f"Invalid date format: {daily['date']}"
