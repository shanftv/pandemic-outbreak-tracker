"""
data transformation utilities for simulation output

converts simulation outputs from Simple-Epidemic format to api-friendly formats.
handles:
- agent position data to GeoJSON
- time-series statistics to pandas-compatible formats
- aggregation for dashboard visualizations
- export formats (JSON, CSV)
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import json
import numpy as np


class SimulationTransformer:
    """utilities for transforming simulation data to api formats."""

    @staticmethod
    def agent_to_geojson_feature(
        agent: Dict[str, Any],
        base_lat: float = 14.5,
        base_lon: float = 120.9,
        scale: float = 0.01,
    ) -> Dict[str, Any]:
        """
        transform single agent data to GeoJSON feature.

        args:
            agent: agent data dictionary with at minimum: id, x, y, state
            base_lat: base latitude for location
            base_lon: base longitude for location
            scale: scale factor to convert grid coordinates to lat/lon offset

        returns:
            GeoJSON Feature object
        """
        # state to risk level mapping
        state_risk_map = {"S": 0, "E": 1, "I": 2, "R": 0, "D": 0}

        # convert grid coordinates to lat/lon offsets
        latitude = base_lat + (agent.get("y", 0) * scale)
        longitude = base_lon + (agent.get("x", 0) * scale)

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
            "properties": {
                "agent_id": agent.get("id", 0),
                "state": agent.get("state", "S"),
                "risk_level": state_risk_map.get(agent.get("state", "S"), 0),
                "days_in_state": agent.get("days_in_state", 0),
                "is_isolated": agent.get("is_isolated", False),
            },
        }

        return feature

    @staticmethod
    def agents_to_geojson(
        agents: List[Dict[str, Any]],
        location_id: str,
        location_name: str,
        base_lat: float = 14.5,
        base_lon: float = 120.9,
    ) -> Dict[str, Any]:
        """
        transform all agent data to GeoJSON FeatureCollection.

        args:
            agents: list of agent dictionaries
            location_id: location identifier
            location_name: location display name
            base_lat: base latitude for location
            base_lon: base longitude for location

        returns:
            GeoJSON FeatureCollection
        """
        features = [
            SimulationTransformer.agent_to_geojson_feature(agent, base_lat, base_lon)
            for agent in agents
        ]

        state_summary = SimulationTransformer._count_states(agents)

        # build geojson
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "location_id": location_id,
                "location_name": location_name,
                "agent_count": len(agents),
                "state_summary": state_summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        return geojson

    @staticmethod
    def _count_states(agents: List[Dict[str, Any]]) -> Dict[str, int]:
        """count agents in each SEIRD state."""
        states = {"S": 0, "E": 0, "I": 0, "R": 0, "D": 0}
        for agent in agents:
            state = agent.get("state", "S")
            if state in states:
                states[state] += 1
        return states

    @staticmethod
    def statistics_to_timeseries(
        statistics: Dict[str, List[int]], time_step: float = 0.5
    ) -> Dict[str, Any]:
        """
        transform statistics dict to time-series format.

        args:
            statistics: statistics with keys like susceptible, infected, etc.
            time_step: time step in days

        returns:
            time-series data with dates
        """
        start_date = datetime.now(timezone.utc)
        timeseries = {}

        for state_key, counts in statistics.items():
            timeseries[state_key] = []
            for i, count in enumerate(counts):
                current_date = start_date + TimeDelta(days=i * time_step)
                timeseries[state_key].append(
                    {"date": current_date.isoformat(), "count": count, "day": i * time_step}
                )

        return timeseries

    @staticmethod
    def create_danger_zone_geojson(
        location_id: str,
        location_name: str,
        latitude: float,
        longitude: float,
        risk_score: float,
        agent_density: float,
        infected_percentage: float,
    ) -> Dict[str, Any]:
        """
        create danger zone GeoJSON feature for map visualization.

        args:
            location_id: location identifier
            location_name: location name
            latitude: center latitude
            longitude: center longitude
            risk_score: risk score (0-100)
            agent_density: agent density (agents per unit area)
            infected_percentage: percentage of agents infected

        returns:
            GeoJSON Feature for danger zone
        """
        # determine risk level and color
        if risk_score >= 75:
            level = "critical"
            color = "#F44336"
        elif risk_score >= 50:
            level = "high"
            color = "#FF9800"
        elif risk_score >= 25:
            level = "moderate"
            color = "#FFC107"
        else:
            level = "low"
            color = "#4CAF50"

        # radius based on density and risk
        radius_meters = max(500, min(5000, int(agent_density * 1000)))

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
            "properties": {
                "location_id": location_id,
                "location_name": location_name,
                "danger_level": level,
                "risk_score": risk_score,
                "agent_density": agent_density,
                "infected_percentage": infected_percentage,
                "color": color,
                "radius_meters": radius_meters,
            },
        }

        return feature

    @staticmethod
    def aggregate_agent_statistics(agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        aggregate agent-level statistics.

        args:
            agents: list of agent dictionaries

        returns:
            aggregated statistics
        """
        if not agents:
            return {
                "total_agents": 0,
                "by_state": {},
                "avg_days_in_state": 0,
                "isolated_count": 0,
                "isolation_rate": 0,
            }

        states = {}
        total_days_in_state = 0
        isolated_count = 0

        for agent in agents:
            state = agent.get("state", "S")
            states[state] = states.get(state, 0) + 1
            total_days_in_state += agent.get("days_in_state", 0)
            if agent.get("is_isolated", False):
                isolated_count += 1

        total_agents = len(agents)
        avg_days = total_days_in_state / total_agents if total_agents > 0 else 0

        return {
            "total_agents": total_agents,
            "by_state": states,
            "avg_days_in_state": avg_days,
            "isolated_count": isolated_count,
            "isolation_rate": (isolated_count / total_agents) if total_agents > 0 else 0,
        }

    @staticmethod
    def create_seird_pivot_table(
        statistics: Dict[str, List[int]], time_step: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        create pivot table format of SEIRD time-series.

        useful for CSV export and data analysis.

        args:
            statistics: statistics dictionary
            time_step: time step in days

        returns:
            list of dicts with day and all states
        """
        if not statistics:
            return []

        # get length from any state
        num_days = len(next(iter(statistics.values())))

        pivot_data = []
        for day in range(num_days):
            row = {"day": day * time_step}
            for state, counts in statistics.items():
                if day < len(counts):
                    row[state.lower()] = counts[day]
            pivot_data.append(row)

        return pivot_data

    @staticmethod
    def calculate_risk_score(
        infected_percentage: float,
        growth_rate: float,
        rt: float,
        doubling_time: Optional[float] = None,
    ) -> float:
        """
        calculate composite risk score for location.

        args:
            infected_percentage: percentage of population infected (0-100)
            growth_rate: recent growth rate
            rt: effective reproduction number
            doubling_time: doubling time in days (lower = more concerning)

        returns:
            risk score (0-100)
        """
        # normalize components to 0-1
        infected_score = min(infected_percentage / 100, 1.0)

        # growth rate score: exp(growth_rate) to emphasize exponential growth
        growth_score = min(np.exp(growth_rate) - 1, 1.0)

        # rt score: (Rt - 1) * 0.5 to emphasize values > 1
        rt_score = max(0, (rt - 1) * 0.5)

        # doubling time score: faster doubling = higher score
        if doubling_time and doubling_time > 0:
            doubling_score = max(0, 1 - (doubling_time / 14))  # 14 days = score 0
        else:
            doubling_score = 0

        # weighted combination
        score = (
            infected_score * 0.3
            + growth_score * 0.3
            + rt_score * 0.2
            + doubling_score * 0.2
        )

        return float(np.clip(score * 100, 0, 100))

    @staticmethod
    def export_simulation_to_json(
        simulation_output: Dict[str, Any], filepath: str
    ) -> None:
        """
        export simulation output to JSON file.

        args:
            simulation_output: complete simulation output dictionary
            filepath: path to save JSON file
        """
        with open(filepath, "w") as f:
            # handle datetime serialization
            json_str = json.dumps(
                simulation_output,
                default=str,  # convert non-serializable to string
                indent=2,
            )
            f.write(json_str)

    @staticmethod
    def export_seird_to_csv(
        statistics: Dict[str, List[int]], filepath: str, time_step: float = 0.5
    ) -> None:
        """
        export SEIRD statistics to CSV.

        args:
            statistics: statistics dictionary
            filepath: path to save CSV
            time_step: time step in days
        """
        import csv

        pivot_data = SimulationTransformer.create_seird_pivot_table(
            statistics, time_step
        )

        if not pivot_data:
            return

        fieldnames = pivot_data[0].keys()

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(pivot_data)

    @staticmethod
    def create_comparison_geojson(
        simulations: List[Dict[str, Any]], field: str = "risk_score"
    ) -> Dict[str, Any]:
        """
        create comparison GeoJSON for multiple locations.

        args:
            simulations: list of simulation outputs
            field: field to use for color coding

        returns:
            GeoJSON FeatureCollection for comparison
        """
        features = []

        for sim in simulations:
            # extract key fields
            location_id = sim.get("location_id")
            location_name = sim.get("location_name")
            metrics = sim.get("metrics", {})

            # calculate risk score if not present
            if field == "risk_score":
                risk_score = SimulationTransformer.calculate_risk_score(
                    infected_percentage=metrics.get("attack_rate", 0),
                    growth_rate=metrics.get("growth_rate", 0),
                    rt=metrics.get("rt", 1),
                    doubling_time=metrics.get("doubling_time"),
                )
            else:
                risk_score = metrics.get(field, 0)

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [120.9 + np.random.random() * 2, 14.5 + np.random.random() * 2],
                },
                "properties": {
                    "location_id": location_id,
                    "location_name": location_name,
                    "value": risk_score,
                    "metrics": metrics,
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
            "comparison_field": field,
        }


# Helper for simulating timedelta (in case datetime module is imported differently)
class TimeDelta:
    """simple timedelta class for date arithmetic."""

    def __init__(self, days: float = 0):
        self.total_seconds = days * 86400

    def __repr__(self):
        return f"TimeDelta(days={self.total_seconds / 86400})"
