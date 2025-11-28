"""
Tests for Metrics Endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestMetricsEndpoints:
    """Test suite for metrics endpoints."""
    
    def test_get_all_metrics_no_data(self, client):
        """Test metrics endpoint when no data available."""
        response = client.get("/api/v1/metrics")
        
        # Should return 503 if metrics file doesn't exist
        assert response.status_code in [200, 503]
    
    def test_get_all_metrics(self, client, sample_metrics_csv):
        """Test retrieving all model metrics."""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "metrics" in data
        assert "average_mae" in data
        assert "average_r2" in data
        assert "last_training" in data
    
    def test_metrics_structure(self, client, sample_metrics_csv):
        """Test individual metric structure."""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        for metric in data["metrics"]:
            assert "location" in metric
            assert "validation_mae" in metric
            assert "validation_rmse" in metric
            assert "test_mae" in metric
            assert "test_rmse" in metric
            assert "test_r2" in metric
            assert "n_estimators" in metric
    
    def test_metrics_values_positive(self, client, sample_metrics_csv):
        """Test that error metrics are positive."""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        for metric in data["metrics"]:
            assert metric["validation_mae"] >= 0
            assert metric["validation_rmse"] >= 0
            assert metric["test_mae"] >= 0
            assert metric["test_rmse"] >= 0
            assert metric["n_estimators"] > 0
    
    def test_r2_score_range(self, client, sample_metrics_csv):
        """Test that R² scores are in valid range."""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        for metric in data["metrics"]:
            # R² can be negative for very bad models, but typically between 0 and 1
            assert metric["test_r2"] <= 1.0
    
    def test_get_location_metrics(self, client, sample_metrics_csv):
        """Test retrieving metrics for specific location."""
        response = client.get("/api/v1/metrics/location/NCR")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["location"] == "NCR"
        assert "validation_mae" in data
        assert "test_r2" in data
    
    def test_get_location_metrics_case_insensitive(self, client, sample_metrics_csv):
        """Test that location lookup is case insensitive."""
        response = client.get("/api/v1/metrics/location/ncr")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["location"].upper() == "NCR"
    
    def test_get_location_metrics_not_found(self, client, sample_metrics_csv):
        """Test metrics for non-existent location."""
        response = client.get("/api/v1/metrics/location/nonexistent")
        
        assert response.status_code == 404


class TestMetricsAggregation:
    """Test suite for metrics aggregation."""
    
    def test_average_mae_calculation(self, client, sample_metrics_csv):
        """Test that average MAE is calculated correctly."""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Calculate expected average
        maes = [m["test_mae"] for m in data["metrics"]]
        expected_avg = sum(maes) / len(maes)
        
        # Allow for small floating point differences
        assert abs(data["average_mae"] - expected_avg) < 0.1
    
    def test_average_r2_calculation(self, client, sample_metrics_csv):
        """Test that average R² is calculated correctly."""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Calculate expected average
        r2s = [m["test_r2"] for m in data["metrics"]]
        expected_avg = sum(r2s) / len(r2s)
        
        # Allow for small floating point differences
        assert abs(data["average_r2"] - expected_avg) < 0.01
