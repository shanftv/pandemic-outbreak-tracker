# Pandemic Outbreak Tracker

COVID-19 Philippines infection rate prediction model using LightGBM regression. Generates 7-day forecasts for top provinces based on historical case data.

## Features

- **7-Day Predictions**: Forecasts infection rates for the next 7 days
- **Danger Zone Visualization**: Color-coded risk levels for map integration
- **REST API**: FastAPI-based endpoints for frontend integration
- **Model Metrics**: Track prediction accuracy with MAE, RMSE, R²

## Project Structure

```
pandemic-outbreak-tracker/
├── api/                    # REST API (FastAPI)
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration settings
│   ├── models/            # Pydantic schemas
│   │   └── schemas.py     # Request/Response models
│   ├── routes/            # API endpoints
│   │   ├── health.py      # Health checks
│   │   ├── locations.py   # Location data
│   │   ├── predictions.py # Prediction endpoints
│   │   ├── danger_zones.py# Map visualization data
│   │   └── metrics.py     # Model metrics
│   └── services/          # Business logic
│       ├── prediction_service.py
│       └── location_service.py
├── scripts/               # ML pipeline scripts
│   ├── prep.py           # Data preparation
│   ├── features.py       # Feature engineering
│   ├── train.py          # Model training
│   └── predict.py        # Generate predictions
├── tests/                 # API tests
│   ├── conftest.py       # Test fixtures
│   ├── test_health.py
│   ├── test_locations.py
│   ├── test_predictions.py
│   ├── test_danger_zones.py
│   ├── test_metrics.py
│   └── test_integration.py
├── docs/                  # Documentation
│   └── API_DOCUMENTATION.md
├── notebooks/             # Jupyter notebooks
└── data/                  # Data files (git-ignored)
```

## Installation

```bash
# Clone the repository
git clone https://github.com/shanftv/pandemic-outbreak-tracker.git
cd pandemic-outbreak-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the API

```bash
# Start the API server
uvicorn api.main:app --reload --port 8000

# API will be available at:
# - http://localhost:8000/docs (Swagger UI)
# - http://localhost:8000/redoc (ReDoc)
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Health check |
| `GET /api/v1/locations` | Get all tracked locations |
| `GET /api/v1/predictions` | Get 7-day predictions |
| `GET /api/v1/danger-zones` | Get danger zones for map |
| `GET /api/v1/danger-zones/geojson` | GeoJSON for Mapbox/Leaflet |
| `GET /api/v1/metrics` | Model performance metrics |

See [API Documentation](docs/API_DOCUMENTATION.md) for full details.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_predictions.py -v
```

## For Web Developers

Quick example for map integration:

```javascript
// Fetch danger zones for Mapbox/Leaflet
fetch('http://localhost:8000/api/v1/danger-zones/geojson')
  .then(response => response.json())
  .then(data => {
    // data is a GeoJSON FeatureCollection
    map.addSource('danger-zones', { type: 'geojson', data });
  });
```

## Team Roles

- **Cloud Engineer**: API development, scheduled jobs, database updates
- **Data Analyst**: ML model training, feature engineering
- **Web Developer**: Frontend dashboard, map visualization

