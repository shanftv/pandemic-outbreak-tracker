# Simulation Integration Guide

## For Data Analyst

This document outlines the remaining tasks to integrate the Simple-Epidemic simulation engine with the Pandemic Outbreak Tracker API.

---

## Overview

The API infrastructure for epidemic simulations is **complete and tested**. The endpoints currently use a mock simulation engine for development/testing purposes. Your task is to replace the mock with the actual `EpidemicSimulation` class from the Simple-Epidemic project.

### Current State
- API endpoints created and tested (36 tests passing)
- Pydantic schemas for request/response models
- In-memory simulation storage
- **Mock simulation engine** needs to be replaced with real implementation

---

## Tasks

### 1. Copy Simulation Engine

Copy the simulation core from Simple-Epidemic into this project:

```bash
# From project root
cp /Users/gdullas/Desktop/Projects/Simulations/Simple-Epidemic/simulation.py \
   api/services/simulation_engine.py
```

### 2. Modify Imports in simulation_engine.py

Update the imports if needed. The file should work standalone without Streamlit dependencies.

**Required dependencies** (already in requirements.txt):
- `numpy`
- `pandas` (optional, for data export)

### 3. Create Simulation Service

Create a new file `api/services/simulation_service.py` that wraps the simulation engine:

```python
"""
Simulation Service
Wrapper around the EpidemicSimulation engine for API integration.
"""

from typing import Dict, Optional, List
from datetime import datetime, UTC
import uuid

from api.services.simulation_engine import EpidemicSimulation, SimulationConfig
from api.models.schemas import SimulationConfigRequest


class SimulationService:
    """Service for managing epidemic simulations."""
    
    def __init__(self):
        self._simulations: Dict[str, dict] = {}
    
    def _config_to_engine(self, config: SimulationConfigRequest) -> SimulationConfig:
        """Convert API config to simulation engine config."""
        return SimulationConfig(
            N=config.population_size,
            grid_size=config.grid_size,
            beta=config.infection_rate,
            incubation_mean=config.incubation_mean,
            incubation_std=config.incubation_std,
            infectious_mean=config.infectious_mean,
            infectious_std=config.infectious_std,
            mortality_rate=config.mortality_rate,
            vax_rate=config.vaccination_rate,
            interaction_radius=config.interaction_radius,
            dt=config.time_step,
            home_attraction=config.home_attraction,
            random_force=config.random_movement,
            isolation_compliance=config.isolation_compliance,
            detection_prob=config.detection_probability,
        )
    
    def create(self, config: SimulationConfigRequest) -> str:
        """Create a new simulation instance."""
        sim_id = f"sim_{uuid.uuid4().hex[:12]}"
        engine_config = self._config_to_engine(config)
        
        # Create the actual simulation
        simulation = EpidemicSimulation(engine_config)
        
        self._simulations[sim_id] = {
            "id": sim_id,
            "config": config,
            "engine": simulation,
            "created_at": datetime.now(UTC),
            "last_updated": datetime.now(UTC),
            "status": "created",
            "total_steps": 0,
        }
        
        return sim_id
    
    def step(self, sim_id: str) -> bool:
        """Run one simulation step."""
        sim = self._simulations.get(sim_id)
        if not sim:
            return False
        
        sim["engine"].step()
        sim["total_steps"] += 1
        sim["status"] = "running"
        sim["last_updated"] = datetime.now(UTC)
        
        # Check completion
        stats = sim["engine"].stats
        if stats["I"][-1] == 0 and stats["E"][-1] == 0:
            sim["status"] = "completed"
        
        return True
    
    def get_stats(self, sim_id: str) -> Optional[dict]:
        """Get simulation statistics."""
        sim = self._simulations.get(sim_id)
        if not sim:
            return None
        
        engine = sim["engine"]
        return {
            "S": engine.stats["S"],
            "E": engine.stats["E"],
            "I": engine.stats["I"],
            "R": engine.stats["R"],
            "D": engine.stats["D"],
            "rt_history": engine.rt_history,
        }
    
    def get_agents(self, sim_id: str) -> Optional[List[dict]]:
        """Get agent data for visualization."""
        sim = self._simulations.get(sim_id)
        if not sim:
            return None
        
        return sim["engine"].get_agent_data()
    
    def get_current_day(self, sim_id: str) -> float:
        """Get current simulation day."""
        sim = self._simulations.get(sim_id)
        if not sim:
            return 0.0
        
        return sim["total_steps"] * sim["config"].time_step
    
    def delete(self, sim_id: str) -> bool:
        """Delete a simulation."""
        if sim_id in self._simulations:
            del self._simulations[sim_id]
            return True
        return False
    
    def get(self, sim_id: str) -> Optional[dict]:
        """Get simulation data."""
        return self._simulations.get(sim_id)
    
    def list_all(self) -> List[dict]:
        """List all simulations."""
        return list(self._simulations.values())
```

### 4. Update Routes to Use Service

Modify `api/routes/simulations.py` to use the new service instead of the mock `SimulationStore`:

```python
# Replace this:
from api.routes.simulations import simulation_store

# With this:
from api.services.simulation_service import SimulationService

simulation_service = SimulationService()
```

Then update each endpoint to use `simulation_service` methods.

### 5. Handle Initial Infected Count

The current Simple-Epidemic `simulation.py` hardcodes `num_infected = 1`. Modify `init_agents()` to accept the initial infected count from config:

```python
# In simulation_engine.py, update SimulationConfig:
@dataclass
class SimulationConfig:
    # ... existing fields ...
    initial_infected: int = 1  # Add this field

# In EpidemicSimulation.init_agents():
def init_agents(self):
    self.agents = []
    num_infected = self.config.initial_infected  # Use config value
    # ... rest of method
```

---

## Configuration Mapping

| API Field | Engine Field | Description |
|-----------|--------------|-------------|
| `population_size` | `N` | Number of agents |
| `grid_size` | `grid_size` | Simulation world size |
| `infection_rate` | `beta` | Transmission rate (β) |
| `incubation_mean` | `incubation_mean` | Mean incubation period |
| `incubation_std` | `incubation_std` | Std dev of incubation |
| `infectious_mean` | `infectious_mean` | Mean infectious period |
| `infectious_std` | `infectious_std` | Std dev of infectious period |
| `mortality_rate` | `mortality_rate` | Case fatality rate |
| `vaccination_rate` | `vax_rate` | Daily vaccination rate |
| `interaction_radius` | `interaction_radius` | Infection distance |
| `time_step` | `dt` | Simulation time step |
| `home_attraction` | `home_attraction` | Pull towards home |
| `random_movement` | `random_force` | Random walk intensity |
| `detection_probability` | `detection_prob` | Case detection rate |
| `isolation_compliance` | `isolation_compliance` | Isolation adherence |
| `initial_infected` | *(new)* | Starting infected count |

---

## API Endpoints Reference

All endpoints are prefixed with `/api/v1/simulations`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create new simulation |
| `GET` | `/` | List all simulations |
| `GET` | `/{id}` | Get simulation state |
| `POST` | `/{id}/step` | Run one step |
| `POST` | `/{id}/run` | Run for N steps/days |
| `GET` | `/{id}/stats` | Get SEIRD statistics |
| `GET` | `/{id}/agents` | Get agent positions |
| `DELETE` | `/{id}` | Delete simulation |

---

## Testing

After integration, run the existing tests to verify everything works:

```bash
# Run simulation tests only
pytest tests/test_simulations.py -v

# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html
```

All 36 simulation tests should continue to pass after integration.

---

## Example API Usage

### Create and Run a Simulation

```bash
# Create simulation
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "population_size": 500,
    "infection_rate": 1.5,
    "mortality_rate": 0.02,
    "vaccination_rate": 0.01
  }'

# Response: {"simulation_id": "sim_abc123", ...}

# Run for 30 days
curl -X POST http://localhost:8000/api/v1/simulations/sim_abc123/run \
  -H "Content-Type: application/json" \
  -d '{"days": 30.0}'

# Get statistics
curl http://localhost:8000/api/v1/simulations/sim_abc123/stats

# Get agent positions (for visualization)
curl http://localhost:8000/api/v1/simulations/sim_abc123/agents
```

---

## Questions?

Contact mer if you have questions about:
- API structure or endpoints
- Request/response schemas
- Testing requirements

The simulation logic and SEIRD model implementation is your domain!

## NOTE
- Delete this md file after implementing the simulation logic

