"""
Pydantic Schemas for API Request/Response Models

These schemas define the structure of data exchanged between the API
and clients (frontend applications).
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class DangerLevel(str, Enum):
    """Risk level classification for danger zones."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class PredictionStatus(str, Enum):
    """Status of prediction data freshness."""
    FRESH = "fresh"          # Updated within last 24 hours
    STALE = "stale"          # Updated more than 24 hours ago
    UNAVAILABLE = "unavailable"  # No predictions available


# ============================================================================
# Health Check Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server timestamp")
    model_status: str = Field(..., description="ML model availability status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-28T12:00:00Z",
                "model_status": "loaded"
            }
        }
    )


# ============================================================================
# Location Schemas
# ============================================================================

class LocationInfo(BaseModel):
    """Information about a tracked location."""
    id: str = Field(..., description="Unique location identifier")
    name: str = Field(..., description="Location display name")
    total_cases: int = Field(..., description="Total historical cases")
    last_updated: datetime = Field(..., description="Last data update timestamp")
    latitude: Optional[float] = Field(None, description="Location latitude")
    longitude: Optional[float] = Field(None, description="Location longitude")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ncr",
                "name": "NCR",
                "total_cases": 150000,
                "last_updated": "2025-11-28T06:00:00Z",
                "latitude": 14.5995,
                "longitude": 120.9842
            }
        }
    )


class LocationsResponse(BaseModel):
    """Response containing list of all tracked locations."""
    locations: List[LocationInfo] = Field(..., description="List of tracked locations")
    count: int = Field(..., description="Total number of locations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                "count": 1
            }
        }
    )


# ============================================================================
# Prediction Schemas
# ============================================================================

class PredictionData(BaseModel):
    """Single day prediction data."""
    date: str = Field(..., description="Prediction date (YYYY-MM-DD)")
    predicted_cases: float = Field(..., description="Predicted new cases")
    day_ahead: int = Field(..., description="Days ahead from today (1-7)")
    confidence_lower: Optional[float] = Field(None, description="Lower confidence bound")
    confidence_upper: Optional[float] = Field(None, description="Upper confidence bound")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-11-29",
                "predicted_cases": 125.5,
                "day_ahead": 1,
                "confidence_lower": 100.0,
                "confidence_upper": 150.0
            }
        }
    )


class LocationPrediction(BaseModel):
    """7-day prediction for a specific location."""
    location_id: str = Field(..., description="Location identifier")
    location_name: str = Field(..., description="Location display name")
    predictions: List[PredictionData] = Field(..., description="7-day forecast")
    total_predicted: float = Field(..., description="Sum of predicted cases for 7 days")
    trend: str = Field(..., description="Trend direction: increasing/decreasing/stable")
    last_7_day_actual: Optional[float] = Field(None, description="Actual cases from last 7 days")
    percent_change: Optional[float] = Field(None, description="Percent change from last 7 days")
    generated_at: datetime = Field(..., description="When prediction was generated")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location_id": "ncr",
                "location_name": "NCR",
                "predictions": [
                    {"date": "2025-11-29", "predicted_cases": 125.5, "day_ahead": 1}
                ],
                "total_predicted": 875.5,
                "trend": "increasing",
                "last_7_day_actual": 800.0,
                "percent_change": 9.4,
                "generated_at": "2025-11-28T06:00:00Z"
            }
        }
    )


class PredictionsResponse(BaseModel):
    """Response containing predictions for all or specific locations."""
    predictions: List[LocationPrediction] = Field(..., description="Predictions by location")
    status: PredictionStatus = Field(..., description="Data freshness status")
    generated_at: datetime = Field(..., description="Batch generation timestamp")
    next_update: Optional[datetime] = Field(None, description="Next scheduled update time")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "predictions": [],
                "status": "fresh",
                "generated_at": "2025-11-28T06:00:00Z",
                "next_update": "2025-11-29T06:00:00Z"
            }
        }
    )


# ============================================================================
# Danger Zone Schemas (for Map Visualization)
# ============================================================================

class DangerZone(BaseModel):
    """
    Danger zone data for map visualization.
    Used by frontend to render color-coded regions on the map.
    """
    location_id: str = Field(..., description="Location identifier")
    location_name: str = Field(..., description="Location display name")
    latitude: float = Field(..., description="Center latitude")
    longitude: float = Field(..., description="Center longitude")
    danger_level: DangerLevel = Field(..., description="Risk classification")
    risk_score: float = Field(..., description="Numeric risk score (0-100)")
    predicted_cases_7d: float = Field(..., description="Predicted cases next 7 days")
    percent_change: float = Field(..., description="Percent change from last week")
    color_hex: str = Field(..., description="Suggested color for map")
    radius_meters: int = Field(..., description="Suggested circle radius for map")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location_id": "ncr",
                "location_name": "NCR",
                "latitude": 14.5995,
                "longitude": 120.9842,
                "danger_level": "high",
                "risk_score": 75.5,
                "predicted_cases_7d": 875.5,
                "percent_change": 15.2,
                "color_hex": "#FF6B6B",
                "radius_meters": 50000
            }
        }
    )


class DangerZonesResponse(BaseModel):
    """Response containing all danger zones for map rendering."""
    danger_zones: List[DangerZone] = Field(..., description="List of danger zones")
    legend: dict = Field(..., description="Color legend for map")
    generated_at: datetime = Field(..., description="Data generation timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "danger_zones": [],
                "legend": {
                    "low": {"color": "#4CAF50", "label": "Low Risk (0-25)"},
                    "moderate": {"color": "#FFC107", "label": "Moderate Risk (25-50)"},
                    "high": {"color": "#FF9800", "label": "High Risk (50-75)"},
                    "critical": {"color": "#F44336", "label": "Critical Risk (75-100)"}
                },
                "generated_at": "2025-11-28T06:00:00Z"
            }
        }
    )


# ============================================================================
# Model Metrics Schemas
# ============================================================================

class ModelMetrics(BaseModel):
    """Performance metrics for a location's prediction model."""
    location: str = Field(..., description="Location name")
    validation_mae: float = Field(..., description="Validation Mean Absolute Error")
    validation_rmse: float = Field(..., description="Validation Root Mean Squared Error")
    test_mae: float = Field(..., description="Test Mean Absolute Error")
    test_rmse: float = Field(..., description="Test Root Mean Squared Error")
    test_r2: float = Field(..., description="Test R-squared score")
    n_estimators: int = Field(..., description="Number of estimators used")
    trained_at: Optional[datetime] = Field(None, description="Model training timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": "NCR",
                "validation_mae": 15.2,
                "validation_rmse": 22.5,
                "test_mae": 18.3,
                "test_rmse": 25.1,
                "test_r2": 0.85,
                "n_estimators": 150,
                "trained_at": "2025-11-28T06:00:00Z"
            }
        }
    )


class MetricsResponse(BaseModel):
    """Response containing model performance metrics."""
    metrics: List[ModelMetrics] = Field(..., description="Metrics for all models")
    average_mae: float = Field(..., description="Average MAE across all models")
    average_r2: float = Field(..., description="Average R² across all models")
    last_training: datetime = Field(..., description="Last model training timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metrics": [],
                "average_mae": 17.5,
                "average_r2": 0.82,
                "last_training": "2025-11-28T06:00:00Z"
            }
        }
    )


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "NotFoundError",
                "message": "Location not found",
                "detail": "No data available for location_id: xyz"
            }
        }
    )


# ============================================================================
# Epidemic Simulation Schemas
# ============================================================================

class AgentState(str, Enum):
    """Health state of an agent in the simulation."""
    SUSCEPTIBLE = "S"
    EXPOSED = "E"
    INFECTED = "I"
    RECOVERED = "R"
    DECEASED = "D"


class SimulationStatus(str, Enum):
    """Status of a simulation instance."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class SimulationConfigRequest(BaseModel):
    """
    Configuration parameters for starting a new epidemic simulation.
    Uses SEIRD model: Susceptible → Exposed → Infected → Recovered/Deceased
    """
    # Population settings
    population_size: int = Field(
        default=200, 
        ge=10, 
        le=10000,
        description="Total number of agents in the simulation"
    )
    grid_size: float = Field(
        default=100.0, 
        ge=20.0, 
        le=500.0,
        description="Size of the simulation world (square grid)"
    )
    initial_infected: int = Field(
        default=1,
        ge=0,
        le=10000,
        description="Number of initially infected agents"
    )
    
    # Disease characteristics
    infection_rate: float = Field(
        default=1.0, 
        ge=0.0, 
        le=5.0,
        alias="beta",
        description="Transmission probability per contact (β)"
    )
    incubation_mean: float = Field(
        default=5.0, 
        ge=0.1, 
        le=500.0,
        description="Mean incubation period in days"
    )
    incubation_std: float = Field(
        default=2.0, 
        ge=0.1, 
        le=5.0,
        description="Standard deviation of incubation period"
    )
    infectious_mean: float = Field(
        default=7.0, 
        ge=0.1, 
        le=500.0,
        description="Mean infectious period in days"
    )
    infectious_std: float = Field(
        default=3.0, 
        ge=0.1, 
        le=7.0,
        description="Standard deviation of infectious period"
    )
    mortality_rate: float = Field(
        default=0.02, 
        ge=0.0, 
        le=0.5,
        description="Case fatality rate (probability of death given infection)"
    )
    interaction_radius: float = Field(
        default=2.0,
        ge=0.5,
        le=10.0,
        description="Distance within which agents can infect others"
    )
    
    # Interventions
    vaccination_rate: float = Field(
        default=0.0, 
        ge=0.0, 
        le=2.0,
        description="Daily vaccination rate (S→R transition)"
    )
    detection_probability: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0,
        description="Probability of detecting an infectious case"
    )
    isolation_compliance: float = Field(
        default=0.8, 
        ge=0.0, 
        le=1.0,
        description="Probability of complying with isolation if detected"
    )
    
    # Mobility parameters
    home_attraction: float = Field(
        default=0.05, 
        ge=0.0, 
        le=0.5,
        description="Strength of pull towards home location"
    )
    random_movement: float = Field(
        default=1.0, 
        ge=0.0, 
        le=3.0,
        description="Intensity of random walk movement"
    )
    
    # Simulation settings
    time_step: float = Field(
        default=0.5, 
        ge=0.001, 
        le=10.0,
        alias="dt",
        description="Simulation time step (smaller = more accurate but slower)"
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
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
        }
    )


# Type alias for backward compatibility
SimulationConfig = SimulationConfigRequest


class AgentData(BaseModel):
    """Data for a single agent in the simulation (for visualization)."""
    id: int = Field(..., description="Unique agent identifier")
    x: float = Field(..., description="X coordinate position")
    y: float = Field(..., description="Y coordinate position")
    state: AgentState = Field(..., description="Current health state")
    days_in_state: float = Field(..., description="Days spent in current state")
    is_isolated: bool = Field(..., description="Whether agent is in isolation")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 0,
                "x": 45.2,
                "y": 67.8,
                "state": "S",
                "days_in_state": 0.0,
                "is_isolated": False
            }
        }
    )


class SimulationStats(BaseModel):
    """Statistical data from the simulation at current time step."""
    susceptible: int = Field(..., description="Number of susceptible agents")
    exposed: int = Field(..., description="Number of exposed agents")
    infected: int = Field(..., description="Number of infected agents")
    recovered: int = Field(..., description="Number of recovered agents")
    deceased: int = Field(..., description="Number of deceased agents")
    
    # Time series (history up to current point)
    susceptible_history: List[int] = Field(default=[], description="S count over time")
    exposed_history: List[int] = Field(default=[], description="E count over time")
    infected_history: List[int] = Field(default=[], description="I count over time")
    recovered_history: List[int] = Field(default=[], description="R count over time")
    deceased_history: List[int] = Field(default=[], description="D count over time")
    
    # Reproduction number
    current_rt: float = Field(..., description="Current effective reproduction number")
    rt_history: List[float] = Field(default=[], description="Rt over time")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "susceptible": 195,
                "exposed": 2,
                "infected": 3,
                "recovered": 0,
                "deceased": 0,
                "susceptible_history": [199, 198, 197, 196, 195],
                "exposed_history": [0, 1, 1, 2, 2],
                "infected_history": [1, 1, 2, 2, 3],
                "recovered_history": [0, 0, 0, 0, 0],
                "deceased_history": [0, 0, 0, 0, 0],
                "current_rt": 2.5,
                "rt_history": [2.0, 2.2, 2.3, 2.4, 2.5]
            }
        }
    )


class SimulationState(BaseModel):
    """Current state of a simulation instance."""
    simulation_id: str = Field(..., description="Unique simulation identifier")
    status: SimulationStatus = Field(..., description="Current simulation status")
    current_day: float = Field(..., description="Current simulation day")
    total_steps: int = Field(..., description="Total steps executed")
    
    # Configuration used
    config: SimulationConfigRequest = Field(..., description="Simulation configuration")
    
    # Current statistics
    stats: SimulationStats = Field(..., description="Current statistics")
    
    # Metadata
    created_at: datetime = Field(..., description="When simulation was created")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "simulation_id": "sim_abc123",
                "status": "running",
                "current_day": 5.5,
                "total_steps": 11,
                "config": {},
                "stats": {},
                "created_at": "2025-11-28T12:00:00Z",
                "last_updated": "2025-11-28T12:05:00Z"
            }
        }
    )


class SimulationCreateResponse(BaseModel):
    """Response when creating a new simulation."""
    simulation_id: str = Field(..., description="Unique simulation identifier")
    status: SimulationStatus = Field(..., description="Initial simulation status")
    message: str = Field(..., description="Status message")
    config: SimulationConfigRequest = Field(..., description="Applied configuration")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "simulation_id": "sim_abc123",
                "status": "created",
                "message": "Simulation created successfully",
                "config": {},
                "created_at": "2025-11-28T12:00:00Z"
            }
        }
    )


class SimulationRunRequest(BaseModel):
    """Request to run simulation for specified number of steps or days."""
    steps: Optional[int] = Field(
        default=None, 
        ge=1, 
        le=10000,
        description="Number of steps to run"
    )
    days: Optional[float] = Field(
        default=None, 
        ge=0.1, 
        le=365.0,
        description="Number of days to simulate"
    )
    stop_when_no_infected: bool = Field(
        default=True,
        description="Stop simulation when no infected/exposed agents remain"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "days": 30.0,
                "stop_when_no_infected": True
            }
        }
    )


class SimulationAgentsResponse(BaseModel):
    """Response containing agent positions for visualization."""
    simulation_id: str = Field(..., description="Simulation identifier")
    current_day: float = Field(..., description="Current simulation day")
    agents: List[AgentData] = Field(..., description="List of all agents")
    grid_size: float = Field(..., description="Size of simulation grid")
    
    # Color mapping for visualization
    state_colors: dict = Field(
        default={
            "S": "#3498db",  # Blue - Susceptible
            "E": "#f1c40f",  # Yellow - Exposed
            "I": "#e74c3c",  # Red - Infected
            "R": "#2ecc71",  # Green - Recovered
            "D": "#34495e"   # Dark Grey - Deceased
        },
        description="Suggested colors for each state"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "simulation_id": "sim_abc123",
                "current_day": 5.5,
                "agents": [],
                "grid_size": 100.0,
                "state_colors": {
                    "S": "#3498db",
                    "E": "#f1c40f", 
                    "I": "#e74c3c",
                    "R": "#2ecc71",
                    "D": "#34495e"
                }
            }
        }
    )


class SimulationListResponse(BaseModel):
    """Response listing all active simulations."""
    simulations: List[SimulationState] = Field(..., description="List of simulations")
    count: int = Field(..., description="Total number of simulations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "simulations": [],
                "count": 0
            }
        }
    )

# Epidemic Metrics Schemas (for Simulation Analysis)

class EpidemicMetrics(BaseModel):
    """computed epidemic metrics from simulation."""
    r0: float = Field(..., description="Basic reproduction number")
    rt: float = Field(..., description="Effective reproduction number (current)")
    attack_rate: float = Field(..., description="Attack rate (% of population infected)")
    case_fatality_rate: float = Field(..., description="Case fatality rate (%)")
    doubling_time: Optional[float] = Field(None, description="Doubling time of infections (days)")
    peak_infected: int = Field(..., description="Peak number of concurrent infected")
    peak_day: int = Field(..., description="Day peak infection occurred")
    outbreak_duration: int = Field(..., description="Total days with active transmission")
    current_infected: int = Field(..., description="Current infected count")
    current_recovered: int = Field(..., description="Current recovered count")
    current_deceased: int = Field(..., description="Current deceased count")
    vaccination_coverage: float = Field(..., description="Vaccination coverage (%)")
    growth_rate: float = Field(..., description="Recent growth rate of infections")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "r0": 2.5,
                "rt": 1.2,
                "attack_rate": 45.5,
                "case_fatality_rate": 2.1,
                "doubling_time": 3.5,
                "peak_infected": 150,
                "peak_day": 15,
                "outbreak_duration": 45,
                "current_infected": 20,
                "current_recovered": 250,
                "current_deceased": 5,
                "vaccination_coverage": 0.0,
                "growth_rate": 0.1
            }
        }
    )


class SimulationStatistics(BaseModel):
    """time-series statistics from simulation."""
    susceptible: List[int] = Field(..., description="Susceptible count per timestep")
    exposed: List[int] = Field(..., description="Exposed count per timestep")
    infected: List[int] = Field(..., description="Infected count per timestep")
    recovered: List[int] = Field(..., description="Recovered count per timestep")
    deceased: List[int] = Field(..., description="Deceased count per timestep")
    rt_history: Optional[List[float]] = Field(None, description="Effective Rt per timestep")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "susceptible": [200, 199, 198],
                "exposed": [0, 1, 2],
                "infected": [0, 0, 1],
                "recovered": [0, 0, 0],
                "deceased": [0, 0, 0],
                "rt_history": [0.0, 1.0, 1.5]
            }
        }
    )


class SimulationOutput(BaseModel):
    """complete simulation output for API response."""
    simulation_id: str = Field(..., description="Unique simulation identifier")
    location_id: str = Field(..., description="Location identifier")
    location_name: str = Field(..., description="Location display name")
    config: SimulationConfigRequest = Field(..., description="Simulation configuration used")
    statistics: SimulationStatistics = Field(..., description="Time-series statistics")
    metrics: EpidemicMetrics = Field(..., description="Calculated epidemic metrics")
    agent_geojson: dict = Field(..., description="Agent positions in GeoJSON format")
    trend: str = Field(..., description="Overall trend: 'increasing', 'decreasing', 'stable'")
    generated_at: datetime = Field(..., description="When simulation was completed")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "simulation_id": "sim_abc123",
                "location_id": "ncr",
                "location_name": "NCR",
                "config": {},
                "statistics": {},
                "metrics": {},
                "agent_geojson": {"type": "FeatureCollection", "features": []},
                "trend": "stable",
                "generated_at": "2025-11-28T12:00:00Z"
            }
        }
    )
