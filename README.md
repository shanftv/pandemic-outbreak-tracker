# Pandemic Outbreak Tracker

[![Frontend application](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/frontend-app.yml/badge.svg)](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/frontend-app.yml)
[![Python application](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/python-app.yml/badge.svg)](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/python-app.yml)
[![CodeQL](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/codeql.yml/badge.svg)](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/codeql.yml)
[![Deploy to Azure](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/azure-deploy.yml/badge.svg)](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/azure-deploy.yml)
[![Quality Monitor](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/quality-monitor.yml/badge.svg)](https://github.com/shanftv/pandemic-outbreak-tracker/actions/workflows/quality-monitor.yml)

COVID-19 Philippines infection rate prediction model using LightGBM regression. Generates 7-day forecasts for top provinces based on historical case data. Includes interactive SEIRD epidemic simulations for scenario modeling.

## Features

- **7-Day Predictions**: Forecasts infection rates for the next 7 days
- **Interactive Dashboard**: React frontend with real-time map visualization
- **Danger Zone Visualization**: Color-coded risk levels using Leaflet maps
- **REST API**: FastAPI-based endpoints for frontend integration
- **Model Metrics**: Track prediction accuracy with MAE, RMSE, R²
- **Epidemic Simulations**: Interactive agent-based SEIRD simulations for scenario modeling

## Project Structure

```
pandemic-outbreak-tracker/
├── api/                    # REST API (FastAPI)
│   ├── main.py            # Application entry point
│   ├── routes/            # API endpoints
│   └── services/          # Business logic
├── frontend/              # React Dashboard (Vite + Tailwind)
│   └── src/
│       ├── components/    # UI components (Map, Stats, Controls)
│       └── pages/         # Dashboard, Simulation, About
├── scripts/               # ML pipeline scripts
├── tests/                 # API tests
├── docs/                  # Documentation
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

## Running the Application

```bash
# Start the API server (terminal 1)
uvicorn api.main:app --reload --port 8000

# Start the frontend (terminal 2)
cd frontend
npm install
npm run dev
```

- **API**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: http://localhost:5173

## API Endpoints

### Predictions & Data

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Health check |
| `GET /api/v1/locations` | Get all tracked locations |
| `GET /api/v1/predictions` | Get 7-day predictions |
| `GET /api/v1/danger-zones` | Get danger zones for map |
| `GET /api/v1/danger-zones/geojson` | GeoJSON for Mapbox/Leaflet |
| `GET /api/v1/metrics` | Model performance metrics |

### Epidemic Simulations

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/simulations` | Create new simulation |
| `GET /api/v1/simulations` | List all simulations |
| `GET /api/v1/simulations/{id}` | Get simulation state |
| `POST /api/v1/simulations/{id}/step` | Run one step |
| `POST /api/v1/simulations/{id}/run` | Run for N days |
| `GET /api/v1/simulations/{id}/stats` | Get SEIRD statistics |
| `GET /api/v1/simulations/{id}/agents` | Get agent positions |
| `DELETE /api/v1/simulations/{id}` | Delete simulation |

See [API Documentation](docs/API_DOCUMENTATION.md) for full details.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_predictions.py -v
pytest tests/test_simulations.py -v
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
- **Data Analyst**: ML model training, feature engineering, simulation engine integration
- **Web Developer**: Frontend dashboard, map visualization

## Acknowledgments

The epidemic simulation feature is based on the agent-based SEIRD model from [Simple-Epidemic](https://github.com/Acteus/Simple-Epidemic). This simulation models disease spread through a population using spatial dynamics with features including:

- Agent-based modeling with autonomous agents
- SEIRD disease progression (Susceptible → Exposed → Infected → Recovered/Deceased)
- Spatial dynamics with home attraction and random walk behavior
- Intervention modeling (vaccination, detection, isolation)
- Real-time Rt (reproduction number) tracking
