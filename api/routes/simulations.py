"""
Simulations Router
Endpoints for running epidemic simulations using the SEIRD agent-based model.

This module provides REST API endpoints for:
- Creating and configuring simulations
- Running simulations step-by-step or in batch
- Retrieving simulation state, statistics, and agent data
- Managing simulation lifecycle

The actual simulation engine (EpidemicSimulation class) should be implemented
by the data analyst team and placed in api/services/simulation_service.py
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from api.models.schemas import (
    SimulationConfigRequest,
    SimulationState,
    SimulationStats,
    SimulationStatus,
    SimulationCreateResponse,
    SimulationRunRequest,
    SimulationAgentsResponse,
    SimulationListResponse,
    AgentData,
    AgentState,
    ErrorResponse,
)
from api.services.simulation_service import SimulationService


router = APIRouter(prefix="/simulations", tags=["Simulations"])

# Initialize simulation service for validation
simulation_service = SimulationService()


# ============================================================================
# In-Memory Simulation Storage
# ============================================================================
# NOTE: This is a simple in-memory store for development/testing.
# For production, consider using Redis or a database.

class SimulationStore:
    """
    In-memory storage for simulation instances.
    
    TODO for Data Analyst:
    - Replace MockSimulation with actual EpidemicSimulation from simulation.py
    - Implement proper simulation engine integration
    """
    
    def __init__(self):
        self._simulations: Dict[str, dict] = {}
    
    def create(self, config: SimulationConfigRequest) -> str:
        """Create a new simulation and return its ID."""
        sim_id = f"sim_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        # Initialize mock simulation data
        # TODO: Replace with actual EpidemicSimulation instantiation
        initial_infected = config.initial_infected
        initial_susceptible = config.population_size - initial_infected
        
        self._simulations[sim_id] = {
            "id": sim_id,
            "config": config,
            "status": SimulationStatus.CREATED,
            "current_day": 0.0,
            "total_steps": 0,
            "created_at": now,
            "last_updated": now,
            # Mock statistics
            "stats": {
                "S": [initial_susceptible],
                "E": [0],
                "I": [initial_infected],
                "R": [0],
                "D": [0],
            },
            "rt_history": [0.0],
            # Mock agent data
            "agents": self._create_mock_agents(config),
        }
        
        return sim_id
    
    def _create_mock_agents(self, config: SimulationConfigRequest) -> list:
        """Create mock agent data for testing."""
        import random
        agents = []
        for i in range(config.population_size):
            state = "I" if i < config.initial_infected else "S"
            agents.append({
                "id": i,
                "x": random.uniform(0, config.grid_size),
                "y": random.uniform(0, config.grid_size),
                "state": state,
                "days_in_state": 0.0,
                "is_isolated": False,
            })
        return agents
    
    def get(self, sim_id: str) -> Optional[dict]:
        """Get simulation by ID."""
        return self._simulations.get(sim_id)
    
    def update(self, sim_id: str, data: dict) -> None:
        """Update simulation data."""
        if sim_id in self._simulations:
            self._simulations[sim_id].update(data)
            self._simulations[sim_id]["last_updated"] = datetime.now(timezone.utc)
    
    def delete(self, sim_id: str) -> bool:
        """Delete simulation. Returns True if deleted."""
        if sim_id in self._simulations:
            del self._simulations[sim_id]
            return True
        return False
    
    def list_all(self) -> list:
        """List all simulations."""
        return list(self._simulations.values())
    
    def run_step(self, sim_id: str) -> bool:
        """
        Run one simulation step.
        
        TODO for Data Analyst:
        - Replace this mock implementation with actual simulation.step()
        - Update agent positions and states from the real simulation
        """
        sim = self._simulations.get(sim_id)
        if not sim:
            return False
        
        import random
        
        config = sim["config"]
        dt = config.time_step
        
        # Update simulation time
        sim["current_day"] += dt
        sim["total_steps"] += 1
        sim["status"] = SimulationStatus.RUNNING
        
        # Get current counts
        stats = sim["stats"]
        current_s = stats["S"][-1]
        current_e = stats["E"][-1]
        current_i = stats["I"][-1]
        current_r = stats["R"][-1]
        current_d = stats["D"][-1]
        
        # Mock SEIRD transitions (simplified)
        # In reality, this should use the actual simulation engine
        new_infections = 0
        if current_i > 0 and current_s > 0:
            # Probability of new infection
            infection_prob = config.infection_rate * current_i / config.population_size * dt
            for _ in range(current_s):
                if random.random() < infection_prob:
                    new_infections += 1
        
        # E -> I transitions
        e_to_i = 0
        if current_e > 0:
            transition_prob = dt / config.incubation_mean
            for _ in range(current_e):
                if random.random() < transition_prob:
                    e_to_i += 1
        
        # I -> R/D transitions
        i_to_r = 0
        i_to_d = 0
        if current_i > 0:
            transition_prob = dt / config.infectious_mean
            for _ in range(current_i):
                if random.random() < transition_prob:
                    if random.random() < config.mortality_rate:
                        i_to_d += 1
                    else:
                        i_to_r += 1
        
        # Update counts
        new_s = max(0, current_s - new_infections)
        new_e = max(0, current_e + new_infections - e_to_i)
        new_i = max(0, current_i + e_to_i - i_to_r - i_to_d)
        new_r = current_r + i_to_r
        new_d = current_d + i_to_d
        
        # Ensure population conservation
        total = new_s + new_e + new_i + new_r + new_d
        if total != config.population_size:
            # Adjust susceptible to conserve population
            new_s = config.population_size - new_e - new_i - new_r - new_d
        
        stats["S"].append(new_s)
        stats["E"].append(new_e)
        stats["I"].append(new_i)
        stats["R"].append(new_r)
        stats["D"].append(new_d)
        
        # Calculate Rt (mock)
        if current_i > 0:
            rt = (new_infections / dt) / current_i * config.infectious_mean
        else:
            rt = 0.0
        sim["rt_history"].append(rt)
        
        # Update mock agent states (simplified - just update counts)
        agents = sim["agents"]
        state_counts = {"S": 0, "E": 0, "I": 0, "R": 0, "D": 0}
        targets = {"S": new_s, "E": new_e, "I": new_i, "R": new_r, "D": new_d}
        
        for agent in agents:
            current_state = agent["state"]
            if state_counts[current_state] < targets[current_state]:
                state_counts[current_state] += 1
            else:
                # Need to transition to a different state
                for state in ["D", "R", "I", "E", "S"]:
                    if state_counts[state] < targets[state]:
                        agent["state"] = state
                        agent["days_in_state"] = 0.0
                        state_counts[state] += 1
                        break
            
            # Update position (simple random walk)
            if agent["state"] != "D" and not agent["is_isolated"]:
                agent["x"] += random.uniform(-1, 1) * dt
                agent["y"] += random.uniform(-1, 1) * dt
                agent["x"] = max(0, min(config.grid_size, agent["x"]))
                agent["y"] = max(0, min(config.grid_size, agent["y"]))
            
            agent["days_in_state"] += dt
        
        # Check if simulation is complete
        if new_i == 0 and new_e == 0:
            sim["status"] = SimulationStatus.COMPLETED
        
        sim["last_updated"] = datetime.now(timezone.utc)
        return True


# Global simulation store instance
simulation_store = SimulationStore()


# ============================================================================
# Helper Functions
# ============================================================================

def _build_simulation_state(sim_data: dict) -> SimulationState:
    """Build SimulationState response from stored simulation data."""
    stats = sim_data["stats"]
    
    return SimulationState(
        simulation_id=sim_data["id"],
        status=sim_data["status"],
        current_day=sim_data["current_day"],
        total_steps=sim_data["total_steps"],
        config=sim_data["config"],
        stats=SimulationStats(
            susceptible=stats["S"][-1],
            exposed=stats["E"][-1],
            infected=stats["I"][-1],
            recovered=stats["R"][-1],
            deceased=stats["D"][-1],
            susceptible_history=stats["S"],
            exposed_history=stats["E"],
            infected_history=stats["I"],
            recovered_history=stats["R"],
            deceased_history=stats["D"],
            current_rt=sim_data["rt_history"][-1] if sim_data["rt_history"] else 0.0,
            rt_history=sim_data["rt_history"],
        ),
        created_at=sim_data["created_at"],
        last_updated=sim_data["last_updated"],
    )


def _build_agents_response(sim_data: dict) -> SimulationAgentsResponse:
    """Build SimulationAgentsResponse from stored simulation data."""
    agents = [
        AgentData(
            id=a["id"],
            x=a["x"],
            y=a["y"],
            state=AgentState(a["state"]),
            days_in_state=a["days_in_state"],
            is_isolated=a["is_isolated"],
        )
        for a in sim_data["agents"]
    ]
    
    return SimulationAgentsResponse(
        simulation_id=sim_data["id"],
        current_day=sim_data["current_day"],
        agents=agents,
        grid_size=sim_data["config"].grid_size,
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "",
    response_model=SimulationCreateResponse,
    status_code=201,
    summary="Create New Simulation",
    description="Create a new epidemic simulation with specified parameters.",
    responses={
        201: {"description": "Simulation created successfully"},
        400: {"description": "Invalid configuration", "model": ErrorResponse},
    }
)
async def create_simulation(
    config: SimulationConfigRequest = None
) -> SimulationCreateResponse:
    """
    Create a new epidemic simulation.
    
    The simulation uses a SEIRD (Susceptible-Exposed-Infected-Recovered-Deceased)
    agent-based model. Agents move in a 2D space and can infect each other
    when within the interaction radius.
    
    Args:
        config: Simulation configuration. Uses defaults if not provided.
    
    Returns:
        SimulationCreateResponse with the simulation ID and initial state.
    """
    if config is None:
        config = SimulationConfigRequest()
    
    # Validate configuration using custom validation
    is_valid, error_message = simulation_service.validate_simulation_config(config)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=error_message or "Invalid simulation configuration"
        )
    
    sim_id = simulation_store.create(config)
    sim_data = simulation_store.get(sim_id)
    
    return SimulationCreateResponse(
        simulation_id=sim_id,
        status=SimulationStatus.CREATED,
        message="Simulation created successfully. Use POST /step or /run to advance.",
        config=config,
        created_at=sim_data["created_at"],
    )


@router.get(
    "",
    response_model=SimulationListResponse,
    summary="List All Simulations",
    description="Get a list of all active simulations.",
)
async def list_simulations() -> SimulationListResponse:
    """
    List all active simulations.
    
    Returns:
        List of all simulation states.
    """
    all_sims = simulation_store.list_all()
    states = [_build_simulation_state(sim) for sim in all_sims]
    
    return SimulationListResponse(
        simulations=states,
        count=len(states),
    )


@router.get(
    "/{simulation_id}",
    response_model=SimulationState,
    summary="Get Simulation State",
    description="Get the current state of a simulation.",
    responses={
        200: {"description": "Simulation state retrieved"},
        404: {"description": "Simulation not found", "model": ErrorResponse},
    }
)
async def get_simulation(simulation_id: str) -> SimulationState:
    """
    Get the current state of a simulation.
    
    Args:
        simulation_id: Unique simulation identifier
    
    Returns:
        Current simulation state including configuration, statistics, and metadata.
    """
    sim_data = simulation_store.get(simulation_id)
    
    if not sim_data:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation not found: {simulation_id}"
        )
    
    return _build_simulation_state(sim_data)


@router.post(
    "/{simulation_id}/step",
    response_model=SimulationState,
    summary="Run One Step",
    description="Advance the simulation by one time step.",
    responses={
        200: {"description": "Step executed successfully"},
        404: {"description": "Simulation not found", "model": ErrorResponse},
        400: {"description": "Simulation already completed", "model": ErrorResponse},
    }
)
async def run_simulation_step(simulation_id: str) -> SimulationState:
    """
    Run one simulation step.
    
    Advances the simulation by one time step (dt). Use this for
    real-time visualization where you want to see each step.
    
    Args:
        simulation_id: Unique simulation identifier
    
    Returns:
        Updated simulation state after the step.
    """
    sim_data = simulation_store.get(simulation_id)
    
    if not sim_data:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation not found: {simulation_id}"
        )
    
    if sim_data["status"] == SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Simulation has already completed (no infected/exposed remaining)"
        )
    
    simulation_store.run_step(simulation_id)
    
    return _build_simulation_state(simulation_store.get(simulation_id))


@router.post(
    "/{simulation_id}/run",
    response_model=SimulationState,
    summary="Run Simulation",
    description="Run the simulation for specified steps or days.",
    responses={
        200: {"description": "Simulation run completed"},
        404: {"description": "Simulation not found", "model": ErrorResponse},
        400: {"description": "Invalid run parameters", "model": ErrorResponse},
    }
)
async def run_simulation(
    simulation_id: str,
    run_config: SimulationRunRequest = None
) -> SimulationState:
    """
    Run the simulation for multiple steps or a specified duration.
    
    You can specify either:
    - `steps`: Number of time steps to run
    - `days`: Number of simulation days to run
    
    If neither is specified, runs for 100 days or until no infected remain.
    
    Args:
        simulation_id: Unique simulation identifier
        run_config: Run configuration (steps, days, stop conditions)
    
    Returns:
        Final simulation state after running.
    """
    sim_data = simulation_store.get(simulation_id)
    
    if not sim_data:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation not found: {simulation_id}"
        )
    
    if sim_data["status"] == SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Simulation has already completed"
        )
    
    if run_config is None:
        run_config = SimulationRunRequest(days=100.0, stop_when_no_infected=True)
    
    # Determine number of steps to run
    config = sim_data["config"]
    dt = config.time_step
    
    if run_config.steps:
        max_steps = run_config.steps
    elif run_config.days:
        max_steps = int(run_config.days / dt)
    else:
        max_steps = int(100.0 / dt)  # Default: 100 days
    
    # Run simulation
    steps_run = 0
    for _ in range(max_steps):
        success = simulation_store.run_step(simulation_id)
        if not success:
            break
        
        steps_run += 1
        
        # Check stop condition
        sim_data = simulation_store.get(simulation_id)
        if run_config.stop_when_no_infected:
            stats = sim_data["stats"]
            if stats["I"][-1] == 0 and stats["E"][-1] == 0:
                break
    
    return _build_simulation_state(simulation_store.get(simulation_id))


@router.get(
    "/{simulation_id}/stats",
    response_model=SimulationStats,
    summary="Get Statistics",
    description="Get detailed statistics from the simulation.",
    responses={
        200: {"description": "Statistics retrieved"},
        404: {"description": "Simulation not found", "model": ErrorResponse},
    }
)
async def get_simulation_stats(simulation_id: str) -> SimulationStats:
    """
    Get detailed statistics from the simulation.
    
    Returns SEIRD counts (current and historical) and reproduction number (Rt).
    
    Args:
        simulation_id: Unique simulation identifier
    
    Returns:
        SimulationStats with current counts and time series data.
    """
    sim_data = simulation_store.get(simulation_id)
    
    if not sim_data:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation not found: {simulation_id}"
        )
    
    stats = sim_data["stats"]
    
    return SimulationStats(
        susceptible=stats["S"][-1],
        exposed=stats["E"][-1],
        infected=stats["I"][-1],
        recovered=stats["R"][-1],
        deceased=stats["D"][-1],
        susceptible_history=stats["S"],
        exposed_history=stats["E"],
        infected_history=stats["I"],
        recovered_history=stats["R"],
        deceased_history=stats["D"],
        current_rt=sim_data["rt_history"][-1] if sim_data["rt_history"] else 0.0,
        rt_history=sim_data["rt_history"],
    )


@router.get(
    "/{simulation_id}/agents",
    response_model=SimulationAgentsResponse,
    summary="Get Agent Data",
    description="Get all agent positions and states for visualization.",
    responses={
        200: {"description": "Agent data retrieved"},
        404: {"description": "Simulation not found", "model": ErrorResponse},
    }
)
async def get_simulation_agents(
    simulation_id: str,
    include_deceased: bool = Query(
        True, 
        description="Include deceased agents in response"
    )
) -> SimulationAgentsResponse:
    """
    Get agent positions and states for visualization.
    
    Returns all agents with their current positions, health states,
    and suggested colors for rendering on a map/grid.
    
    Args:
        simulation_id: Unique simulation identifier
        include_deceased: Whether to include deceased agents
    
    Returns:
        SimulationAgentsResponse with agent data and color mapping.
    """
    sim_data = simulation_store.get(simulation_id)
    
    if not sim_data:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation not found: {simulation_id}"
        )
    
    response = _build_agents_response(sim_data)
    
    # Filter out deceased if requested
    if not include_deceased:
        response.agents = [a for a in response.agents if a.state != AgentState.DECEASED]
    
    return response


@router.delete(
    "/{simulation_id}",
    status_code=204,
    summary="Delete Simulation",
    description="Stop and delete a simulation.",
    responses={
        204: {"description": "Simulation deleted"},
        404: {"description": "Simulation not found", "model": ErrorResponse},
    }
)
async def delete_simulation(simulation_id: str) -> None:
    """
    Delete a simulation.
    
    Stops the simulation and removes all associated data.
    
    Args:
        simulation_id: Unique simulation identifier
    """
    success = simulation_store.delete(simulation_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation not found: {simulation_id}"
        )

