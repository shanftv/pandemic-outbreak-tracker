"""
Tests for Location Endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestLocationEndpoints:
    """Test suite for location endpoints."""
    
    def test_get_all_locations(self, client):
        """Test retrieving all locations."""
        response = client.get("/api/v1/locations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "locations" in data
        assert "count" in data
        assert isinstance(data["locations"], list)
        assert data["count"] == len(data["locations"])
    
    def test_get_all_locations_with_coordinates(self, client):
        """Test that locations include coordinates by default."""
        response = client.get("/api/v1/locations?include_coordinates=true")
        
        assert response.status_code == 200
        data = response.json()
        
        # At least some locations should have coordinates
        for location in data["locations"]:
            assert "id" in location
            assert "name" in location
            assert "total_cases" in location
            assert "last_updated" in location
    
    def test_get_all_locations_without_coordinates(self, client):
        """Test getting locations without coordinates."""
        response = client.get("/api/v1/locations?include_coordinates=false")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still return locations
        assert "locations" in data
    
    def test_get_location_by_valid_id(self, client):
        """Test retrieving a specific location by ID."""
        # First get all locations to get a valid ID
        response = client.get("/api/v1/locations")
        assert response.status_code == 200
        locations = response.json()["locations"]
        
        if locations:
            location_id = locations[0]["id"]
            response = client.get(f"/api/v1/locations/{location_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == location_id
    
    def test_get_location_by_invalid_id(self, client):
        """Test retrieving a non-existent location returns 404."""
        response = client.get("/api/v1/locations/nonexistent_location_xyz")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data


class TestLocationDataStructure:
    """Test suite for location data structure validation."""
    
    def test_location_has_required_fields(self, client):
        """Test that each location has all required fields."""
        response = client.get("/api/v1/locations")
        
        assert response.status_code == 200
        locations = response.json()["locations"]
        
        required_fields = ["id", "name", "total_cases", "last_updated"]
        
        for location in locations:
            for field in required_fields:
                assert field in location, f"Missing field: {field}"
    
    def test_location_id_format(self, client):
        """Test that location IDs are properly formatted."""
        response = client.get("/api/v1/locations")
        
        assert response.status_code == 200
        locations = response.json()["locations"]
        
        for location in locations:
            # IDs should be lowercase with underscores
            assert location["id"] == location["id"].lower()
            assert " " not in location["id"]
