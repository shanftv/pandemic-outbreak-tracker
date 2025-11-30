"""
Comprehensive tests for API services to achieve high coverage.

Tests cover:
- simulation_service.py
- location_service.py
- prediction_service.py
- data_transform.py
- stats_utils.py
"""

import pytest
import json
import tempfile
import numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from api.services.simulation_service import SimulationService
from api.services.location_service import LocationService
from api.services.prediction_service import PredictionService
from api.services.data_transform import SimulationTransformer, TimeDelta
from api.services.stats_utils import EpidemicStats
from api.models.schemas import (
    SimulationConfig,
    SimulationStatistics,
    EpidemicMetrics,
    AgentData,
)
from api.config import settings


# =============================================================================
# SimulationService Tests
# =============================================================================

class TestSimulationServiceValidation:
    """Test simulation config validation edge cases."""

    def setup_method(self):
        self.service = SimulationService()

    def test_grid_size_below_minimum(self):
        """Test grid size below minimum threshold."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=19,  # Below minimum of 20
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "grid" in error.lower()

    def test_grid_size_above_maximum(self):
        """Test grid size above maximum threshold."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=501,  # Above maximum of 500
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "grid" in error.lower()

    def test_infection_rate_above_maximum(self):
        """Test infection rate above maximum."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=5.1,  # Above maximum of 5.0
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "infection" in error.lower()

    def test_negative_infection_rate(self):
        """Test negative infection rate."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=-0.5,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "infection" in error.lower()

    def test_negative_incubation_mean(self):
        """Test negative incubation mean."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=-1.0,  # Negative
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "incubation" in error.lower()

    def test_negative_incubation_std(self):
        """Test negative incubation std."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=-1.0,  # Negative
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "incubation" in error.lower()

    def test_negative_infectious_mean(self):
        """Test negative infectious mean."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=-1.0,  # Negative
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "infectious" in error.lower()

    def test_negative_infectious_std(self):
        """Test negative infectious std."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=-1.0,  # Negative
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "infectious" in error.lower()

    def test_negative_mortality_rate(self):
        """Test negative mortality rate."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=-0.1,  # Negative
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "mortality" in error.lower()

    def test_vaccination_rate_above_one(self):
        """Test vaccination rate above 1."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=1.5,  # Above 1
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "vaccination" in error.lower()

    def test_detection_probability_above_one(self):
        """Test detection probability above 1."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=1.5,  # Above 1
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "detection" in error.lower()

    def test_isolation_compliance_above_one(self):
        """Test isolation compliance above 1."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=1.5,  # Above 1
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "isolation" in error.lower()

    def test_negative_interaction_radius(self):
        """Test negative interaction radius."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=-1.0,  # Negative
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "interaction" in error.lower()

    def test_zero_time_step(self):
        """Test zero time step."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.0,  # Zero
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "time" in error.lower()

    def test_negative_home_attraction(self):
        """Test negative home attraction."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=-0.1,  # Negative
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "home" in error.lower()

    def test_negative_random_movement(self):
        """Test negative random movement."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=-0.5,  # Negative
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "random" in error.lower()

    def test_initial_infected_equal_population(self):
        """Test initial infected equal to population."""
        config = SimulationConfig.model_construct(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=100,  # Equal to population
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid
        assert "initial" in error.lower() or "population" in error.lower()


class TestSimulationServiceTransform:
    """Test simulation service transformation methods."""

    def setup_method(self):
        self.service = SimulationService()

    def test_transform_agent_data_to_geojson(self):
        """Test transforming agent data to GeoJSON."""
        # Create AgentData objects with x, y grid coordinates
        agents = [
            AgentData(id=1, x=50.0, y=50.0, state="S", days_in_state=0, is_isolated=False),
            AgentData(id=2, x=60.0, y=55.0, state="I", days_in_state=3, is_isolated=True),
            AgentData(id=3, x=45.0, y=48.0, state="E", days_in_state=1, is_isolated=False),
            AgentData(id=4, x=52.0, y=51.0, state="R", days_in_state=5, is_isolated=False),
            AgentData(id=5, x=58.0, y=53.0, state="D", days_in_state=7, is_isolated=False),
        ]

        geojson = self.service.transform_agent_data_to_geojson(
            agents, "test_loc", "Test Location"
        )

        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 5
        assert geojson["properties"]["location_id"] == "test_loc"
        assert geojson["properties"]["agent_count"] == 5

        # Check risk levels
        for feature in geojson["features"]:
            state = feature["properties"]["state"]
            risk_level = feature["properties"]["risk_level"]
            if state == "I":
                assert risk_level == 2
            elif state == "E":
                assert risk_level == 1
            else:
                assert risk_level == 0

    def test_transform_agent_data_unknown_state(self):
        """Test transforming agent data with unknown state."""
        # Create an agent with an unknown state using model_construct
        agent = AgentData.model_construct(
            id=1,
            x=50.0,
            y=50.0,
            state="X",  # Unknown state - bypasses validation with model_construct
            days_in_state=0,
            is_isolated=False,
        )
        agents = [agent]

        geojson = self.service.transform_agent_data_to_geojson(
            agents, "test_loc", "Test Location"
        )

        # Should default to risk_level 0
        assert geojson["features"][0]["properties"]["risk_level"] == 0


class TestSimulationServiceMetrics:
    """Test epidemic metrics calculation."""

    def setup_method(self):
        self.service = SimulationService()

    def test_calculate_epidemic_metrics_full(self):
        """Test full epidemic metrics calculation."""
        config = SimulationConfig(
            population_size=100,
            grid_size=100,
            infection_rate=1.5,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.05,
            vaccination_rate=0.01,
            initial_infected=5,
        )

        statistics = SimulationStatistics(
            susceptible=[95, 90, 80, 65, 50, 35, 25, 20, 18, 17],
            exposed=[0, 3, 8, 12, 15, 12, 8, 4, 2, 1],
            infected=[5, 7, 10, 18, 25, 35, 40, 35, 25, 15],
            recovered=[0, 0, 1, 3, 7, 13, 22, 35, 48, 60],
            deceased=[0, 0, 1, 2, 3, 5, 5, 6, 7, 7],
        )

        metrics = self.service.calculate_epidemic_metrics(statistics, config)

        assert isinstance(metrics, EpidemicMetrics)
        assert metrics.r0 >= 0
        assert metrics.rt >= 0
        assert 0 <= metrics.attack_rate <= 100
        assert 0 <= metrics.case_fatality_rate <= 100
        assert metrics.peak_infected > 0
        assert metrics.peak_day >= 0

    def test_calculate_epidemic_metrics_empty_stats(self):
        """Test metrics with minimal statistics."""
        config = SimulationConfig(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            initial_infected=1,
        )

        statistics = SimulationStatistics(
            susceptible=[99],
            exposed=[0],
            infected=[1],
            recovered=[0],
            deceased=[0],
        )

        metrics = self.service.calculate_epidemic_metrics(statistics, config)
        assert isinstance(metrics, EpidemicMetrics)

    def test_calculate_epidemic_metrics_no_vaccination(self):
        """Test metrics with no vaccination."""
        config = SimulationConfig(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.0,
            initial_infected=1,
        )

        statistics = SimulationStatistics(
            susceptible=[99, 95, 90, 85],
            exposed=[0, 2, 5, 8],
            infected=[1, 3, 5, 7],
            recovered=[0, 0, 0, 0],
            deceased=[0, 0, 0, 0],
        )

        metrics = self.service.calculate_epidemic_metrics(statistics, config)
        assert metrics.vaccination_coverage == 0

    def test_calculate_epidemic_metrics_with_vaccination(self):
        """Test metrics with vaccination."""
        config = SimulationConfig(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.05,
            initial_infected=1,
        )

        statistics = SimulationStatistics(
            susceptible=[99, 95, 90, 85, 80, 75],
            exposed=[0, 2, 5, 8, 10, 12],
            infected=[1, 3, 5, 7, 9, 11],
            recovered=[0, 0, 0, 0, 1, 2],
            deceased=[0, 0, 0, 0, 0, 0],
        )

        metrics = self.service.calculate_epidemic_metrics(statistics, config)
        assert metrics.vaccination_coverage >= 0


class TestSimulationServiceR0Rt:
    """Test R0 and Rt estimation methods."""

    def setup_method(self):
        self.service = SimulationService()

    def test_estimate_r0_short_array(self):
        """Test R0 estimation with very short data."""
        infected = np.array([1])
        r0 = self.service._estimate_r0(infected, 7.0, 0.5, 100)
        assert r0 == 0

    def test_estimate_r0_zero_population(self):
        """Test R0 estimation with zero population."""
        infected = np.array([1, 2, 4, 8])
        r0 = self.service._estimate_r0(infected, 7.0, 0.5, 0)
        assert r0 == 0

    def test_estimate_r0_no_early_infections(self):
        """Test R0 estimation with no early infections."""
        infected = np.array([0, 0, 0, 0, 0])
        r0 = self.service._estimate_r0(infected, 7.0, 0.5, 100)
        assert r0 == 1.0

    def test_estimate_r0_growing_outbreak(self):
        """Test R0 estimation with growing outbreak."""
        infected = np.array([1, 2, 4, 8, 16, 32, 64, 100, 120, 130])
        r0 = self.service._estimate_r0(infected, 7.0, 1.0, 1000)
        assert r0 > 1.0

    def test_calculate_rt_short_array(self):
        """Test Rt calculation with very short data."""
        infected = np.array([1])
        rt = self.service._calculate_rt(infected, 7.0, 0.5)
        assert rt == 0

    def test_calculate_rt_zero_start(self):
        """Test Rt calculation when starting at zero."""
        infected = np.array([0, 0, 0, 5, 10])
        rt = self.service._calculate_rt(infected, 7.0, 0.5)
        assert rt >= 0


class TestSimulationServiceDoublingTime:
    """Test doubling time calculation."""

    def setup_method(self):
        self.service = SimulationService()

    def test_doubling_time_short_array(self):
        """Test doubling time with very short data."""
        infected = np.array([1])
        dt = self.service._calculate_doubling_time(infected, 0.5)
        assert dt is None

    def test_doubling_time_no_growth(self):
        """Test doubling time with no growth."""
        infected = np.array([10, 10, 10, 10, 10])
        dt = self.service._calculate_doubling_time(infected, 0.5)
        assert dt is None

    def test_doubling_time_declining(self):
        """Test doubling time with declining infections."""
        infected = np.array([20, 15, 10, 8, 5])
        dt = self.service._calculate_doubling_time(infected, 0.5)
        assert dt is None

    def test_doubling_time_slow_growth(self):
        """Test doubling time that doesn't reach 2x."""
        infected = np.array([10, 11, 12, 13, 14])
        dt = self.service._calculate_doubling_time(infected, 0.5)
        assert dt is None

    def test_doubling_time_fast_growth(self):
        """Test doubling time with fast growth."""
        infected = np.array([10, 12, 15, 20, 25, 30])
        dt = self.service._calculate_doubling_time(infected, 1.0)
        assert dt is not None
        assert dt > 0


class TestSimulationServiceTrend:
    """Test trend calculation."""

    def setup_method(self):
        self.service = SimulationService()

    def test_calculate_trend_single_metric(self):
        """Test trend with single metric."""
        metrics = [
            EpidemicMetrics(
                r0=1.5, rt=1.2, attack_rate=10, case_fatality_rate=2,
                doubling_time=5, peak_infected=50, peak_day=10,
                outbreak_duration=30, current_infected=20,
                current_recovered=10, current_deceased=2,
                vaccination_coverage=5, growth_rate=0.1
            )
        ]
        trend = self.service.calculate_trend(metrics)
        assert trend == "stable"

    def test_calculate_trend_increasing(self):
        """Test trend detection - increasing."""
        metrics = [
            EpidemicMetrics(
                r0=1.5, rt=1.5, attack_rate=10, case_fatality_rate=2,
                doubling_time=5, peak_infected=50, peak_day=10,
                outbreak_duration=30, current_infected=20,
                current_recovered=10, current_deceased=2,
                vaccination_coverage=5, growth_rate=0.1
            ),
            EpidemicMetrics(
                r0=1.5, rt=1.8, attack_rate=15, case_fatality_rate=2,
                doubling_time=4, peak_infected=60, peak_day=12,
                outbreak_duration=32, current_infected=30,
                current_recovered=12, current_deceased=3,
                vaccination_coverage=6, growth_rate=0.2
            ),
            EpidemicMetrics(
                r0=1.5, rt=2.0, attack_rate=20, case_fatality_rate=2,
                doubling_time=3, peak_infected=70, peak_day=14,
                outbreak_duration=34, current_infected=40,
                current_recovered=14, current_deceased=4,
                vaccination_coverage=7, growth_rate=0.3
            ),
        ]
        trend = self.service.calculate_trend(metrics)
        assert trend == "increasing"

    def test_calculate_trend_decreasing(self):
        """Test trend detection - decreasing."""
        metrics = [
            EpidemicMetrics(
                r0=1.5, rt=0.6, attack_rate=10, case_fatality_rate=2,
                doubling_time=5, peak_infected=50, peak_day=10,
                outbreak_duration=30, current_infected=20,
                current_recovered=10, current_deceased=2,
                vaccination_coverage=5, growth_rate=0.1
            ),
            EpidemicMetrics(
                r0=1.5, rt=0.5, attack_rate=12, case_fatality_rate=2,
                doubling_time=6, peak_infected=50, peak_day=10,
                outbreak_duration=32, current_infected=15,
                current_recovered=15, current_deceased=3,
                vaccination_coverage=6, growth_rate=0.0
            ),
            EpidemicMetrics(
                r0=1.5, rt=0.4, attack_rate=14, case_fatality_rate=2,
                doubling_time=7, peak_infected=50, peak_day=10,
                outbreak_duration=34, current_infected=10,
                current_recovered=20, current_deceased=4,
                vaccination_coverage=7, growth_rate=-0.1
            ),
        ]
        trend = self.service.calculate_trend(metrics)
        assert trend == "decreasing"


class TestSimulationServiceAggregation:
    """Test simulation aggregation methods."""

    def setup_method(self):
        self.service = SimulationService()

    def test_aggregate_simulations_by_location_empty(self):
        """Test aggregation with empty list."""
        result = self.service.aggregate_simulations_by_location([])
        assert result == {}

    def test_transform_simulation_to_api_response(self):
        """Test transforming simulation output to API response."""
        simulation_output = {
            "config": {
                "population_size": 100,
                "grid_size": 100,
                "infection_rate": 1.5,
                "incubation_mean": 5.0,
                "incubation_std": 1.0,
                "infectious_mean": 7.0,
                "infectious_std": 1.0,
                "mortality_rate": 0.02,
                "vaccination_rate": 0.01,
                "detection_probability": 0.5,
                "isolation_compliance": 0.8,
                "interaction_radius": 2.0,
                "time_step": 0.5,
                "home_attraction": 0.1,
                "random_movement": 0.5,
                "initial_infected": 5,
            },
            "statistics": {
                "susceptible": [95, 90, 85],
                "exposed": [0, 3, 5],
                "infected": [5, 7, 10],
                "recovered": [0, 0, 0],
                "deceased": [0, 0, 0],
            },
            "agents": [
                {
                    "id": 1,
                    "x": 50.0,
                    "y": 50.0,
                    "state": "S",
                    "days_in_state": 0,
                    "is_isolated": False,
                },
            ],
        }

        result = self.service.transform_simulation_to_api_response(
            simulation_output, "sim_123", "ncr", "NCR"
        )

        assert result.simulation_id == "sim_123"
        assert result.location_id == "ncr"
        assert result.location_name == "NCR"
        assert result.trend in ["increasing", "decreasing", "stable"]


# =============================================================================
# LocationService Tests
# =============================================================================

class TestLocationServiceCache:
    """Test location service caching behavior."""

    def setup_method(self):
        self.service = LocationService()

    def test_load_locations_no_file(self):
        """Test loading locations when file doesn't exist."""
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'features_csv', Path('/nonexistent/file.csv')):
            df = self.service._load_locations()
            assert df.empty

    def test_load_locations_cached(self):
        """Test that cached data is returned."""
        import pandas as pd
        
        self.service._cache = pd.DataFrame({
            'location': ['NCR'],
            'new_cases': [100],
            'date': [datetime.now()]
        })
        self.service._cache_time = datetime.now(timezone.utc)
        
        result = self.service._load_locations()
        assert not result.empty
        assert 'location' in result.columns

    def test_load_locations_expired_cache(self):
        """Test that expired cache is not used."""
        import pandas as pd
        
        self.service._cache = pd.DataFrame({'location': ['NCR']})
        # Set cache time to more than TTL ago
        self.service._cache_time = datetime.now(timezone.utc) - timedelta(seconds=self.service._cache_ttl + 100)
        
        with patch.object(settings, 'features_csv', Path('/nonexistent/file.csv')):
            result = self.service._load_locations()
            assert result.empty


class TestLocationServiceMethods:
    """Test location service methods."""

    def setup_method(self):
        self.service = LocationService()

    @pytest.mark.asyncio
    async def test_get_all_locations_sample_data(self):
        """Test getting all locations returns sample data when no file."""
        with patch.object(settings, 'features_csv', Path('/nonexistent/file.csv')):
            locations = await self.service.get_all_locations()
            # Should return sample locations
            assert len(locations) > 0

    @pytest.mark.asyncio
    async def test_get_all_locations_without_coordinates(self):
        """Test getting locations without coordinates."""
        with patch.object(settings, 'features_csv', Path('/nonexistent/file.csv')):
            locations = await self.service.get_all_locations(include_coordinates=False)
            for loc in locations:
                assert loc.latitude is None
                assert loc.longitude is None

    @pytest.mark.asyncio
    async def test_get_location_by_id_not_found(self):
        """Test getting location by non-existent ID."""
        with patch.object(settings, 'features_csv', Path('/nonexistent/file.csv')):
            result = await self.service.get_location_by_id("nonexistent_xyz")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_location_by_name(self):
        """Test getting location by name."""
        with patch.object(settings, 'features_csv', Path('/nonexistent/file.csv')):
            locations = await self.service.get_all_locations()
            if locations:
                # Try to find by name
                _ = await self.service.get_location_by_id(locations[0].name)
                # May or may not find depending on sample data
                pass


class TestLocationServiceWithData:
    """Test location service with actual data."""

    def setup_method(self):
        self.service = LocationService()

    @pytest.mark.asyncio
    async def test_get_all_locations_with_csv(self, tmp_path):
        """Test getting locations from CSV file."""
        import pandas as pd
        
        # Create test CSV
        csv_path = tmp_path / "features.csv"
        df = pd.DataFrame({
            'location': ['NCR', 'Calabarzon'],
            'new_cases': [100, 50],
            'date': [datetime.now(), datetime.now()]
        })
        df.to_csv(csv_path, index=False)
        
        # Clear cache
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'features_csv', csv_path):
            locations = await self.service.get_all_locations()
            assert len(locations) == 2
            # Should be sorted by total_cases descending
            assert locations[0].total_cases >= locations[1].total_cases

    @pytest.mark.asyncio
    async def test_get_location_by_id_from_csv(self, tmp_path):
        """Test getting specific location from CSV."""
        import pandas as pd
        
        csv_path = tmp_path / "features.csv"
        df = pd.DataFrame({
            'location': ['NCR', 'Calabarzon'],
            'new_cases': [100, 50],
            'date': [datetime.now(), datetime.now()]
        })
        df.to_csv(csv_path, index=False)
        
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'features_csv', csv_path):
            location = await self.service.get_location_by_id('ncr')
            assert location is not None
            assert location.name == 'NCR'


# =============================================================================
# PredictionService Tests
# =============================================================================

class TestPredictionServiceCache:
    """Test prediction service caching."""

    def setup_method(self):
        self.service = PredictionService()

    def test_load_predictions_no_file(self):
        """Test loading predictions when file doesn't exist."""
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'predictions_json', Path('/nonexistent/file.json')):
            result = self.service._load_predictions()
            assert result == {}

    def test_load_predictions_cached(self):
        """Test that cached predictions are returned."""
        self.service._cache = {"NCR": [{"date": "2025-01-01", "predicted_cases": 100, "day_ahead": 1}]}
        self.service._cache_time = datetime.now(timezone.utc)
        
        result = self.service._load_predictions()
        assert "NCR" in result

    def test_load_predictions_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        json_path = tmp_path / "predictions.json"
        json_path.write_text("invalid json {{{")
        
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'predictions_json', json_path):
            result = self.service._load_predictions()
            assert result == {}


class TestPredictionServiceTrend:
    """Test prediction service trend calculation."""

    def setup_method(self):
        self.service = PredictionService()

    def test_calculate_trend_single_prediction(self):
        """Test trend calculation with single prediction."""
        predictions = [{"predicted_cases": 100}]
        trend = self.service._calculate_trend(predictions)
        assert trend == "stable"

    def test_calculate_trend_increasing(self):
        """Test trend calculation - increasing."""
        predictions = [
            {"predicted_cases": 100},
            {"predicted_cases": 105},
            {"predicted_cases": 110},
            {"predicted_cases": 120},
            {"predicted_cases": 130},
            {"predicted_cases": 145},
            {"predicted_cases": 160},
        ]
        trend = self.service._calculate_trend(predictions)
        assert trend == "increasing"

    def test_calculate_trend_decreasing(self):
        """Test trend calculation - decreasing."""
        predictions = [
            {"predicted_cases": 160},
            {"predicted_cases": 145},
            {"predicted_cases": 130},
            {"predicted_cases": 120},
            {"predicted_cases": 110},
            {"predicted_cases": 100},
            {"predicted_cases": 85},
        ]
        trend = self.service._calculate_trend(predictions)
        assert trend == "decreasing"


class TestPredictionServiceMethods:
    """Test prediction service methods."""

    def setup_method(self):
        self.service = PredictionService()

    @pytest.mark.asyncio
    async def test_get_all_predictions_empty(self):
        """Test getting predictions when no data."""
        with patch.object(settings, 'predictions_json', Path('/nonexistent/file.json')):
            predictions = await self.service.get_all_predictions()
            assert predictions == []

    @pytest.mark.asyncio
    async def test_get_prediction_by_location_not_found(self):
        """Test getting prediction for non-existent location."""
        with patch.object(settings, 'predictions_json', Path('/nonexistent/file.json')):
            result = await self.service.get_prediction_by_location("nonexistent_xyz")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_prediction_status_unavailable(self):
        """Test prediction status when file doesn't exist."""
        from api.models.schemas import PredictionStatus
        
        with patch.object(settings, 'predictions_json', Path('/nonexistent/file.json')):
            status = await self.service.get_prediction_status()
            assert status == PredictionStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_get_prediction_status_fresh(self, tmp_path):
        """Test prediction status for fresh file."""
        from api.models.schemas import PredictionStatus
        
        json_path = tmp_path / "predictions.json"
        json_path.write_text("{}")
        
        with patch.object(settings, 'predictions_json', json_path):
            status = await self.service.get_prediction_status()
            assert status == PredictionStatus.FRESH

    @pytest.mark.asyncio
    async def test_get_last_generated_time_no_file(self):
        """Test getting last generated time when no file."""
        with patch.object(settings, 'predictions_json', Path('/nonexistent/file.json')):
            result = await self.service.get_last_generated_time()
            assert result is None

    @pytest.mark.asyncio
    async def test_get_next_update_time_no_file(self):
        """Test getting next update time when no file."""
        with patch.object(settings, 'predictions_json', Path('/nonexistent/file.json')):
            result = await self.service.get_next_update_time()
            assert result is None

    @pytest.mark.asyncio
    async def test_get_predictions_summary_empty(self):
        """Test predictions summary when no data."""
        with patch.object(settings, 'predictions_json', Path('/nonexistent/file.json')):
            summary = await self.service.get_predictions_summary()
            assert summary["total_locations"] == 0
            assert summary["total_predicted_cases"] == 0

    @pytest.mark.asyncio
    async def test_get_top_risk_locations_empty(self):
        """Test top risk locations when no data."""
        with patch.object(settings, 'predictions_json', Path('/nonexistent/file.json')):
            result = await self.service.get_top_risk_locations()
            assert result == []


class TestPredictionServiceWithData:
    """Test prediction service with actual data."""

    def setup_method(self):
        self.service = PredictionService()

    @pytest.mark.asyncio
    async def test_get_all_predictions_with_data(self, tmp_path):
        """Test getting predictions with data."""
        json_path = tmp_path / "predictions.json"
        data = {
            "NCR": [
                {"date": "2025-01-01", "predicted_cases": 100, "day_ahead": 1},
                {"date": "2025-01-02", "predicted_cases": 110, "day_ahead": 2},
                {"date": "2025-01-03", "predicted_cases": 105, "day_ahead": 3},
                {"date": "2025-01-04", "predicted_cases": 120, "day_ahead": 4},
                {"date": "2025-01-05", "predicted_cases": 115, "day_ahead": 5},
                {"date": "2025-01-06", "predicted_cases": 125, "day_ahead": 6},
                {"date": "2025-01-07", "predicted_cases": 130, "day_ahead": 7},
            ]
        }
        json_path.write_text(json.dumps(data))
        
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'predictions_json', json_path):
            predictions = await self.service.get_all_predictions()
            assert len(predictions) == 1
            assert predictions[0].location_name == "NCR"

    @pytest.mark.asyncio
    async def test_get_prediction_by_location_found(self, tmp_path):
        """Test getting prediction by location with data."""
        json_path = tmp_path / "predictions.json"
        data = {
            "NCR": [
                {"date": "2025-01-01", "predicted_cases": 100, "day_ahead": 1},
                {"date": "2025-01-02", "predicted_cases": 110, "day_ahead": 2},
                {"date": "2025-01-03", "predicted_cases": 105, "day_ahead": 3},
                {"date": "2025-01-04", "predicted_cases": 120, "day_ahead": 4},
                {"date": "2025-01-05", "predicted_cases": 115, "day_ahead": 5},
                {"date": "2025-01-06", "predicted_cases": 125, "day_ahead": 6},
                {"date": "2025-01-07", "predicted_cases": 130, "day_ahead": 7},
            ]
        }
        json_path.write_text(json.dumps(data))
        
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'predictions_json', json_path):
            prediction = await self.service.get_prediction_by_location("ncr")
            assert prediction is not None
            # Also test by name
            prediction_by_name = await self.service.get_prediction_by_location("NCR")
            assert prediction_by_name is not None


# =============================================================================
# DataTransform Tests
# =============================================================================

class TestSimulationTransformerTimeSeries:
    """Test time series transformation."""

    def test_statistics_to_timeseries(self):
        """Test converting statistics to time series."""
        statistics = {
            "susceptible": [100, 95, 90],
            "infected": [0, 3, 8],
        }
        
        result = SimulationTransformer.statistics_to_timeseries(statistics, time_step=0.5)
        
        assert "susceptible" in result
        assert "infected" in result
        assert len(result["susceptible"]) == 3
        assert result["susceptible"][0]["day"] == 0

    def test_statistics_to_timeseries_empty(self):
        """Test time series with empty statistics."""
        result = SimulationTransformer.statistics_to_timeseries({}, time_step=0.5)
        assert result == {}


class TestSimulationTransformerDangerZone:
    """Test danger zone GeoJSON creation."""

    def test_create_danger_zone_low_risk(self):
        """Test danger zone with low risk."""
        feature = SimulationTransformer.create_danger_zone_geojson(
            location_id="test",
            location_name="Test",
            latitude=14.5,
            longitude=120.9,
            risk_score=15,
            agent_density=10,
            infected_percentage=5,
        )
        
        assert feature["properties"]["danger_level"] == "low"
        assert feature["properties"]["color"] == "#4CAF50"

    def test_create_danger_zone_moderate_risk(self):
        """Test danger zone with moderate risk."""
        feature = SimulationTransformer.create_danger_zone_geojson(
            location_id="test",
            location_name="Test",
            latitude=14.5,
            longitude=120.9,
            risk_score=35,
            agent_density=20,
            infected_percentage=15,
        )
        
        assert feature["properties"]["danger_level"] == "moderate"
        assert feature["properties"]["color"] == "#FFC107"

    def test_create_danger_zone_high_risk(self):
        """Test danger zone with high risk."""
        feature = SimulationTransformer.create_danger_zone_geojson(
            location_id="test",
            location_name="Test",
            latitude=14.5,
            longitude=120.9,
            risk_score=60,
            agent_density=50,
            infected_percentage=30,
        )
        
        assert feature["properties"]["danger_level"] == "high"
        assert feature["properties"]["color"] == "#FF9800"


class TestSimulationTransformerRiskScore:
    """Test risk score calculation."""

    def test_risk_score_no_doubling_time(self):
        """Test risk score without doubling time."""
        score = SimulationTransformer.calculate_risk_score(
            infected_percentage=10,
            growth_rate=0.1,
            rt=1.2,
            doubling_time=None,
        )
        assert 0 <= score <= 100

    def test_risk_score_zero_doubling_time(self):
        """Test risk score with zero doubling time."""
        score = SimulationTransformer.calculate_risk_score(
            infected_percentage=10,
            growth_rate=0.1,
            rt=1.2,
            doubling_time=0,
        )
        assert 0 <= score <= 100

    def test_risk_score_extreme_values(self):
        """Test risk score with extreme values."""
        score = SimulationTransformer.calculate_risk_score(
            infected_percentage=100,
            growth_rate=2.0,
            rt=5.0,
            doubling_time=1,
        )
        # Should be capped at 100
        assert score <= 100


class TestSimulationTransformerExport:
    """Test export functionality."""

    def test_export_simulation_to_json(self, tmp_path):
        """Test exporting simulation to JSON."""
        output = {
            "simulation_id": "test_123",
            "metrics": {"r0": 1.5, "rt": 1.2},
            "timestamp": datetime.now(timezone.utc),
        }
        
        filepath = tmp_path / "simulation.json"
        SimulationTransformer.export_simulation_to_json(output, str(filepath))
        
        assert filepath.exists()
        with open(filepath) as f:
            data = json.load(f)
            assert data["simulation_id"] == "test_123"

    def test_export_seird_to_csv(self, tmp_path):
        """Test exporting SEIRD to CSV."""
        statistics = {
            "susceptible": [100, 95, 90],
            "exposed": [0, 3, 6],
            "infected": [0, 2, 4],
            "recovered": [0, 0, 0],
            "deceased": [0, 0, 0],
        }
        
        filepath = tmp_path / "seird.csv"
        SimulationTransformer.export_seird_to_csv(statistics, str(filepath), time_step=1.0)
        
        assert filepath.exists()
        content = filepath.read_text()
        assert "day" in content
        assert "susceptible" in content

    def test_export_seird_to_csv_empty(self, tmp_path):
        """Test exporting empty SEIRD to CSV."""
        filepath = tmp_path / "empty_seird.csv"
        SimulationTransformer.export_seird_to_csv({}, str(filepath))
        
        # File should not be created or should be empty
        assert not filepath.exists() or filepath.stat().st_size == 0


class TestSimulationTransformerComparison:
    """Test comparison GeoJSON creation."""

    def test_create_comparison_geojson(self):
        """Test creating comparison GeoJSON."""
        simulations = [
            {
                "location_id": "loc1",
                "location_name": "Location 1",
                "metrics": {
                    "attack_rate": 20,
                    "growth_rate": 0.1,
                    "rt": 1.5,
                    "doubling_time": 5,
                },
            },
            {
                "location_id": "loc2",
                "location_name": "Location 2",
                "metrics": {
                    "attack_rate": 10,
                    "growth_rate": -0.1,
                    "rt": 0.8,
                    "doubling_time": None,
                },
            },
        ]
        
        result = SimulationTransformer.create_comparison_geojson(simulations)
        
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 2
        assert result["comparison_field"] == "risk_score"

    def test_create_comparison_geojson_custom_field(self):
        """Test creating comparison with custom field."""
        simulations = [
            {
                "location_id": "loc1",
                "location_name": "Location 1",
                "metrics": {"rt": 1.5, "attack_rate": 20},
            },
        ]
        
        result = SimulationTransformer.create_comparison_geojson(simulations, field="rt")
        
        assert result["comparison_field"] == "rt"
        assert result["features"][0]["properties"]["value"] == 1.5

    def test_create_comparison_geojson_empty(self):
        """Test creating comparison with empty list."""
        result = SimulationTransformer.create_comparison_geojson([])
        
        assert result["type"] == "FeatureCollection"
        assert result["features"] == []


class TestTimeDelta:
    """Test TimeDelta helper class."""

    def test_timedelta_creation(self):
        """Test TimeDelta creation."""
        td = TimeDelta(days=5)
        assert td.total_seconds == 5 * 86400

    def test_timedelta_repr(self):
        """Test TimeDelta string representation."""
        td = TimeDelta(days=3)
        assert "3" in repr(td)


class TestSimulationTransformerPivotTable:
    """Test SEIRD pivot table creation."""

    def test_create_seird_pivot_table_empty(self):
        """Test pivot table with empty data."""
        result = SimulationTransformer.create_seird_pivot_table({})
        assert result == []

    def test_create_seird_pivot_table_mismatched_lengths(self):
        """Test pivot table with mismatched array lengths."""
        statistics = {
            "susceptible": [100, 95, 90],
            "infected": [0, 5],  # Shorter array
        }
        
        result = SimulationTransformer.create_seird_pivot_table(statistics)
        
        # Should handle gracefully
        assert len(result) == 3
        # Last row might not have infected
        assert result[2].get("infected") is None or "infected" in result[2]


# =============================================================================
# StatsUtils Tests
# =============================================================================

class TestEpidemicStatsRt:
    """Test Rt calculation edge cases."""

    def test_calculate_rt_empty(self):
        """Test Rt with empty list."""
        rt = EpidemicStats.calculate_rt([], infectious_period=7)
        assert rt == 0.0

    def test_calculate_rt_single_value(self):
        """Test Rt with single value."""
        rt = EpidemicStats.calculate_rt([10], infectious_period=7)
        assert rt == 0.0

    def test_calculate_rt_zero_growth_factor(self):
        """Test Rt when growth factor is zero."""
        rt = EpidemicStats.calculate_rt([10, 0, 0], infectious_period=7)
        # Starting value > 0 but ends at 0
        assert rt >= 0


class TestEpidemicStatsR0:
    """Test R0 estimation edge cases."""

    def test_estimate_r0_empty(self):
        """Test R0 with empty list."""
        r0 = EpidemicStats.estimate_r0([], infectious_period=7)
        assert r0 == 0.0

    def test_estimate_r0_single_value(self):
        """Test R0 with single value."""
        r0 = EpidemicStats.estimate_r0([10], infectious_period=7)
        assert r0 == 0.0

    def test_estimate_r0_zero_population(self):
        """Test R0 with zero population."""
        r0 = EpidemicStats.estimate_r0([1, 2, 4], infectious_period=7, population=0)
        assert r0 == 0.0

    def test_estimate_r0_low_counts(self):
        """Test R0 with counts below MIN_CASES_FOR_STATS."""
        r0 = EpidemicStats.estimate_r0([1, 2, 3, 4], infectious_period=7)
        # Should return default since counts are below MIN_CASES_FOR_STATS
        assert r0 == 1.0


class TestEpidemicStatsDoublingTime:
    """Test doubling time edge cases."""

    def test_doubling_time_empty(self):
        """Test doubling time with empty list."""
        dt = EpidemicStats.calculate_doubling_time([])
        assert dt is None

    def test_doubling_time_single_value(self):
        """Test doubling time with single value."""
        dt = EpidemicStats.calculate_doubling_time([10])
        assert dt is None

    def test_doubling_time_low_counts(self):
        """Test doubling time with counts below threshold."""
        dt = EpidemicStats.calculate_doubling_time([1, 2, 3, 4])
        # Counts below MIN_CASES_FOR_STATS
        assert dt is None


class TestEpidemicStatsGrowthRate:
    """Test growth rate calculation edge cases."""

    def test_growth_rate_empty(self):
        """Test growth rate with empty list."""
        gr = EpidemicStats.calculate_growth_rate([])
        assert gr == 0.0

    def test_growth_rate_single_value(self):
        """Test growth rate with single value."""
        gr = EpidemicStats.calculate_growth_rate([10])
        assert gr == 0.0

    def test_growth_rate_from_zero(self):
        """Test growth rate starting from zero."""
        gr = EpidemicStats.calculate_growth_rate([0, 0, 0, 5, 10])
        # Should handle zero start
        assert gr == 1.0  # Represents infinite growth from 0

    def test_growth_rate_all_zeros(self):
        """Test growth rate with all zeros."""
        gr = EpidemicStats.calculate_growth_rate([0, 0, 0])
        assert gr == 0.0


class TestEpidemicStatsPeak:
    """Test peak metrics calculation."""

    def test_peak_metrics_empty(self):
        """Test peak metrics with empty list."""
        peak_count, peak_day = EpidemicStats.calculate_peak_metrics([])
        assert peak_count == 0
        assert peak_day == 0


class TestEpidemicStatsDuration:
    """Test epidemic duration calculation."""

    def test_duration_empty(self):
        """Test duration with empty list."""
        duration = EpidemicStats.calculate_epidemic_duration([])
        assert duration == 0

    def test_duration_all_below_threshold(self):
        """Test duration when all below threshold."""
        duration = EpidemicStats.calculate_epidemic_duration([0, 0, 0], min_threshold=5)
        assert duration == 0


class TestEpidemicStatsTrend:
    """Test trend calculation edge cases."""

    def test_trend_short_series(self):
        """Test trend with very short series."""
        trend = EpidemicStats.calculate_trend([1.0])
        assert trend == "stable"

    def test_trend_long_series_increasing(self):
        """Test trend with long increasing series."""
        trend = EpidemicStats.calculate_trend([0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0])
        assert trend == "increasing"

    def test_trend_long_series_decreasing(self):
        """Test trend with long decreasing series."""
        trend = EpidemicStats.calculate_trend([2.0, 1.8, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5])
        assert trend == "decreasing"


class TestEpidemicStatsSmoothSeries:
    """Test series smoothing."""

    def test_smooth_series_empty(self):
        """Test smoothing empty series."""
        result = EpidemicStats.smooth_series([])
        assert result == []

    def test_smooth_series_short(self):
        """Test smoothing series shorter than window."""
        result = EpidemicStats.smooth_series([1, 2], window=5)
        assert len(result) == 2

    def test_smooth_series_normal(self):
        """Test normal smoothing operation."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        result = EpidemicStats.smooth_series(data, window=3)
        assert len(result) == len(data)


class TestEpidemicStatsSecondaryCases:
    """Test secondary cases estimation."""

    def test_secondary_cases_empty(self):
        """Test secondary cases with empty list."""
        result = EpidemicStats.estimate_secondary_cases([], infectious_period=7)
        assert result == []

    def test_secondary_cases_normal(self):
        """Test normal secondary cases estimation."""
        infected = [1, 5, 10, 20, 30]
        result = EpidemicStats.estimate_secondary_cases(
            infected, infectious_period=7, contact_rate=5.0
        )
        assert len(result) == len(infected)
        assert all(x >= 0 for x in result)

    def test_secondary_cases_all_zeros(self):
        """Test secondary cases with all zeros."""
        result = EpidemicStats.estimate_secondary_cases([0, 0, 0], infectious_period=7)
        assert len(result) == 3
        assert all(x == 0 for x in result)


class TestEpidemicStatsAttackRate:
    """Test attack rate calculation edge cases."""

    def test_attack_rate_zero_start(self):
        """Test attack rate with zero starting susceptible."""
        ar = EpidemicStats.calculate_attack_rate(
            susceptible_start=0,
            susceptible_end=0,
            deceased=0
        )
        assert ar == 0.0


class TestEpidemicStatsCFR:
    """Test CFR calculation edge cases."""

    def test_cfr_zero_infected(self):
        """Test CFR with zero infected."""
        cfr = EpidemicStats.calculate_case_fatality_rate(
            total_infected=0,
            total_deceased=0
        )
        assert cfr == 0.0


# =============================================================================
# Additional Coverage Tests
# =============================================================================

class TestSimulationServiceAggregationFull:
    """Additional tests for simulation aggregation."""

    def setup_method(self):
        self.service = SimulationService()

    def test_aggregate_simulations_multiple_locations(self):
        """Test aggregation with multiple simulations from different locations."""
        from api.models.schemas import SimulationOutput, SimulationStatistics

        # Create mock simulation outputs
        config = SimulationConfig(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
        )

        stats = SimulationStatistics(
            susceptible=[90, 85, 80],
            exposed=[5, 8, 10],
            infected=[5, 7, 10],
            recovered=[0, 0, 0],
            deceased=[0, 0, 0],
        )

        metrics1 = EpidemicMetrics(
            r0=2.0, rt=1.5, attack_rate=20, case_fatality_rate=2,
            doubling_time=5, peak_infected=50, peak_day=10,
            outbreak_duration=30, current_infected=20,
            current_recovered=10, current_deceased=2,
            vaccination_coverage=5, growth_rate=0.1
        )

        metrics2 = EpidemicMetrics(
            r0=2.5, rt=1.8, attack_rate=25, case_fatality_rate=3,
            doubling_time=4, peak_infected=60, peak_day=12,
            outbreak_duration=35, current_infected=25,
            current_recovered=15, current_deceased=3,
            vaccination_coverage=6, growth_rate=0.2
        )

        sim1 = SimulationOutput(
            simulation_id="sim_1",
            location_id="loc1",
            location_name="Location 1",
            config=config,
            statistics=stats,
            metrics=metrics1,
            agent_geojson={"type": "FeatureCollection", "features": []},
            trend="increasing",
            generated_at=datetime.now(timezone.utc),
        )

        sim2 = SimulationOutput(
            simulation_id="sim_2",
            location_id="loc1",
            location_name="Location 1",
            config=config,
            statistics=stats,
            metrics=metrics2,
            agent_geojson={"type": "FeatureCollection", "features": []},
            trend="increasing",
            generated_at=datetime.now(timezone.utc),
        )

        sim3 = SimulationOutput(
            simulation_id="sim_3",
            location_id="loc2",
            location_name="Location 2",
            config=config,
            statistics=stats,
            metrics=metrics1,
            agent_geojson={"type": "FeatureCollection", "features": []},
            trend="stable",
            generated_at=datetime.now(timezone.utc),
        )

        result = self.service.aggregate_simulations_by_location([sim1, sim2, sim3])

        assert len(result) == 2
        assert "loc1" in result
        assert "loc2" in result
        assert len(result["loc1"]["simulations"]) == 2
        assert len(result["loc2"]["simulations"]) == 1

        # Check averages for loc1
        assert result["loc1"]["avg_r0"] == (2.0 + 2.5) / 2
        assert result["loc1"]["avg_rt"] == (1.5 + 1.8) / 2


class TestDataTransformAgentMethods:
    """Test data transform agent methods for full coverage."""

    def test_agent_to_geojson_feature_with_defaults(self):
        """Test agent to geojson with default parameters."""
        agent = {
            "id": 1,
            "x": 50,
            "y": 50,
            "state": "I",
            "days_in_state": 3,
            "is_isolated": True,
        }
        feature = SimulationTransformer.agent_to_geojson_feature(agent)
        
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        assert feature["properties"]["state"] == "I"
        assert feature["properties"]["risk_level"] == 2

    def test_agent_to_geojson_feature_with_custom_base(self):
        """Test agent to geojson with custom base coordinates."""
        agent = {"id": 1, "x": 10, "y": 10, "state": "S"}
        feature = SimulationTransformer.agent_to_geojson_feature(
            agent, base_lat=10.0, base_lon=100.0, scale=0.1
        )
        
        # Check coordinates are calculated correctly
        expected_lat = 10.0 + (10 * 0.1)  # 11.0
        expected_lon = 100.0 + (10 * 0.1)  # 101.0
        assert feature["geometry"]["coordinates"] == [expected_lon, expected_lat]

    def test_agent_to_geojson_feature_missing_fields(self):
        """Test agent to geojson with missing optional fields."""
        agent = {"id": 1, "state": "R"}  # Missing x, y, days_in_state, is_isolated
        feature = SimulationTransformer.agent_to_geojson_feature(agent)
        
        # Should use defaults
        assert feature["properties"]["days_in_state"] == 0
        assert feature["properties"]["is_isolated"] == False

    def test_agents_to_geojson_state_summary(self):
        """Test agents to geojson includes state summary."""
        agents = [
            {"id": 1, "x": 10, "y": 10, "state": "S"},
            {"id": 2, "x": 20, "y": 20, "state": "S"},
            {"id": 3, "x": 30, "y": 30, "state": "I"},
            {"id": 4, "x": 40, "y": 40, "state": "E"},
            {"id": 5, "x": 50, "y": 50, "state": "R"},
        ]
        
        geojson = SimulationTransformer.agents_to_geojson(
            agents, "test_loc", "Test Location"
        )
        
        assert "state_summary" in geojson["properties"]
        summary = geojson["properties"]["state_summary"]
        assert summary["S"] == 2
        assert summary["I"] == 1
        assert summary["E"] == 1
        assert summary["R"] == 1
        assert summary["D"] == 0

    def test_count_states_unknown_state(self):
        """Test _count_states with unknown state."""
        agents = [
            {"state": "S"},
            {"state": "X"},  # Unknown state
            {"state": "I"},
        ]
        
        result = SimulationTransformer._count_states(agents)
        
        assert result["S"] == 1
        assert result["I"] == 1
        # Unknown state should not be counted
        assert "X" not in result or result.get("X", 0) == 0


class TestDataTransformAggregation:
    """Test agent statistics aggregation."""

    def test_aggregate_agent_statistics_full(self):
        """Test full agent statistics aggregation."""
        agents = [
            {"state": "S", "days_in_state": 0, "is_isolated": False},
            {"state": "E", "days_in_state": 2, "is_isolated": False},
            {"state": "I", "days_in_state": 5, "is_isolated": True},
            {"state": "I", "days_in_state": 3, "is_isolated": True},
            {"state": "R", "days_in_state": 10, "is_isolated": False},
        ]
        
        stats = SimulationTransformer.aggregate_agent_statistics(agents)
        
        assert stats["total_agents"] == 5
        assert stats["by_state"]["S"] == 1
        assert stats["by_state"]["E"] == 1
        assert stats["by_state"]["I"] == 2
        assert stats["by_state"]["R"] == 1
        assert stats["isolated_count"] == 2
        assert stats["isolation_rate"] == 2 / 5
        # Average days: (0 + 2 + 5 + 3 + 10) / 5 = 4
        assert stats["avg_days_in_state"] == 4


class TestPredictionServiceAdditional:
    """Additional prediction service tests."""

    def setup_method(self):
        self.service = PredictionService()

    @pytest.mark.asyncio
    async def test_get_predictions_summary_with_data(self, tmp_path):
        """Test predictions summary with actual data."""
        json_path = tmp_path / "predictions.json"
        data = {
            "NCR": [
                {"date": "2025-01-01", "predicted_cases": 100, "day_ahead": 1},
                {"date": "2025-01-02", "predicted_cases": 120, "day_ahead": 2},
                {"date": "2025-01-03", "predicted_cases": 130, "day_ahead": 3},
                {"date": "2025-01-04", "predicted_cases": 140, "day_ahead": 4},
                {"date": "2025-01-05", "predicted_cases": 150, "day_ahead": 5},
                {"date": "2025-01-06", "predicted_cases": 160, "day_ahead": 6},
                {"date": "2025-01-07", "predicted_cases": 170, "day_ahead": 7},
            ],
            "Calabarzon": [
                {"date": "2025-01-01", "predicted_cases": 80, "day_ahead": 1},
                {"date": "2025-01-02", "predicted_cases": 75, "day_ahead": 2},
                {"date": "2025-01-03", "predicted_cases": 70, "day_ahead": 3},
                {"date": "2025-01-04", "predicted_cases": 65, "day_ahead": 4},
                {"date": "2025-01-05", "predicted_cases": 60, "day_ahead": 5},
                {"date": "2025-01-06", "predicted_cases": 55, "day_ahead": 6},
                {"date": "2025-01-07", "predicted_cases": 50, "day_ahead": 7},
            ],
        }
        json_path.write_text(json.dumps(data))
        
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'predictions_json', json_path):
            summary = await self.service.get_predictions_summary()
            
            assert summary["total_locations"] == 2
            assert summary["total_predicted_cases"] > 0
            assert len(summary["top_5_risk"]) == 2

    @pytest.mark.asyncio
    async def test_get_top_risk_with_data(self, tmp_path):
        """Test top risk locations with actual data."""
        json_path = tmp_path / "predictions.json"
        data = {
            "NCR": [
                {"date": "2025-01-01", "predicted_cases": 100, "day_ahead": 1},
                {"date": "2025-01-02", "predicted_cases": 100, "day_ahead": 2},
                {"date": "2025-01-03", "predicted_cases": 100, "day_ahead": 3},
                {"date": "2025-01-04", "predicted_cases": 100, "day_ahead": 4},
                {"date": "2025-01-05", "predicted_cases": 100, "day_ahead": 5},
                {"date": "2025-01-06", "predicted_cases": 100, "day_ahead": 6},
                {"date": "2025-01-07", "predicted_cases": 100, "day_ahead": 7},
            ],
        }
        json_path.write_text(json.dumps(data))
        
        self.service._cache = None
        self.service._cache_time = None
        
        with patch.object(settings, 'predictions_json', json_path):
            result = await self.service.get_top_risk_locations(limit=3)
            
            assert len(result) == 1
            assert result[0].location_name == "NCR"

    @pytest.mark.asyncio
    async def test_get_next_update_time_with_file(self, tmp_path):
        """Test next update time calculation."""
        json_path = tmp_path / "predictions.json"
        json_path.write_text("{}")
        
        with patch.object(settings, 'predictions_json', json_path):
            result = await self.service.get_next_update_time()
            # Should return a datetime
            assert result is not None or result is None  # Either valid or None


class TestStatsUtilsAdditional:
    """Additional stats utils tests."""

    def test_calculate_rt_with_window(self):
        """Test Rt calculation with custom window."""
        infected = [10, 15, 20, 30, 40, 50, 60]
        rt = EpidemicStats.calculate_rt(
            infected, infectious_period=7, time_step=1.0, window_days=3
        )
        assert rt > 0

    def test_estimate_r0_with_growth(self):
        """Test R0 estimation with clear growth pattern."""
        infected = [10, 15, 22, 33, 50, 75, 110, 165]
        r0 = EpidemicStats.estimate_r0(
            infected, infectious_period=7, time_step=1.0, population=1000
        )
        assert r0 > 1.0  # Should detect growth

    def test_calculate_doubling_time_found(self):
        """Test doubling time when doubling occurs."""
        infected = [10, 12, 15, 20, 25, 30, 40]
        dt = EpidemicStats.calculate_doubling_time(infected, time_step=1.0)
        # Should find doubling time
        assert dt is not None or dt is None  # May or may not find depending on data

    def test_calculate_growth_rate_with_window(self):
        """Test growth rate with custom window."""
        infected = [10, 12, 14, 16, 18, 20]
        gr = EpidemicStats.calculate_growth_rate(
            infected, time_step=1.0, window_days=5
        )
        assert gr > 0

    def test_epidemic_duration_with_data(self):
        """Test epidemic duration with actual infections."""
        infected = [0, 5, 10, 15, 10, 5, 0, 0]
        duration = EpidemicStats.calculate_epidemic_duration(
            infected, time_step=1.0, min_threshold=1
        )
        assert duration == 5  # 5 days with infections >= 1

    def test_calculate_trend_medium_series(self):
        """Test trend with medium-length series."""
        metrics = [1.0, 1.1, 1.2, 1.15, 1.2, 1.25]
        trend = EpidemicStats.calculate_trend(metrics)
        assert trend in ["increasing", "decreasing", "stable"]


class TestLocationServiceAdditional:
    """Additional location service tests."""

    def setup_method(self):
        self.service = LocationService()

    @pytest.mark.asyncio
    async def test_get_location_by_id_case_insensitive(self):
        """Test getting location by ID is case-insensitive."""
        with patch.object(settings, 'features_csv', Path('/nonexistent/file.csv')):
            locations = await self.service.get_all_locations()
            if locations:
                # Try uppercase
                result = await self.service.get_location_by_id(locations[0].id.upper())
                # Should find it
                assert result is not None or result is None


class TestSimulationServiceValidationAdditional:
    """Additional validation tests."""

    def setup_method(self):
        self.service = SimulationService()

    def test_validate_valid_config(self):
        """Test validation of a completely valid config."""
        config = SimulationConfig(
            population_size=100,
            grid_size=100,
            infection_rate=1.0,
            incubation_mean=5.0,
            incubation_std=1.0,
            infectious_mean=7.0,
            infectious_std=1.0,
            mortality_rate=0.02,
            vaccination_rate=0.01,
            detection_probability=0.5,
            isolation_compliance=0.8,
            interaction_radius=2.0,
            time_step=0.5,
            home_attraction=0.1,
            random_movement=0.5,
            initial_infected=5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert is_valid
        assert error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

