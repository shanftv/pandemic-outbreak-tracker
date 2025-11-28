"""
Tests for Danger Zone Endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestDangerZoneEndpoints:
    """Test suite for danger zone endpoints."""
    
    def test_get_danger_zones(self, client):
        """Test retrieving all danger zones."""
        response = client.get("/api/v1/danger-zones")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "danger_zones" in data
        assert "legend" in data
        assert "generated_at" in data
    
    def test_danger_zone_structure(self, client, mock_predictions_file):
        """Test danger zone data structure."""
        response = client.get("/api/v1/danger-zones")
        
        assert response.status_code == 200
        data = response.json()
        
        for zone in data["danger_zones"]:
            assert "location_id" in zone
            assert "location_name" in zone
            assert "latitude" in zone
            assert "longitude" in zone
            assert "danger_level" in zone
            assert "risk_score" in zone
            assert "predicted_cases_7d" in zone
            assert "color_hex" in zone
            assert "radius_meters" in zone
    
    def test_danger_level_values(self, client, mock_predictions_file):
        """Test that danger levels are valid."""
        response = client.get("/api/v1/danger-zones")
        
        assert response.status_code == 200
        data = response.json()
        
        valid_levels = ["low", "moderate", "high", "critical"]
        
        for zone in data["danger_zones"]:
            assert zone["danger_level"] in valid_levels
    
    def test_color_hex_format(self, client, mock_predictions_file):
        """Test that colors are valid hex codes."""
        response = client.get("/api/v1/danger-zones")
        
        assert response.status_code == 200
        data = response.json()
        
        import re
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        
        for zone in data["danger_zones"]:
            assert hex_pattern.match(zone["color_hex"]), f"Invalid hex color: {zone['color_hex']}"
    
    def test_risk_score_range(self, client, mock_predictions_file):
        """Test that risk scores are within 0-100 range."""
        response = client.get("/api/v1/danger-zones")
        
        assert response.status_code == 200
        data = response.json()
        
        for zone in data["danger_zones"]:
            assert 0 <= zone["risk_score"] <= 100
    
    def test_legend_structure(self, client):
        """Test the legend structure."""
        response = client.get("/api/v1/danger-zones")
        
        assert response.status_code == 200
        data = response.json()
        
        legend = data["legend"]
        expected_levels = ["low", "moderate", "high", "critical"]
        
        for level in expected_levels:
            assert level in legend
            assert "color" in legend[level]
            assert "label" in legend[level]
    
    def test_min_risk_filter(self, client, mock_predictions_file):
        """Test filtering by minimum risk score."""
        response = client.get("/api/v1/danger-zones?min_risk=50")
        
        assert response.status_code == 200
        data = response.json()
        
        for zone in data["danger_zones"]:
            assert zone["risk_score"] >= 50
    
    def test_exclude_low_risk(self, client, mock_predictions_file):
        """Test excluding low risk zones."""
        response = client.get("/api/v1/danger-zones?include_low_risk=false")
        
        assert response.status_code == 200
        data = response.json()
        
        for zone in data["danger_zones"]:
            assert zone["danger_level"] != "low"


class TestGeoJSONEndpoint:
    """Test suite for GeoJSON endpoint."""
    
    def test_geojson_endpoint(self, client):
        """Test GeoJSON endpoint returns valid format."""
        response = client.get("/api/v1/danger-zones/geojson")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "type" in data
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert "metadata" in data
    
    def test_geojson_feature_structure(self, client, mock_predictions_file):
        """Test GeoJSON feature structure."""
        response = client.get("/api/v1/danger-zones/geojson")
        
        assert response.status_code == 200
        data = response.json()
        
        for feature in data["features"]:
            assert feature["type"] == "Feature"
            assert "geometry" in feature
            assert "properties" in feature
            
            # Check geometry
            geom = feature["geometry"]
            assert geom["type"] == "Point"
            assert "coordinates" in geom
            assert len(geom["coordinates"]) == 2  # [lon, lat]
            
            # Check properties
            props = feature["properties"]
            assert "id" in props
            assert "name" in props
            assert "dangerLevel" in props
            assert "riskScore" in props
            assert "color" in props
    
    def test_geojson_coordinates_order(self, client, mock_predictions_file):
        """Test GeoJSON uses [longitude, latitude] order."""
        response = client.get("/api/v1/danger-zones/geojson")
        
        assert response.status_code == 200
        data = response.json()
        
        for feature in data["features"]:
            coords = feature["geometry"]["coordinates"]
            lon, lat = coords
            
            # Valid longitude range: -180 to 180
            # Valid latitude range: -90 to 90
            # Philippine coordinates: around 120°E, 14°N
            assert -180 <= lon <= 180, f"Invalid longitude: {lon}"
            assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
