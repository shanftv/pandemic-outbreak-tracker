"""
Tests for Health Check Endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    def test_health_check(self, client):
        """Test the main health check endpoint."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "model_status" in data
        
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
    
    def test_health_check_returns_timestamp(self, client):
        """Test that health check returns a valid timestamp."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Timestamp should be parseable
        assert "timestamp" in data
        assert "T" in data["timestamp"]  # ISO format check
    
    def test_readiness_check(self, client):
        """Test the readiness check endpoint."""
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ready" in data
        assert "checks" in data
        assert "timestamp" in data
        
        # Checks should be a dict
        assert isinstance(data["checks"], dict)


class TestRootEndpoint:
    """Test suite for root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        
        assert data["name"] == "Pandemic Outbreak Tracker API"
        assert data["docs"] == "/docs"
