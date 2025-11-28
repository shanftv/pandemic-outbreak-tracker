# Pandemic Outbreak Tracker API Documentation

## Overview

This REST API provides disease outbreak predictions, visualization data, and epidemic simulations for the Pandemic Outbreak Tracker dashboard. It's designed to serve the frontend application with data for interactive map visualizations, prediction charts, and agent-based epidemic simulations.

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
| POST | `/simulations` | Create new epidemic simulation |
| GET | `/simulations` | List all simulations |
| GET | `/simulations/{id}` | Get simulation state |
| POST | `/simulations/{id}/step` | Run one simulation step |
| POST | `/simulations/{id}/run` | Run simulation for N steps/days |
| GET | `/simulations/{id}/stats` | Get SEIRD statistics |
| GET | `/simulations/{id}/agents` | Get agent positions for visualization |
| DELETE | `/simulations/{id}` | Delete simulation |

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

### Simulations

The simulation endpoints allow you to run interactive SEIRD (Susceptible-Exposed-Infected-Recovered-Deceased) epidemic simulations with agent-based modeling.

#### `POST /api/v1/simulations`

Create a new epidemic simulation.

**Request Body:**
```json
{
  "population_size": 200,
  "grid_size": 100.0,
  "initial_infected": 1,
  "infection_rate": 1.0,
  "incubation_mean": 5.0,
  "incubation_std": 2.0,
  "infectious_mean": 7.0,
  "infectious_std": 3.0,
  "mortality_rate": 0.02,
  "vaccination_rate": 0.0,
  "detection_probability": 0.0,
  "isolation_compliance": 0.8,
  "home_attraction": 0.05,
  "random_movement": 1.0,
  "time_step": 0.5
}
```

All fields are optional and have sensible defaults.

**Configuration Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `population_size` | int | 200 | 10-2000 | Number of agents |
| `grid_size` | float | 100.0 | 20-500 | Simulation world size |
| `initial_infected` | int | 1 | 1-50 | Starting infected count |
| `infection_rate` | float | 1.0 | 0-5 | Transmission rate (β) |
| `incubation_mean` | float | 5.0 | 1-14 | Mean incubation period (days) |
| `incubation_std` | float | 2.0 | 0.1-5 | Std dev of incubation |
| `infectious_mean` | float | 7.0 | 1-21 | Mean infectious period (days) |
| `infectious_std` | float | 3.0 | 0.1-7 | Std dev of infectious period |
| `mortality_rate` | float | 0.02 | 0-0.5 | Case fatality rate |
| `vaccination_rate` | float | 0.0 | 0-0.1 | Daily vaccination rate |
| `detection_probability` | float | 0.0 | 0-1 | Case detection rate |
| `isolation_compliance` | float | 0.8 | 0-1 | Isolation adherence |
| `home_attraction` | float | 0.05 | 0-0.5 | Pull towards home location |
| `random_movement` | float | 1.0 | 0-3 | Random walk intensity |
| `time_step` | float | 0.5 | 0.1-1 | Simulation time step |

**Response (201):**
```json
{
  "simulation_id": "sim_abc123def456",
  "status": "created",
  "message": "Simulation created successfully. Use POST /step or /run to advance.",
  "config": { ... },
  "created_at": "2025-11-28T12:00:00Z"
}
```

#### `GET /api/v1/simulations`

List all active simulations.

**Response:**
```json
{
  "simulations": [
    {
      "simulation_id": "sim_abc123",
      "status": "running",
      "current_day": 15.5,
      "total_steps": 31,
      "config": { ... },
      "stats": { ... },
      "created_at": "2025-11-28T12:00:00Z",
      "last_updated": "2025-11-28T12:05:00Z"
    }
  ],
  "count": 1
}
```

#### `GET /api/v1/simulations/{simulation_id}`

Get the current state of a simulation.

**Response:**
```json
{
  "simulation_id": "sim_abc123",
  "status": "running",
  "current_day": 15.5,
  "total_steps": 31,
  "config": { ... },
  "stats": {
    "susceptible": 150,
    "exposed": 10,
    "infected": 25,
    "recovered": 13,
    "deceased": 2,
    "current_rt": 1.8,
    "susceptible_history": [199, 198, ...],
    "exposed_history": [0, 1, ...],
    "infected_history": [1, 1, ...],
    "recovered_history": [0, 0, ...],
    "deceased_history": [0, 0, ...],
    "rt_history": [0.0, 2.1, ...]
  },
  "created_at": "2025-11-28T12:00:00Z",
  "last_updated": "2025-11-28T12:05:00Z"
}
```

#### `POST /api/v1/simulations/{simulation_id}/step`

Run one simulation time step.

**Response:** Returns updated `SimulationState` (same as GET)

#### `POST /api/v1/simulations/{simulation_id}/run`

Run simulation for multiple steps or days.

**Request Body:**
```json
{
  "steps": 100,
  "days": null,
  "stop_when_no_infected": true
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `steps` | int | Number of steps to run (1-10000) |
| `days` | float | Number of days to simulate (0.1-365) |
| `stop_when_no_infected` | bool | Stop when epidemic ends (default: true) |

Specify either `steps` or `days`, not both. If neither specified, runs for 100 days.

**Response:** Returns updated `SimulationState`

#### `GET /api/v1/simulations/{simulation_id}/stats`

Get detailed SEIRD statistics.

**Response:**
```json
{
  "susceptible": 150,
  "exposed": 10,
  "infected": 25,
  "recovered": 13,
  "deceased": 2,
  "susceptible_history": [199, 198, 197, ...],
  "exposed_history": [0, 1, 2, ...],
  "infected_history": [1, 1, 2, ...],
  "recovered_history": [0, 0, 0, ...],
  "deceased_history": [0, 0, 0, ...],
  "current_rt": 1.8,
  "rt_history": [0.0, 2.1, 1.9, ...]
}
```

#### `GET /api/v1/simulations/{simulation_id}/agents`

Get agent positions for visualization.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_deceased` | bool | true | Include deceased agents |

**Response:**
```json
{
  "simulation_id": "sim_abc123",
  "current_day": 15.5,
  "grid_size": 100.0,
  "agents": [
    {
      "id": 0,
      "x": 45.2,
      "y": 67.8,
      "state": "S",
      "days_in_state": 15.5,
      "is_isolated": false
    },
    {
      "id": 1,
      "x": 23.1,
      "y": 89.4,
      "state": "I",
      "days_in_state": 3.0,
      "is_isolated": false
    }
  ],
  "state_colors": {
    "S": "#3498db",
    "E": "#f1c40f",
    "I": "#e74c3c",
    "R": "#2ecc71",
    "D": "#34495e"
  }
}
```

**Agent States:**
| State | Color | Description |
|-------|-------|-------------|
| S | Blue (#3498db) | Susceptible - Can be infected |
| E | Yellow (#f1c40f) | Exposed - Infected but not yet infectious |
| I | Red (#e74c3c) | Infected - Infectious and can spread disease |
| R | Green (#2ecc71) | Recovered - Immune |
| D | Grey (#34495e) | Deceased |

#### `DELETE /api/v1/simulations/{simulation_id}`

Delete a simulation.

**Response:** 204 No Content

---

### Simulation Visualization Example

```javascript
// Create simulation
const response = await fetch('http://localhost:8000/api/v1/simulations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    population_size: 300,
    infection_rate: 1.5,
    mortality_rate: 0.03
  })
});
const { simulation_id } = await response.json();

// Run simulation step by step for animation
async function animate() {
  const stepResponse = await fetch(
    `http://localhost:8000/api/v1/simulations/${simulation_id}/step`,
    { method: 'POST' }
  );
  const state = await stepResponse.json();
  
  // Get agent positions
  const agentsResponse = await fetch(
    `http://localhost:8000/api/v1/simulations/${simulation_id}/agents`
  );
  const { agents, state_colors, grid_size } = await agentsResponse.json();
  
  // Render agents on canvas
  agents.forEach(agent => {
    ctx.fillStyle = state_colors[agent.state];
    ctx.beginPath();
    ctx.arc(
      agent.x / grid_size * canvas.width,
      agent.y / grid_size * canvas.height,
      5, 0, Math.PI * 2
    );
    ctx.fill();
  });
  
  // Continue if simulation not complete
  if (state.status !== 'completed') {
    requestAnimationFrame(animate);
  }
}

animate();
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
pytest tests/test_simulations.py -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```
