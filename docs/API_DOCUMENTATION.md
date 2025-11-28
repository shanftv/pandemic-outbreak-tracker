# Pandemic Outbreak Tracker API Documentation

## Overview

This REST API provides disease outbreak predictions and visualization data for the Pandemic Outbreak Tracker dashboard. It's designed to serve the frontend application with data for interactive map visualizations and prediction charts.

**Base URL:** `http://localhost:8000/api/v1`

**API Documentation (Interactive):**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn api.main:app --reload --port 8000
```

### Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get danger zones for map
curl http://localhost:8000/api/v1/danger-zones/geojson
```

---

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness check |
| GET | `/locations` | Get all tracked locations |
| GET | `/locations/{id}` | Get specific location |
| GET | `/predictions` | Get all predictions |
| GET | `/predictions/location/{id}` | Get prediction for location |
| GET | `/predictions/summary` | Get predictions summary |
| GET | `/predictions/top-risk` | Get highest risk locations |
| GET | `/danger-zones` | Get danger zones for map |
| GET | `/danger-zones/geojson` | Get GeoJSON for Mapbox/Leaflet |
| GET | `/metrics` | Get model performance metrics |

---

## For Web Developers (Map Integration)

### 🗺️ Rendering the Map with Danger Zones

The main endpoint you'll need is `/danger-zones/geojson`. This returns a GeoJSON FeatureCollection that can be directly loaded into Mapbox or Leaflet.

#### Mapbox Example

```javascript
// Initialize map
mapboxgl.accessToken = 'YOUR_TOKEN';
const map = new mapboxgl.Map({
  container: 'map',
  style: 'mapbox://styles/mapbox/dark-v11',
  center: [121.0, 12.5], // Philippines
  zoom: 6
});

// Fetch and display danger zones
fetch('http://localhost:8000/api/v1/danger-zones/geojson')
  .then(response => response.json())
  .then(data => {
    map.addSource('danger-zones', {
      type: 'geojson',
      data: data
    });

    // Add circles for each danger zone
    map.addLayer({
      id: 'danger-zones-circles',
      type: 'circle',
      source: 'danger-zones',
      paint: {
        'circle-radius': ['/', ['get', 'radius'], 5000],
        'circle-color': ['get', 'color'],
        'circle-opacity': 0.6,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff'
      }
    });

    // Add popups on click
    map.on('click', 'danger-zones-circles', (e) => {
      const props = e.features[0].properties;
      new mapboxgl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(`
          <h3>${props.name}</h3>
          <p>Risk Score: ${props.riskScore}</p>
          <p>Danger Level: ${props.dangerLevel}</p>
          <p>Predicted (7d): ${props.predictedCases7d} cases</p>
        `)
        .addTo(map);
    });
  });
```

#### Leaflet Example

```javascript
// Initialize map
const map = L.map('map').setView([12.5, 121.0], 6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Fetch and display danger zones
fetch('http://localhost:8000/api/v1/danger-zones/geojson')
  .then(response => response.json())
  .then(data => {
    L.geoJSON(data, {
      pointToLayer: (feature, latlng) => {
        return L.circle(latlng, {
          radius: feature.properties.radius,
          fillColor: feature.properties.color,
          fillOpacity: 0.6,
          color: '#ffffff',
          weight: 2
        });
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties;
        layer.bindPopup(`
          <h3>${props.name}</h3>
          <p>Risk Score: ${props.riskScore}</p>
          <p>Danger Level: ${props.dangerLevel}</p>
          <p>Predicted (7d): ${props.predictedCases7d} cases</p>
        `);
      }
    }).addTo(map);
  });
```

---

## Endpoint Details

### Health Check

#### `GET /api/v1/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-28T12:00:00Z",
  "model_status": "loaded"
}
```

---

### Locations

#### `GET /api/v1/locations`

Get all tracked locations.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_coordinates` | boolean | `true` | Include lat/lng |

**Response:**
```json
{
  "locations": [
    {
      "id": "ncr",
      "name": "NCR",
      "total_cases": 150000,
      "last_updated": "2025-11-28T06:00:00Z",
      "latitude": 14.5995,
      "longitude": 120.9842
    }
  ],
  "count": 10
}
```

#### `GET /api/v1/locations/{location_id}`

Get a specific location.

**Response:** Single `LocationInfo` object

---

### Predictions

#### `GET /api/v1/predictions`

Get 7-day predictions for all locations.

**Response:**
```json
{
  "predictions": [
    {
      "location_id": "ncr",
      "location_name": "NCR",
      "predictions": [
        {
          "date": "2025-11-29",
          "predicted_cases": 125.5,
          "day_ahead": 1
        },
        // ... 7 days total
      ],
      "total_predicted": 875.5,
      "trend": "increasing",
      "last_7_day_actual": 800.0,
      "percent_change": 9.4,
      "generated_at": "2025-11-28T06:00:00Z"
    }
  ],
  "status": "fresh",
  "generated_at": "2025-11-28T06:00:00Z",
  "next_update": "2025-11-29T06:00:00Z"
}
```

#### `GET /api/v1/predictions/location/{location_id}`

Get predictions for a specific location.

#### `GET /api/v1/predictions/summary`

Get summary statistics.

**Response:**
```json
{
  "total_locations": 10,
  "total_predicted_cases": 5432.5,
  "increasing_locations": 4,
  "decreasing_locations": 3,
  "stable_locations": 3,
  "top_5_risk": [
    {"location": "NCR", "predicted_cases": 875.5, "trend": "increasing"}
  ]
}
```

#### `GET /api/v1/predictions/top-risk`

Get highest risk locations.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | `5` | Number of locations (1-20) |

---

### Danger Zones

#### `GET /api/v1/danger-zones`

Get danger zones for map visualization.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_risk` | float | `0` | Minimum risk score (0-100) |
| `include_low_risk` | boolean | `true` | Include low-risk zones |

**Response:**
```json
{
  "danger_zones": [
    {
      "location_id": "ncr",
      "location_name": "NCR",
      "latitude": 14.5995,
      "longitude": 120.9842,
      "danger_level": "high",
      "risk_score": 75.5,
      "predicted_cases_7d": 875.5,
      "percent_change": 15.2,
      "color_hex": "#FF9800",
      "radius_meters": 30000
    }
  ],
  "legend": {
    "low": {"color": "#4CAF50", "label": "Low Risk (0-25)"},
    "moderate": {"color": "#FFC107", "label": "Moderate Risk (25-50)"},
    "high": {"color": "#FF9800", "label": "High Risk (50-75)"},
    "critical": {"color": "#F44336", "label": "Critical Risk (75-100)"}
  },
  "generated_at": "2025-11-28T12:00:00Z"
}
```

#### `GET /api/v1/danger-zones/geojson`

Get danger zones as GeoJSON FeatureCollection.

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [120.9842, 14.5995]
      },
      "properties": {
        "id": "ncr",
        "name": "NCR",
        "dangerLevel": "high",
        "riskScore": 75.5,
        "predictedCases7d": 875.5,
        "percentChange": 15.2,
        "color": "#FF9800",
        "radius": 30000
      }
    }
  ],
  "metadata": {
    "generatedAt": "2025-11-28T12:00:00Z",
    "legend": {...}
  }
}
```

---

### Metrics

#### `GET /api/v1/metrics`

Get model performance metrics.

**Response:**
```json
{
  "metrics": [
    {
      "location": "NCR",
      "validation_mae": 15.2,
      "validation_rmse": 22.5,
      "test_mae": 18.3,
      "test_rmse": 25.1,
      "test_r2": 0.85,
      "n_estimators": 150,
      "trained_at": "2025-11-28T06:00:00Z"
    }
  ],
  "average_mae": 17.5,
  "average_r2": 0.82,
  "last_training": "2025-11-28T06:00:00Z"
}
```

---

## Color Legend for Danger Levels

| Level | Risk Score | Color | Hex Code |
|-------|-----------|-------|----------|
| 🟢 Low | 0-25 | Green | `#4CAF50` |
| 🟡 Moderate | 25-50 | Yellow | `#FFC107` |
| 🟠 High | 50-75 | Orange | `#FF9800` |
| 🔴 Critical | 75-100 | Red | `#F44336` |

---

## Data Refresh Schedule

- **Predictions are updated daily at 6:00 AM UTC**
- Check the `generated_at` field to see when data was last updated
- Check the `status` field: `fresh` (< 24h), `stale` (> 24h), `unavailable`

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Description |
|-------------|-------------|
| 404 | Resource not found |
| 422 | Validation error (invalid parameters) |
| 500 | Internal server error |
| 503 | Service unavailable (data not ready) |

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_danger_zones.py -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```
