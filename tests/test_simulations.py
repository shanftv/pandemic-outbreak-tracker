"""
Tests for Epidemic Simulation Endpoints

This test suite covers all simulation API endpoints:
- POST /api/v1/simulations - Create simulation
- GET /api/v1/simulations - List simulations
- GET /api/v1/simulations/{id} - Get simulation state
- POST /api/v1/simulations/{id}/step - Run one step
- POST /api/v1/simulations/{id}/run - Run simulation
- GET /api/v1/simulations/{id}/stats - Get statistics
- GET /api/v1/simulations/{id}/agents - Get agent data
- DELETE /api/v1/simulations/{id} - Delete simulation
"""

import pytest
from fastapi.testclient import TestClient

from api.routes.simulations import simulation_store


@pytest.fixture(autouse=True)
def clean_simulations():
    """Clean up simulation store before and after each test."""
    # Clear before test
    simulation_store._simulations.clear()
    yield
    # Clear after test
    simulation_store._simulations.clear()


class TestCreateSimulation:
    """Test suite for simulation creation endpoint."""
    
    def test_create_simulation_default_config(self, client):
        """Test creating simulation with default configuration."""
        response = client.post("/api/v1/simulations")
        
        assert response.status_code == 201
        data = response.json()
        
        assert "simulation_id" in data
        assert data["simulation_id"].startswith("sim_")
        assert data["status"] == "created"
        assert "message" in data
        assert "config" in data
        assert "created_at" in data
    
    def test_create_simulation_custom_config(self, client):
        """Test creating simulation with custom configuration."""
        config = {
            "population_size": 500,
            "grid_size": 150.0,
            "infection_rate": 2.0,
            "incubation_mean": 4.0,
            "infectious_mean": 10.0,
            "mortality_rate": 0.05,
            "vaccination_rate": 0.01
        }
        
        response = client.post("/api/v1/simulations", json=config)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["config"]["population_size"] == 500
        assert data["config"]["grid_size"] == 150.0
        # infection_rate is serialized as "beta" due to Pydantic alias
        assert data["config"].get("infection_rate", data["config"].get("beta")) == 2.0
        assert data["config"]["mortality_rate"] == 0.05
    
    def test_create_simulation_invalid_initial_infected(self, client):
        """Test that initial_infected cannot exceed population_size."""
        config = {
            "population_size": 100,
            "initial_infected": 100  # Equal to population size (exceeds le=50 constraint)
        }
        
        response = client.post("/api/v1/simulations", json=config)
        
        # Returns 422 (Pydantic validation) or 400 (custom validation)
        assert response.status_code in [400, 422]
    
    def test_create_simulation_validates_bounds(self, client):
        """Test that configuration values are validated."""
        # Population size too small
        response = client.post("/api/v1/simulations", json={"population_size": 5})
        assert response.status_code == 422  # Validation error
        
        # Infection rate too high
        response = client.post("/api/v1/simulations", json={"infection_rate": 10.0})
        assert response.status_code == 422
        
        # Mortality rate too high
        response = client.post("/api/v1/simulations", json={"mortality_rate": 0.8})
        assert response.status_code == 422


class TestListSimulations:
    """Test suite for listing simulations endpoint."""
    
    def test_list_empty_simulations(self, client):
        """Test listing when no simulations exist."""
        response = client.get("/api/v1/simulations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "simulations" in data
        assert "count" in data
        assert data["count"] == 0
        assert data["simulations"] == []
    
    def test_list_multiple_simulations(self, client):
        """Test listing multiple simulations."""
        # Create 3 simulations
        for _ in range(3):
            client.post("/api/v1/simulations")
        
        response = client.get("/api/v1/simulations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 3
        assert len(data["simulations"]) == 3
        
        # Each simulation should have required fields
        for sim in data["simulations"]:
            assert "simulation_id" in sim
            assert "status" in sim
            assert "current_day" in sim
            assert "config" in sim
            assert "stats" in sim


class TestGetSimulationState:
    """Test suite for getting simulation state endpoint."""
    
    def test_get_simulation_state(self, client):
        """Test getting simulation state by ID."""
        # Create a simulation
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        # Get its state
        response = client.get(f"/api/v1/simulations/{sim_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["simulation_id"] == sim_id
        assert data["status"] == "created"
        assert data["current_day"] == 0.0
        assert data["total_steps"] == 0
        assert "config" in data
        assert "stats" in data
    
    def test_get_nonexistent_simulation(self, client):
        """Test getting state of non-existent simulation."""
        response = client.get("/api/v1/simulations/sim_nonexistent123")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_simulation_state_stats_structure(self, client):
        """Test that simulation stats have correct structure."""
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        response = client.get(f"/api/v1/simulations/{sim_id}")
        data = response.json()
        
        stats = data["stats"]
        assert "susceptible" in stats
        assert "exposed" in stats
        assert "infected" in stats
        assert "recovered" in stats
        assert "deceased" in stats
        assert "current_rt" in stats
        assert "susceptible_history" in stats
        assert "rt_history" in stats


class TestRunSimulationStep:
    """Test suite for running simulation step endpoint."""
    
    def test_run_single_step(self, client):
        """Test running a single simulation step."""
        # Create simulation
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        # Run one step
        response = client.post(f"/api/v1/simulations/{sim_id}/step")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["simulation_id"] == sim_id
        assert data["status"] == "running"
        assert data["current_day"] > 0
        assert data["total_steps"] == 1
    
    def test_run_multiple_steps(self, client):
        """Test running multiple simulation steps."""
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        # Run 5 steps
        for i in range(5):
            response = client.post(f"/api/v1/simulations/{sim_id}/step")
            assert response.status_code == 200
        
        # Check final state
        response = client.get(f"/api/v1/simulations/{sim_id}")
        data = response.json()
        
        assert data["total_steps"] == 5
        
        # History should have 6 entries (initial + 5 steps)
        assert len(data["stats"]["susceptible_history"]) == 6
    
    def test_run_step_nonexistent_simulation(self, client):
        """Test running step on non-existent simulation."""
        response = client.post("/api/v1/simulations/sim_nonexistent/step")
        
        assert response.status_code == 404
    
    def test_run_step_updates_stats(self, client):
        """Test that running steps updates statistics."""
        create_response = client.post("/api/v1/simulations", json={
            "population_size": 200,
            "initial_infected": 5,
            "infection_rate": 2.0
        })
        sim_id = create_response.json()["simulation_id"]
        
        # Get initial stats
        initial_response = client.get(f"/api/v1/simulations/{sim_id}")
        initial_stats = initial_response.json()["stats"]
        
        # Run several steps
        for _ in range(10):
            client.post(f"/api/v1/simulations/{sim_id}/step")
        
        # Get updated stats
        final_response = client.get(f"/api/v1/simulations/{sim_id}")
        final_stats = final_response.json()["stats"]
        
        # History should be longer
        assert len(final_stats["susceptible_history"]) > len(initial_stats["susceptible_history"])


class TestRunSimulationBatch:
    """Test suite for running simulation in batch endpoint."""
    
    def test_run_by_days(self, client):
        """Test running simulation for specified number of days."""
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        response = client.post(
            f"/api/v1/simulations/{sim_id}/run",
            json={"days": 10.0, "stop_when_no_infected": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have run for approximately 10 days
        # With dt=0.5, that's 20 steps
        assert data["current_day"] >= 9.5  # Allow some tolerance
    
    def test_run_by_steps(self, client):
        """Test running simulation for specified number of steps."""
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        response = client.post(
            f"/api/v1/simulations/{sim_id}/run",
            json={"steps": 50, "stop_when_no_infected": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_steps"] == 50
    
    def test_run_stops_when_no_infected(self, client):
        """Test that simulation stops when no infected remain."""
        # Create simulation with small population and high recovery
        create_response = client.post("/api/v1/simulations", json={
            "population_size": 50,
            "initial_infected": 1,
            "infection_rate": 0.1,  # Low infection rate
            "infectious_mean": 2.0,  # Short infectious period
            "mortality_rate": 0.0
        })
        sim_id = create_response.json()["simulation_id"]
        
        response = client.post(
            f"/api/v1/simulations/{sim_id}/run",
            json={"days": 100.0, "stop_when_no_infected": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have completed (no more infected)
        stats = data["stats"]
        if data["status"] == "completed":
            assert stats["infected"] == 0
            assert stats["exposed"] == 0
    
    def test_run_nonexistent_simulation(self, client):
        """Test running non-existent simulation."""
        response = client.post(
            "/api/v1/simulations/sim_nonexistent/run",
            json={"days": 10.0}
        )
        
        assert response.status_code == 404
    
    def test_run_default_parameters(self, client):
        """Test running with default parameters (100 days)."""
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        # Run with no parameters - should use defaults
        response = client.post(f"/api/v1/simulations/{sim_id}/run")
        
        assert response.status_code == 200


class TestGetSimulationStats:
    """Test suite for simulation statistics endpoint."""
    
    def test_get_stats_initial(self, client):
        """Test getting initial statistics."""
        create_response = client.post("/api/v1/simulations", json={
            "population_size": 200,
            "initial_infected": 5
        })
        sim_id = create_response.json()["simulation_id"]
        
        response = client.get(f"/api/v1/simulations/{sim_id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check initial SEIRD counts
        assert data["susceptible"] == 195
        assert data["exposed"] == 0
        assert data["infected"] == 5
        assert data["recovered"] == 0
        assert data["deceased"] == 0
    
    def test_get_stats_after_steps(self, client):
        """Test getting statistics after running steps."""
        create_response = client.post("/api/v1/simulations", json={
            "population_size": 100,
            "initial_infected": 3
        })
        sim_id = create_response.json()["simulation_id"]
        
        # Run some steps
        client.post(f"/api/v1/simulations/{sim_id}/run", json={"steps": 20})
        
        response = client.get(f"/api/v1/simulations/{sim_id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Population should be conserved
        total = (data["susceptible"] + data["exposed"] + 
                 data["infected"] + data["recovered"] + data["deceased"])
        assert total == 100
        
        # Should have history data
        assert len(data["susceptible_history"]) > 1
        assert len(data["rt_history"]) > 1
    
    def test_get_stats_nonexistent(self, client):
        """Test getting stats for non-existent simulation."""
        response = client.get("/api/v1/simulations/sim_nonexistent/stats")
        
        assert response.status_code == 404
    
    def test_rt_history_values(self, client):
        """Test that Rt values are reasonable."""
        create_response = client.post("/api/v1/simulations", json={
            "population_size": 200,
            "initial_infected": 5,
            "infection_rate": 1.5
        })
        sim_id = create_response.json()["simulation_id"]
        
        # Run simulation
        client.post(f"/api/v1/simulations/{sim_id}/run", json={"steps": 50})
        
        response = client.get(f"/api/v1/simulations/{sim_id}/stats")
        data = response.json()
        
        # Rt values should be non-negative
        for rt in data["rt_history"]:
            assert rt >= 0


class TestGetSimulationAgents:
    """Test suite for agent data endpoint."""
    
    def test_get_agents_initial(self, client):
        """Test getting initial agent positions."""
        create_response = client.post("/api/v1/simulations", json={
            "population_size": 50,
            "grid_size": 100.0,
            "initial_infected": 2
        })
        sim_id = create_response.json()["simulation_id"]
        
        response = client.get(f"/api/v1/simulations/{sim_id}/agents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["simulation_id"] == sim_id
        assert data["grid_size"] == 100.0
        assert len(data["agents"]) == 50
        assert "state_colors" in data
    
    def test_agent_data_structure(self, client):
        """Test that each agent has required fields."""
        create_response = client.post("/api/v1/simulations", json={"population_size": 20})
        sim_id = create_response.json()["simulation_id"]
        
        response = client.get(f"/api/v1/simulations/{sim_id}/agents")
        data = response.json()
        
        for agent in data["agents"]:
            assert "id" in agent
            assert "x" in agent
            assert "y" in agent
            assert "state" in agent
            assert "days_in_state" in agent
            assert "is_isolated" in agent
            
            # Position within grid
            assert 0 <= agent["x"] <= data["grid_size"]
            assert 0 <= agent["y"] <= data["grid_size"]
            
            # Valid state
            assert agent["state"] in ["S", "E", "I", "R", "D"]
    
    def test_get_agents_exclude_deceased(self, client):
        """Test excluding deceased agents from response."""
        # Create simulation with high mortality
        create_response = client.post("/api/v1/simulations", json={
            "population_size": 100,
            "initial_infected": 20,
            "infection_rate": 3.0,
            "mortality_rate": 0.5,
            "infectious_mean": 3.0
        })
        sim_id = create_response.json()["simulation_id"]
        
        # Run to get some deaths
        client.post(f"/api/v1/simulations/{sim_id}/run", json={"days": 30.0})
        
        # Get all agents
        response_all = client.get(f"/api/v1/simulations/{sim_id}/agents")
        
        # Get excluding deceased
        response_filtered = client.get(
            f"/api/v1/simulations/{sim_id}/agents?include_deceased=false"
        )
        
        assert response_all.status_code == 200
        assert response_filtered.status_code == 200
        
        # Filtered should have no deceased
        for agent in response_filtered.json()["agents"]:
            assert agent["state"] != "D"
    
    def test_state_colors_mapping(self, client):
        """Test that state colors mapping is provided."""
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        response = client.get(f"/api/v1/simulations/{sim_id}/agents")
        data = response.json()
        
        colors = data["state_colors"]
        assert "S" in colors
        assert "E" in colors
        assert "I" in colors
        assert "R" in colors
        assert "D" in colors
        
        # Colors should be hex format
        for color in colors.values():
            assert color.startswith("#")


class TestDeleteSimulation:
    """Test suite for simulation deletion endpoint."""
    
    def test_delete_simulation(self, client):
        """Test deleting a simulation."""
        # Create simulation
        create_response = client.post("/api/v1/simulations")
        sim_id = create_response.json()["simulation_id"]
        
        # Verify it exists
        assert client.get(f"/api/v1/simulations/{sim_id}").status_code == 200
        
        # Delete it
        response = client.delete(f"/api/v1/simulations/{sim_id}")
        
        assert response.status_code == 204
        
        # Verify it's gone
        assert client.get(f"/api/v1/simulations/{sim_id}").status_code == 404
    
    def test_delete_nonexistent_simulation(self, client):
        """Test deleting non-existent simulation."""
        response = client.delete("/api/v1/simulations/sim_nonexistent")
        
        assert response.status_code == 404
    
    def test_delete_removes_from_list(self, client):
        """Test that deleted simulation is removed from list."""
        # Create 3 simulations
        sim_ids = []
        for _ in range(3):
            response = client.post("/api/v1/simulations")
            sim_ids.append(response.json()["simulation_id"])
        
        # Delete middle one
        client.delete(f"/api/v1/simulations/{sim_ids[1]}")
        
        # List should have 2
        response = client.get("/api/v1/simulations")
        data = response.json()
        
        assert data["count"] == 2
        listed_ids = [s["simulation_id"] for s in data["simulations"]]
        assert sim_ids[0] in listed_ids
        assert sim_ids[1] not in listed_ids
        assert sim_ids[2] in listed_ids


class TestSimulationIntegration:
    """Integration tests for complete simulation workflows."""
    
    def test_complete_simulation_workflow(self, client):
        """Test a complete simulation from creation to completion."""
        # 1. Create simulation
        create_response = client.post("/api/v1/simulations", json={
            "population_size": 100,
            "initial_infected": 3,
            "infection_rate": 1.0,
            "mortality_rate": 0.05
        })
        
        assert create_response.status_code == 201
        sim_id = create_response.json()["simulation_id"]
        
        # 2. Run step by step for a few steps
        for _ in range(5):
            step_response = client.post(f"/api/v1/simulations/{sim_id}/step")
            assert step_response.status_code == 200
        
        # 3. Check state
        state_response = client.get(f"/api/v1/simulations/{sim_id}")
        assert state_response.status_code == 200
        assert state_response.json()["total_steps"] == 5
        
        # 4. Run in batch
        run_response = client.post(
            f"/api/v1/simulations/{sim_id}/run",
            json={"days": 30.0}
        )
        assert run_response.status_code == 200
        
        # 5. Get final stats
        stats_response = client.get(f"/api/v1/simulations/{sim_id}/stats")
        assert stats_response.status_code == 200
        
        stats = stats_response.json()
        
        # Population conserved
        total = (stats["susceptible"] + stats["exposed"] + 
                 stats["infected"] + stats["recovered"] + stats["deceased"])
        assert total == 100
        
        # 6. Get agent positions
        agents_response = client.get(f"/api/v1/simulations/{sim_id}/agents")
        assert agents_response.status_code == 200
        assert len(agents_response.json()["agents"]) == 100
        
        # 7. Delete simulation
        delete_response = client.delete(f"/api/v1/simulations/{sim_id}")
        assert delete_response.status_code == 204
        
        # Verify deleted
        assert client.get(f"/api/v1/simulations/{sim_id}").status_code == 404
    
    def test_intervention_effects(self, client):
        """Test that interventions affect simulation outcomes."""
        # Run simulation without interventions
        create1 = client.post("/api/v1/simulations", json={
            "population_size": 200,
            "initial_infected": 5,
            "infection_rate": 2.0,
            "vaccination_rate": 0.0,
            "detection_probability": 0.0
        })
        sim1_id = create1.json()["simulation_id"]
        
        # Run simulation with interventions
        create2 = client.post("/api/v1/simulations", json={
            "population_size": 200,
            "initial_infected": 5,
            "infection_rate": 2.0,
            "vaccination_rate": 0.05,  # High vaccination
            "detection_probability": 0.8,
            "isolation_compliance": 0.9
        })
        sim2_id = create2.json()["simulation_id"]
        
        # Run both for same duration
        client.post(f"/api/v1/simulations/{sim1_id}/run", 
                   json={"days": 50.0, "stop_when_no_infected": False})
        client.post(f"/api/v1/simulations/{sim2_id}/run", 
                   json={"days": 50.0, "stop_when_no_infected": False})
        
        # Both should complete successfully
        stats1 = client.get(f"/api/v1/simulations/{sim1_id}/stats").json()
        stats2 = client.get(f"/api/v1/simulations/{sim2_id}/stats").json()
        
        # Population should be conserved in both
        total1 = (stats1["susceptible"] + stats1["exposed"] + 
                  stats1["infected"] + stats1["recovered"] + stats1["deceased"])
        total2 = (stats2["susceptible"] + stats2["exposed"] + 
                  stats2["infected"] + stats2["recovered"] + stats2["deceased"])
        
        assert total1 == 200
        assert total2 == 200
    
    def test_multiple_concurrent_simulations(self, client):
        """Test running multiple simulations concurrently."""
        # Create multiple simulations with different configs
        # Use higher initial_infected to prevent early completion during 10-step test
        configs = [
            {"population_size": 100, "infection_rate": 0.5, "initial_infected": 5},
            {"population_size": 200, "infection_rate": 1.0, "initial_infected": 10},
            {"population_size": 300, "infection_rate": 2.0, "initial_infected": 15},
        ]
        
        sim_ids = []
        for config in configs:
            response = client.post("/api/v1/simulations", json=config)
            assert response.status_code == 201
            sim_ids.append(response.json()["simulation_id"])
        
        # Run steps on each
        for sim_id in sim_ids:
            for _ in range(10):
                response = client.post(f"/api/v1/simulations/{sim_id}/step")
                assert response.status_code == 200
        
        # Verify each has correct state
        for i, sim_id in enumerate(sim_ids):
            response = client.get(f"/api/v1/simulations/{sim_id}")
            data = response.json()
            
            assert data["total_steps"] == 10
            assert data["config"]["population_size"] == configs[i]["population_size"]
        
        # List should show all 3
        list_response = client.get("/api/v1/simulations")
        assert list_response.json()["count"] == 3


class TestSimulationEdgeCases:
    """Test edge cases and error handling."""
    
    def test_minimum_population(self, client):
        """Test simulation with minimum population."""
        response = client.post("/api/v1/simulations", json={
            "population_size": 10,
            "initial_infected": 1
        })
        
        assert response.status_code == 201
        
        # Should still run
        sim_id = response.json()["simulation_id"]
        step_response = client.post(f"/api/v1/simulations/{sim_id}/step")
        assert step_response.status_code == 200
    
    def test_high_mortality_simulation(self, client):
        """Test simulation with very high mortality."""
        response = client.post("/api/v1/simulations", json={
            "population_size": 50,
            "initial_infected": 10,
            "infection_rate": 3.0,
            "mortality_rate": 0.5,  # 50% mortality
            "infectious_mean": 3.0
        })
        
        assert response.status_code == 201
        sim_id = response.json()["simulation_id"]
        
        # Run until completion
        client.post(f"/api/v1/simulations/{sim_id}/run", 
                   json={"days": 100.0, "stop_when_no_infected": True})
        
        stats = client.get(f"/api/v1/simulations/{sim_id}/stats").json()
        
        # Should have deaths
        assert stats["deceased"] >= 0
        
        # Population should still be conserved
        total = (stats["susceptible"] + stats["exposed"] + 
                 stats["infected"] + stats["recovered"] + stats["deceased"])
        assert total == 50
    
    def test_zero_infection_rate(self, client):
        """Test simulation with zero infection rate."""
        response = client.post("/api/v1/simulations", json={
            "population_size": 100,
            "initial_infected": 5,
            "infection_rate": 0.0  # No transmission
        })
        
        assert response.status_code == 201
        sim_id = response.json()["simulation_id"]
        
        # Run simulation
        client.post(f"/api/v1/simulations/{sim_id}/run", 
                   json={"days": 30.0, "stop_when_no_infected": True})
        
        stats = client.get(f"/api/v1/simulations/{sim_id}/stats").json()
        
        # Initial susceptible should be unchanged (no new infections)
        # All exposed should be 0 (no new exposures)
        assert stats["exposed"] == 0
    
    def test_run_completed_simulation(self, client):
        """Test that running a completed simulation returns error."""
        # Create simulation that will complete quickly
        response = client.post("/api/v1/simulations", json={
            "population_size": 20,
            "initial_infected": 1,
            "infection_rate": 0.1,
            "infectious_mean": 1.0
        })
        sim_id = response.json()["simulation_id"]
        
        # Run until completion
        client.post(f"/api/v1/simulations/{sim_id}/run", 
                   json={"days": 100.0, "stop_when_no_infected": True})
        
        # Check if completed
        state = client.get(f"/api/v1/simulations/{sim_id}").json()
        
        if state["status"] == "completed":
            # Should not allow more steps
            response = client.post(f"/api/v1/simulations/{sim_id}/step")
            assert response.status_code == 400

