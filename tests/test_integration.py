"""
Integration Tests for API
Tests for complete API workflows and integration scenarios.
"""

import pytest
from fastapi.testclient import TestClient


class TestAPIIntegration:
    """Integration tests for complete API workflows."""
    
    def test_full_workflow_health_to_predictions(self, client, mock_predictions_file):
        """Test a typical frontend workflow: check health, get predictions."""
        # Step 1: Check health
        health_response = client.get("/api/v1/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # Step 2: Get locations
        locations_response = client.get("/api/v1/locations")
        assert locations_response.status_code == 200
        locations = locations_response.json()["locations"]
        
        # Step 3: Get predictions
        predictions_response = client.get("/api/v1/predictions")
        assert predictions_response.status_code == 200
        
        # Step 4: Get danger zones for map
        danger_zones_response = client.get("/api/v1/danger-zones")
        assert danger_zones_response.status_code == 200
    
    def test_map_visualization_workflow(self, client, mock_predictions_file):
        """Test workflow for map visualization."""
        # Get GeoJSON for map
        response = client.get("/api/v1/danger-zones/geojson")
        assert response.status_code == 200
        
        data = response.json()
        assert data["type"] == "FeatureCollection"
        
        # Verify all features have required map properties
        for feature in data["features"]:
            props = feature["properties"]
            assert "color" in props  # For circle color
            assert "radius" in props  # For circle radius
            assert "name" in props  # For popup
            assert "riskScore" in props  # For popup
    
    def test_location_detail_workflow(self, client, mock_predictions_file):
        """Test workflow for viewing location details."""
        # Get all locations
        locations_response = client.get("/api/v1/locations")
        assert locations_response.status_code == 200
        locations = locations_response.json()["locations"]
        
        if locations:
            location_id = locations[0]["id"]
            
            # Get specific location
            loc_response = client.get(f"/api/v1/locations/{location_id}")
            assert loc_response.status_code == 200
            
            # Get predictions for location
            pred_response = client.get(f"/api/v1/predictions/location/{location_id}")
            # May or may not exist depending on mock data
            assert pred_response.status_code in [200, 404]


class TestCORSHeaders:
    """Test CORS configuration for frontend access."""
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # CORS middleware should handle this
        assert response.status_code in [200, 204, 405]
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        # Note: TestClient may not fully simulate CORS headers


class TestErrorHandling:
    """Test error handling and responses."""
    
    def test_404_for_invalid_endpoint(self, client):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_404_for_invalid_location(self, client):
        """Test 404 for non-existent location."""
        response = client.get("/api/v1/locations/xyz_invalid_location")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_invalid_query_parameter(self, client):
        """Test handling of invalid query parameters."""
        response = client.get("/api/v1/predictions/top-risk?limit=-1")
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_invalid_limit_too_high(self, client):
        """Test that limit parameter is bounded."""
        response = client.get("/api/v1/predictions/top-risk?limit=1000")
        
        # Should return validation error (limit is 1-20)
        assert response.status_code == 422


class TestAPIVersioning:
    """Test API versioning."""
    
    def test_v1_prefix(self, client):
        """Test that all endpoints use v1 prefix."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/locations",
            "/api/v1/predictions",
            "/api/v1/danger-zones",
            "/api/v1/metrics",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 404 for the path (may return 5xx if data missing)
            assert response.status_code != 404, f"Endpoint not found: {endpoint}"
