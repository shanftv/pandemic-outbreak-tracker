# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

COVID-19 Philippines outbreak tracker with 7-day infection rate predictions using LightGBM regression. Includes FastAPI REST API for frontend integration and interactive SEIRD epidemic simulations for scenario modeling.

## Common Commands

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API
```bash
# Start API server (development with auto-reload)
uvicorn api.main:app --reload --port 8000

# Start API server (production)
uvicorn api.main:app --host 0.0.0.0 --port 8000

# API documentation available at:
# - http://localhost:8000/docs (Swagger UI)
# - http://localhost:8000/redoc (ReDoc)
```

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_predictions.py -v

# Run specific test function
pytest tests/test_predictions.py::test_get_all_predictions -v

# Run only simulation tests
pytest tests/test_simulations.py -v

# Run tests matching pattern
pytest -k "prediction" -v
```

### Linting
```bash
# Run flake8 linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### ML Pipeline
```bash
# Run full pipeline (download data, train, predict)
python scripts/full_pipeline.py

# Skip data download (use existing data)
python scripts/full_pipeline.py --skip-download

# Train models for top N locations only
python scripts/full_pipeline.py --top-n 5

# Individual pipeline steps
python scripts/prep.py data/Case_Information.csv data/cleaned_ph_covid.csv
python scripts/features.py data/cleaned_ph_covid.csv data/features_ph_covid.csv
python scripts/train.py data/features_ph_covid.csv models/ reports/metrics.csv
python scripts/predict.py models/ data/features_ph_covid.csv predictions.json predictions.csv
```

## Architecture

### API Layer (FastAPI)
The API follows a clean layered architecture:

**Routes** (`api/routes/`) → Handle HTTP requests/responses, validation
- Each route file corresponds to a domain (predictions, locations, danger_zones, simulations)
- Use Pydantic schemas for request/response validation
- Routes should be thin and delegate business logic to services

**Services** (`api/services/`) → Business logic and data access
- `prediction_service.py`: Loads and processes prediction data from JSON
- `location_service.py`: Manages location metadata and coordinates
- Services implement caching (TTL: 5 minutes) to reduce file I/O
- All services use async methods for consistency

**Models** (`api/models/schemas.py`) → Pydantic data models
- Define all request/response schemas
- Includes validation rules and field descriptions
- Used for OpenAPI documentation generation

**Config** (`api/config.py`) → Centralized settings
- Uses Pydantic Settings with environment variable support
- Prefix: `PANDEMIC_API_` (e.g., `PANDEMIC_API_DEBUG=true`)
- Contains location coordinates, danger zone thresholds, and colors
- All paths are relative to project root via `settings.project_root`

### ML Pipeline (scripts/)
Sequential pipeline for model training and predictions:

1. **prep.py**: Data cleaning and standardization
   - Filters Philippines COVID-19 case data by date
   - Aggregates by location and date
   - Outputs cleaned CSV

2. **features.py**: Feature engineering
   - Creates lag features (1, 3, 7 days)
   - Rolling window features (3, 7, 14 days): mean, std, min, max
   - Temporal features: day_of_week, month, week_of_year, days_since_start
   - Outputs features CSV

3. **train.py**: LightGBM model training
   - Trains separate models for each location
   - Train/validation/test split with temporal ordering
   - Early stopping on validation MAE
   - Saves models as joblib files: `lgb_{location}.pkl`
   - Outputs metrics CSV with MAE, RMSE, R²

4. **predict.py**: 7-day forecast generation
   - Recursive prediction: uses previous predictions as lag features
   - Generates predictions for 7 days ahead
   - Outputs JSON and CSV files

5. **full_pipeline.py**: End-to-end orchestration
   - Downloads latest data from Kaggle
   - Runs all pipeline steps sequentially
   - Designed for cron job execution
   - Logs to `pipeline.log`

### Data Flow
```
Kaggle Dataset (Case_Information.csv)
    ↓ prep.py
Cleaned Data (cleaned_ph_covid.csv)
    ↓ features.py
Feature Matrix (features_ph_covid.csv)
    ↓ train.py
Trained Models (models/*.pkl) + Metrics (metrics.csv)
    ↓ predict.py
Predictions (predictions.json, predictions.csv)
    ↓ API Services
REST API Endpoints
    ↓
Frontend/Clients
```

### Simulation System (Partially Implemented)
The API endpoints for epidemic simulations are **complete and tested**, but use a mock simulation engine:

**Current State**:
- All simulation endpoints implemented in `api/routes/simulations.py`
- Mock `SimulationStore` class for testing
- 36 passing tests in `tests/test_simulations.py`

**Integration Needed** (Data Analyst):
- Copy SEIRD simulation engine from Simple-Epidemic project
- Create `api/services/simulation_service.py` wrapper
- Replace mock in `simulations.py` with actual engine
- See `docs/SIMULATION_INTEGRATION.md` for detailed instructions

**Simulation Storage**:
- Currently in-memory (dictionary)
- For production, consider Redis or database
- Each simulation has unique ID: `sim_{12-char-hex}`

## Testing Guidelines

### Fixture Pattern
Use shared fixtures from `tests/conftest.py`:
- `client`: TestClient for API requests
- `sample_predictions`: Mock prediction data
- `mock_predictions_file`: Temporary file with test data
- `sample_metrics_csv`: Mock metrics data

### Testing Async Endpoints
```python
def test_async_endpoint(client):
    response = client.get("/api/v1/predictions")
    assert response.status_code == 200
```

### Testing with Temporary Files
```python
def test_with_file(mock_predictions_file):
    # settings.predictions_json is automatically mocked
    # and restored after test completes
    pass
```

## Project-Specific Conventions

### Location Naming
- Database/file keys: spaces and slashes converted to underscores
  - Example: `"NCR"` → `"ncr"`, `"Central Visayas"` → `"central_visayas"`
- API responses: use full display names from `LOCATION_COORDINATES`
- Model files: safe names with underscores (`lgb_NCR.pkl`)

### Date Handling
- All API timestamps use UTC timezone
- Prediction files: ISO 8601 format (`YYYY-MM-DD`)
- Model training: temporal ordering must be preserved
- Predictions: always 7 days ahead from latest available data

### CORS Configuration
- Default: allows all origins (`["*"]`) for development
- Production: configure via environment variables
  ```bash
  PANDEMIC_API_CORS_ORIGINS='["https://yourdomain.com"]'
  ```

### Danger Zone Classification
Risk levels based on 7-day predicted cases:
- **Low** (<25): Green (#4CAF50)
- **Moderate** (25-50): Yellow (#FFC107)
- **High** (50-75): Orange (#FF9800)
- **Critical** (>75): Red (#F44336)

Configure thresholds in `api/config.py` or via environment variables.

### Model Refresh Schedule
- Production: Daily at 6:00 AM UTC via cron job
- Pipeline downloads latest Kaggle data
- Retrains models on updated data
- Regenerates 7-day predictions
- API auto-detects new files (cache TTL: 5 minutes)

## CI/CD

GitHub Actions workflow (`.github/workflows/python-app.yml`):
- Triggers on push/PR to `main` branch
- Python 3.10
- Installs dependencies from requirements.txt
- Runs flake8 linting
- Runs pytest test suite
- All tests must pass before merge

## Data Dependencies

### Required Files (Generated by Pipeline)
- `data/predictions/predictions.json`: 7-day forecasts for API
- `data/predictions/predictions.csv`: Same data in CSV format
- `data/models/metrics.csv`: Model performance metrics
- `data/processed/features.csv`: Feature matrix (used by API for metadata)

### File Locations (Relative to Project Root)
Paths are defined in `api/config.py` via `settings`:
```python
settings.data_dir              # data/
settings.models_dir            # data/models/
settings.predictions_json      # data/predictions/predictions.json
settings.predictions_csv       # data/predictions/predictions.csv
settings.features_csv          # data/processed/features.csv
settings.metrics_csv           # data/models/metrics.csv
```

## Notes for AI Agents

- When modifying API endpoints, always update corresponding Pydantic schemas
- Keep routes thin; move complex logic to services
- Test files mirror the structure of `api/routes/`
- When adding new locations, update `LOCATION_COORDINATES` in `api/config.py`
- Pipeline scripts log to stdout and `pipeline.log` simultaneously
- Mock simulation will be replaced with real engine - check `docs/SIMULATION_INTEGRATION.md`
- GeoJSON endpoint (`/danger-zones/geojson`) is optimized for Mapbox/Leaflet integration
