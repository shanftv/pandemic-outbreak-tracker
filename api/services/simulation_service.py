"""
simulation service
business logic for processing simulation data and turning it into useful formats.

handles:
- parameter validation to make sure inputs make sense
- data transformation from simulation outputs to api formats
- epidemic metrics (Rt, R0, doubling time, etc.)
- trend analysis and stats
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import numpy as np
from api.models.schemas import (
    SimulationConfig,
    SimulationStatistics,
    EpidemicMetrics,
    AgentData,
    SimulationOutput,
)


class SimulationService:
    """handles simulation data and transformations."""

    # default rt window in days
    RT_WINDOW = 7

    def __init__(self):
        """initialize the service."""
        pass

    def validate_simulation_config(self, config: SimulationConfig) -> Tuple[bool, Optional[str]]:
        """
        Validate simulation configuration parameters.

        Args:
            config: SimulationConfig to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # check population size is reasonable (matches Pydantic: ge=10, le=10000)
        if not (10 <= config.population_size <= 10000):
            return False, "Population size must be between 10 and 10000"

        if not (20 <= config.grid_size <= 500):
            return False, "Grid size must be between 20 and 500"

        # disease parameters need to make sense (matches Pydantic: ge=0.0, le=5.0)
        if not (0 <= config.infection_rate <= 5):
            return False, "Infection rate (beta) must be between 0 and 5"

        if config.incubation_mean <= 0 or config.incubation_std < 0:
            return False, "Incubation period mean must be > 0 and std >= 0"

        if config.infectious_mean <= 0 or config.infectious_std < 0:
            return False, "Infectious period mean must be > 0 and std >= 0"

        if not (0 <= config.mortality_rate <= 1):
            return False, "Mortality rate must be between 0 and 1"

        # intervention rates should be between 0 and 1
        if not (0 <= config.vaccination_rate <= 1):
            return False, "Vaccination rate must be between 0 and 1"

        if not (0 <= config.detection_probability <= 1):
            return False, "Detection probability must be between 0 and 1"

        if not (0 <= config.isolation_compliance <= 1):
            return False, "Isolation compliance must be between 0 and 1"

        # movement/interaction parameters
        if config.interaction_radius <= 0:
            return False, "Interaction radius must be > 0"

        if not (0 < config.time_step <= 1):
            return False, "Time step must be between 0 and 1"

        if config.home_attraction < 0:
            return False, "Home attraction must be >= 0"

        if config.random_movement < 0:
            return False, "Random movement must be >= 0"

        # make sure parameters work together
        if config.incubation_mean + config.infectious_mean > 365:
            return False, "Total disease duration exceeds 1 year"

        # initial_infected must be strictly less than population_size (need at least 1 susceptible)
        if config.initial_infected >= config.population_size:
            return False, "Initial infected must be less than population size"

        if not (1 <= config.initial_infected < config.population_size):
            return False, "Initial infected must be at least 1 and less than population size"

        return True, None

    def transform_agent_data_to_geojson(
        self, agents: List[AgentData], location_id: str, location_name: str
    ) -> Dict:
        """
        Transform agent positions and states to GeoJSON format for danger zones.

        Args:
            agents: List of agent data
            location_id: Location identifier
            location_name: Location display name

        Returns:
            GeoJSON FeatureCollection
        """
        features = []

        for agent in agents:
            # map disease states to how risky they are
            state_to_risk = {
                "S": 0,  # no risk yet
                "E": 1,  # exposed, might get sick
                "I": 2,  # sick and spreading
                "R": 0,  # recovered, safe
                "D": 0,  # gone
            }

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [agent.longitude, agent.latitude],  # GeoJSON uses [lon, lat]
                },
                "properties": {
                    "agent_id": agent.id,
                    "state": agent.state,
                    "risk_level": state_to_risk.get(agent.state, 0),
                    "days_in_state": agent.days_in_state,
                    "is_isolated": agent.is_isolated,
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "location_id": location_id,
                "location_name": location_name,
                "agent_count": len(agents),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    def calculate_epidemic_metrics(
        self, statistics: SimulationStatistics, config: SimulationConfig
    ) -> EpidemicMetrics:
        """
        Calculate epidemic metrics from simulation statistics.

        Args:
            statistics: Simulation statistics (SEIRD counts over time)
            config: Simulation configuration

        Returns:
            EpidemicMetrics object
        """
        s_counts = np.array(statistics.susceptible)
        e_counts = np.array(statistics.exposed)
        i_counts = np.array(statistics.infected)
        r_counts = np.array(statistics.recovered)
        d_counts = np.array(statistics.deceased)

        total_population = config.population_size
        time_steps = len(s_counts)

        # attack rate is what % of people got sick
        total_infected = r_counts[-1] + d_counts[-1]
        attack_rate = (total_infected / total_population) * 100 if total_population > 0 else 0

        # cfr is what % of infected people died
        case_fatality_rate = (
            (d_counts[-1] / total_infected) * 100 if total_infected > 0 else 0
        )

        # r0 is how contagious at the start
        # calculated from early phase growth
        r0 = self._estimate_r0(
            i_counts, config.infectious_mean, config.time_step, total_population
        )

        # rt is how many people are getting infected right now
        rt = self._calculate_rt(i_counts, config.infectious_mean, config.time_step)

        # doubling time is how fast cases are doubling
        doubling_time = self._calculate_doubling_time(i_counts, config.time_step)

        # when did the most people get sick at once
        peak_infected = int(np.max(i_counts)) if len(i_counts) > 0 else 0
        peak_day = (
            int(np.argmax(i_counts) * config.time_step) if len(i_counts) > 0 else 0
        )

        # numbers at the end of simulation
        current_infected = int(i_counts[-1]) if len(i_counts) > 0 else 0
        current_recovered = int(r_counts[-1]) if len(r_counts) > 0 else 0
        current_deceased = int(d_counts[-1]) if len(d_counts) > 0 else 0

        # how many days did the outbreak last
        infected_days = np.sum(i_counts > 0)
        outbreak_duration = int(infected_days * config.time_step)

        # estimate how many got vaccinated
        vaccination_coverage = 0
        if config.vaccination_rate > 0:
            # rough estimate based on vaccination rate
            vaccination_coverage = min(config.vaccination_rate * outbreak_duration * total_population, total_population) / total_population * 100

        # is it going up or down
        if len(i_counts) >= 2:
            recent_infected = i_counts[-7:] if len(i_counts) >= 7 else i_counts
            if len(recent_infected) > 1:
                growth_rate = (recent_infected[-1] - recent_infected[0]) / (
                    recent_infected[0] if recent_infected[0] > 0 else 1
                )
            else:
                growth_rate = 0
        else:
            growth_rate = 0

        return EpidemicMetrics(
            r0=r0,
            rt=rt,
            attack_rate=attack_rate,
            case_fatality_rate=case_fatality_rate,
            doubling_time=doubling_time,
            peak_infected=peak_infected,
            peak_day=peak_day,
            outbreak_duration=outbreak_duration,
            current_infected=current_infected,
            current_recovered=current_recovered,
            current_deceased=current_deceased,
            vaccination_coverage=vaccination_coverage,
            growth_rate=growth_rate,
        )

    def _estimate_r0(
        self, infected_counts: np.ndarray, infectious_period: float, dt: float, population: int
    ) -> float:
        """
        Estimate basic reproduction number (R0).

        Uses early phase infections to estimate average number of secondary cases.

        Args:
            infected_counts: Array of infected counts over time
            infectious_period: Average infectious period in days
            dt: Time step in days
            population: Total population

        Returns:
            Estimated R0
        """
        if len(infected_counts) < 2 or population == 0:
            return 0

        # look at the beginning of the outbreak
        early_phase_end = max(min(len(infected_counts) // 10, 20), 5)
        early_infected = infected_counts[:early_phase_end]

        # Calculate average growth rate in early phase
        if np.max(early_infected) > 0:
            # use exponential growth formula
            valid_indices = np.where(early_infected > 0)[0]
            if len(valid_indices) >= 2:
                i_start = early_infected[valid_indices[0]]
                i_end = early_infected[valid_indices[-1]]
                time_diff = (valid_indices[-1] - valid_indices[0]) * dt

                if time_diff > 0 and i_start > 0:
                    lambda_growth = np.log(i_end / i_start) / time_diff
                    # convert growth rate to r0
                    r0 = 1 + lambda_growth * infectious_period
                    return max(0, r0)

        return 1.0

    def _calculate_rt(
        self, infected_counts: np.ndarray, infectious_period: float, dt: float
    ) -> float:
        """
        Calculate effective reproduction number (Rt).

        Measures current transmission potential.

        Args:
            infected_counts: Array of infected counts over time
            infectious_period: Average infectious period in days
            dt: Time step in days

        Returns:
            Current Rt value
        """
        if len(infected_counts) < 2:
            return 0

        # look at recent data
        window_size = max(int(self.RT_WINDOW / dt), 2)
        recent_infected = infected_counts[-window_size:] if len(infected_counts) >= window_size else infected_counts

        # calculate how fast it's growing
        if len(recent_infected) >= 2 and recent_infected[0] > 0:
            growth_factor = recent_infected[-1] / recent_infected[0]
            time_span = (len(recent_infected) - 1) * dt
            if time_span > 0:
                lambda_growth = np.log(growth_factor) / time_span
                # convert to rt
                rt = 1 + lambda_growth * infectious_period
                return max(0, rt)

        return 1.0

    def _calculate_doubling_time(
        self, infected_counts: np.ndarray, dt: float
    ) -> Optional[float]:
        """
        Calculate doubling time of infections.

        Args:
            infected_counts: Array of infected counts over time
            dt: Time step in days

        Returns:
            Doubling time in days or None if not calculable
        """
        if len(infected_counts) < 2:
            return None

        # find when cases were increasing
        for i in range(1, len(infected_counts)):
            if infected_counts[i] > infected_counts[i - 1] > 0:
                # growth phase found
                growth_indices = np.where(np.array(infected_counts[i:]) > infected_counts[i])[0]

                if len(growth_indices) > 0:
                    endpoint = growth_indices[-1] + i
                    if infected_counts[endpoint] >= 2 * infected_counts[i]:
                        doubling_time = (endpoint - i) * dt
                        return doubling_time

        return None

    def calculate_trend(self, metrics_history: List[EpidemicMetrics]) -> str:
        """
        Calculate trend direction based on metrics history.

        Args:
            metrics_history: List of EpidemicMetrics over time

        Returns:
            Trend string: 'increasing', 'decreasing', or 'stable'
        """
        if len(metrics_history) < 2:
            return "stable"

        # look at recent rt values
        recent_rt = [m.rt for m in metrics_history[-3:]]
        avg_recent = np.mean(recent_rt)

        if avg_recent > 1.1:
            return "increasing"
        elif avg_recent < 0.9:
            return "decreasing"
        else:
            return "stable"

    def transform_simulation_to_api_response(
        self,
        simulation_output: Dict,
        simulation_id: str,
        location_id: str,
        location_name: str,
    ) -> SimulationOutput:
        """
        Transform raw simulation output to API response format.

        Args:
            simulation_output: Raw simulation output dict
            simulation_id: Unique simulation identifier
            location_id: Location identifier
            location_name: Location display name

        Returns:
            SimulationOutput ready for API response
        """
        config = SimulationConfig(**simulation_output.get("config", {}))
        statistics = SimulationStatistics(**simulation_output.get("statistics", {}))
        agents = [AgentData(**agent) for agent in simulation_output.get("agents", [])]

        # do all the calculations
        metrics = self.calculate_epidemic_metrics(statistics, config)

        # convert agent positions to map format
        agent_geojson = self.transform_agent_data_to_geojson(agents, location_id, location_name)

        # check which direction things are going
        trend = self.calculate_trend([metrics])

        return SimulationOutput(
            simulation_id=simulation_id,
            location_id=location_id,
            location_name=location_name,
            config=config,
            statistics=statistics,
            metrics=metrics,
            agent_geojson=agent_geojson,
            trend=trend,
            generated_at=datetime.now(timezone.utc),
        )

    def aggregate_simulations_by_location(
        self, simulations: List[SimulationOutput]
    ) -> Dict[str, Dict]:
        """
        Aggregate simulation metrics by location for dashboard view.

        Args:
            simulations: List of simulation outputs

        Returns:
            Dictionary mapping location_id to aggregated metrics
        """
        aggregated = {}

        for sim in simulations:
            loc_id = sim.location_id
            if loc_id not in aggregated:
                aggregated[loc_id] = {
                    "location_name": sim.location_name,
                    "simulations": [],
                    "avg_r0": 0,
                    "avg_rt": 0,
                    "avg_attack_rate": 0,
                    "total_deceased": 0,
                }

            aggregated[loc_id]["simulations"].append(sim)
            aggregated[loc_id]["avg_r0"] += sim.metrics.r0
            aggregated[loc_id]["avg_rt"] += sim.metrics.rt
            aggregated[loc_id]["avg_attack_rate"] += sim.metrics.attack_rate
            aggregated[loc_id]["total_deceased"] += sim.metrics.current_deceased

        # average the metrics for each location
        for loc_id, data in aggregated.items():
            sim_count = len(data["simulations"])
            if sim_count > 0:
                data["avg_r0"] /= sim_count
                data["avg_rt"] /= sim_count
                data["avg_attack_rate"] /= sim_count

        return aggregated
