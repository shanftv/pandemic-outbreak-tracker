"""
test cases for simulation integration

tests cover edge cases and boundary conditions for:
- parameter validation
- epidemic metrics calculations
- data transformations
- simulation statistics
"""

import pytest
import numpy as np
from api.services.simulation_service import SimulationService
from api.services.stats_utils import EpidemicStats
from api.services.data_transform import SimulationTransformer
from api.models.schemas import (
    SimulationConfig,
    SimulationStatistics,
    EpidemicMetrics,
)


class TestSimulationParameterValidation:
    """test parameter validation edge cases"""

    def setup_method(self):
        """set up test fixtures"""
        self.service = SimulationService()

    def test_minimum_population(self):
        """test minimum population size"""
        config = SimulationConfig(
            population_size=50,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert is_valid, f"Valid config rejected: {error}"

    def test_population_below_minimum(self):
        """test population below minimum threshold"""
        config = SimulationConfig(
            population_size=49,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid, "Should reject population < 50"
        assert "population" in error.lower()

    def test_population_above_maximum(self):
        """test population above maximum threshold"""
        config = SimulationConfig(
            population_size=5001,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid, "Should reject population > 5000"

    def test_zero_mortality_rate(self):
        """test zero mortality rate (valid edge case)"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            mortality_rate=0.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert is_valid, "Zero mortality should be valid"

    def test_100_percent_mortality(self):
        """test 100% mortality rate"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            mortality_rate=1.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert is_valid, "100% mortality should be valid"

    def test_mortality_above_100_percent(self):
        """test mortality rate > 100%"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            mortality_rate=1.1,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid, "Mortality > 100% should be invalid"

    def test_zero_vaccination_rate(self):
        """test zero vaccination rate"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            vaccination_rate=0.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert is_valid, "Zero vaccination should be valid"

    def test_100_percent_vaccination(self):
        """test 100% daily vaccination rate"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            vaccination_rate=1.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert is_valid, "100% vaccination should be valid"

    def test_initial_infected_exceeds_population(self):
        """test initial infected exceeds population"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            initial_infected=101,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid, "Initial infected > population should be invalid"

    def test_zero_initial_infected(self):
        """test zero initial infected"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            initial_infected=0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid, "Zero initial infected should be invalid"

    def test_disease_duration_exceeds_year(self):
        """test disease duration > 1 year"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=300.0,
            infectious_mean=100.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid, "Disease duration > 365 days should be invalid"

    def test_minimum_time_step(self):
        """test minimum time step"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            time_step=0.01,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert is_valid, "Small time step should be valid"

    def test_time_step_too_large(self):
        """test time step > 1 day"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=1.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
            time_step=1.5,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid, "Time step > 1 should be invalid"

    def test_zero_infection_rate(self):
        """test zero infection rate"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=0.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert not is_valid, "Zero infection rate should be invalid"

    def test_high_infection_rate(self):
        """test high infection rate"""
        config = SimulationConfig(
            population_size=100,
            grid_size=50,
            infection_rate=10.0,
            incubation_mean=5.0,
            infectious_mean=7.0,
        )
        is_valid, error = self.service.validate_simulation_config(config)
        assert is_valid, "High infection rate should be valid"


class TestEpidemicMetricsCalculation:
    """test epidemic metrics edge cases"""

    def test_rt_with_zero_infected(self):
        """test rt calculation with no infections"""
        infected = [0, 0, 0, 0, 0]
        rt = EpidemicStats.calculate_rt(infected, infectious_period=7, time_step=0.5)
        assert rt == 0.0, "Rt should be 0 with no infections"

    def test_rt_with_stable_infections(self):
        """test rt with stable infected count"""
        infected = [10, 10, 10, 10, 10]
        rt = EpidemicStats.calculate_rt(infected, infectious_period=7, time_step=0.5)
        assert abs(rt - 1.0) < 0.1, "Rt should be ~1 with stable infections"

    def test_rt_with_exponential_growth(self):
        """test rt with exponential growth"""
        # exponential growth with r=2
        infected = [1, 2, 4, 8, 16, 32]
        rt = EpidemicStats.calculate_rt(infected, infectious_period=7, time_step=1.0)
        assert rt > 1.0, "Rt should be > 1 with exponential growth"

    def test_r0_estimation_early_phase(self):
        """test r0 estimation from early phase"""
        # simulated early exponential phase
        infected = [1, 2, 4, 8, 16, 20, 22, 24]
        r0 = EpidemicStats.estimate_r0(infected, infectious_period=7, time_step=1.0)
        assert 1.0 <= r0 <= 5.0, "R0 should be in reasonable range"

    def test_r0_with_no_growth(self):
        """test r0 with minimal infections"""
        infected = [1, 1, 1, 1]
        r0 = EpidemicStats.estimate_r0(infected, infectious_period=7, time_step=1.0)
        assert r0 >= 1.0, "R0 should be >= 1"

    def test_doubling_time_with_growth(self):
        """test doubling time calculation"""
        infected = [10, 12, 15, 20, 25, 30]
        doubling_time = EpidemicStats.calculate_doubling_time(infected, time_step=1.0)
        assert doubling_time is not None, "Should calculate doubling time"
        assert doubling_time > 0, "Doubling time should be positive"

    def test_doubling_time_no_growth(self):
        """test doubling time with no growth"""
        infected = [10, 10, 10, 10]
        doubling_time = EpidemicStats.calculate_doubling_time(infected, time_step=1.0)
        assert doubling_time is None, "Should return None when no doubling"

    def test_attack_rate_full_outbreak(self):
        """test attack rate with full outbreak"""
        attack_rate = EpidemicStats.calculate_attack_rate(
            susceptible_start=100, susceptible_end=10, deceased=5
        )
        assert 85 <= attack_rate <= 95, "Attack rate should reflect ~90% infected"

    def test_attack_rate_no_outbreak(self):
        """test attack rate with no outbreak"""
        attack_rate = EpidemicStats.calculate_attack_rate(
            susceptible_start=100, susceptible_end=100, deceased=0
        )
        assert attack_rate == 0.0, "Attack rate should be 0 with no infections"

    def test_cfr_100_percent(self):
        """test cfr with 100% mortality"""
        cfr = EpidemicStats.calculate_case_fatality_rate(total_infected=50, total_deceased=50)
        assert abs(cfr - 100.0) < 0.01, "CFR should be 100%"

    def test_cfr_zero_percent(self):
        """test cfr with no deaths"""
        cfr = EpidemicStats.calculate_case_fatality_rate(total_infected=50, total_deceased=0)
        assert cfr == 0.0, "CFR should be 0%"

    def test_cfr_with_zero_infected(self):
        """test cfr calculation with no infected"""
        cfr = EpidemicStats.calculate_case_fatality_rate(total_infected=0, total_deceased=0)
        assert cfr == 0.0, "CFR should be 0 with no infected"

    def test_growth_rate_positive(self):
        """test growth rate with increasing infections"""
        infected = [10, 12, 14, 16, 18]
        growth = EpidemicStats.calculate_growth_rate(infected, time_step=1.0)
        assert growth > 0, "Growth rate should be positive"

    def test_growth_rate_negative(self):
        """test growth rate with decreasing infections"""
        infected = [20, 18, 15, 12, 10]
        growth = EpidemicStats.calculate_growth_rate(infected, time_step=1.0)
        assert growth < 0, "Growth rate should be negative"

    def test_peak_metrics_calculation(self):
        """test peak infection calculation"""
        infected = [1, 5, 10, 20, 50, 30, 10, 2, 0]
        peak_count, peak_day = EpidemicStats.calculate_peak_metrics(infected, time_step=1.0)
        assert peak_count == 50, f"Peak should be 50, got {peak_count}"
        assert peak_day == 4, f"Peak day should be 4, got {peak_day}"

    def test_epidemic_duration_calculation(self):
        """test outbreak duration calculation"""
        infected = [0, 1, 5, 10, 5, 1, 0, 0]
        duration = EpidemicStats.calculate_epidemic_duration(infected, time_step=1.0)
        assert 5 <= duration <= 6, "Duration should be ~5-6 days"

    def test_trend_increasing(self):
        """test trend detection - increasing"""
        metrics = [1.0, 1.2, 1.4, 1.5, 1.6]
        trend = EpidemicStats.calculate_trend(metrics)
        assert trend == "increasing", "Should detect increasing trend"

    def test_trend_decreasing(self):
        """test trend detection - decreasing"""
        metrics = [1.5, 1.2, 1.0, 0.9, 0.8]
        trend = EpidemicStats.calculate_trend(metrics)
        assert trend == "decreasing", "Should detect decreasing trend"

    def test_trend_stable(self):
        """test trend detection - stable"""
        metrics = [1.0, 1.0, 1.05, 0.95, 1.0]
        trend = EpidemicStats.calculate_trend(metrics)
        assert trend == "stable", "Should detect stable trend"


class TestDataTransformation:
    """test data transformation edge cases"""

    def test_agent_to_geojson_feature(self):
        """test single agent to geojson conversion"""
        agent = {
            "id": 1,
            "x": 50,
            "y": 50,
            "state": "I",
            "days_in_state": 3,
            "is_isolated": False,
        }
        feature = SimulationTransformer.agent_to_geojson_feature(agent)
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        assert feature["properties"]["agent_id"] == 1
        assert feature["properties"]["state"] == "I"

    def test_agents_to_geojson_empty(self):
        """test empty agents list"""
        geojson = SimulationTransformer.agents_to_geojson(
            [], "test_loc", "Test Location"
        )
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 0
        assert geojson["properties"]["agent_count"] == 0

    def test_agents_to_geojson_multiple(self):
        """test multiple agents conversion"""
        agents = [
            {"id": i, "x": i, "y": i, "state": "S", "days_in_state": 0, "is_isolated": False}
            for i in range(10)
        ]
        geojson = SimulationTransformer.agents_to_geojson(
            agents, "test_loc", "Test Location"
        )
        assert len(geojson["features"]) == 10

    def test_statistics_pivot_table(self):
        """test seird pivot table creation"""
        stats = {
            "susceptible": [100, 95, 90, 85],
            "exposed": [0, 3, 6, 9],
            "infected": [0, 1, 3, 5],
            "recovered": [0, 1, 1, 1],
            "deceased": [0, 0, 0, 0],
        }
        pivot = SimulationTransformer.create_seird_pivot_table(stats, time_step=1.0)
        assert len(pivot) == 4
        assert all("day" in row for row in pivot)
        assert pivot[0]["day"] == 0
        assert pivot[3]["day"] == 3

    def test_risk_score_calculation_low(self):
        """test risk score - low risk scenario"""
        score = SimulationTransformer.calculate_risk_score(
            infected_percentage=5,
            growth_rate=-0.1,
            rt=0.8,
            doubling_time=20,
        )
        assert 0 <= score <= 30, "Low risk scenario should score low"

    def test_risk_score_calculation_high(self):
        """test risk score - high risk scenario"""
        score = SimulationTransformer.calculate_risk_score(
            infected_percentage=30,
            growth_rate=0.3,
            rt=2.5,
            doubling_time=2,
        )
        assert score > 50, "High risk scenario should score high"

    def test_danger_zone_geojson_critical(self):
        """test danger zone with critical risk"""
        feature = SimulationTransformer.create_danger_zone_geojson(
            location_id="test",
            location_name="Test",
            latitude=14.5,
            longitude=120.9,
            risk_score=85,
            agent_density=100,
            infected_percentage=50,
        )
        assert feature["properties"]["danger_level"] == "critical"
        assert feature["properties"]["color"] == "#F44336"

    def test_agent_statistics_empty(self):
        """test agent statistics with no agents"""
        stats = SimulationTransformer.aggregate_agent_statistics([])
        assert stats["total_agents"] == 0
        assert stats["isolation_rate"] == 0

    def test_agent_statistics_with_isolated(self):
        """test agent statistics with isolated agents"""
        agents = [
            {"state": "I", "days_in_state": 5, "is_isolated": True},
            {"state": "I", "days_in_state": 3, "is_isolated": False},
            {"state": "S", "days_in_state": 0, "is_isolated": False},
        ]
        stats = SimulationTransformer.aggregate_agent_statistics(agents)
        assert stats["total_agents"] == 3
        assert stats["isolated_count"] == 1
        assert abs(stats["isolation_rate"] - 1/3) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
