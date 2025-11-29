"""
stats utilities for epidemic metrics calculations

provides statistical computations for epidemic modeling:
- Rt (effective reproduction number) calculation
- R0 (basic reproduction number) estimation
- doubling time calculations
- trend analysis
- epidemic curve analysis
"""

from typing import List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta


class EpidemicStats:
    """utility class for epidemic calculations."""

    # default parameters for calculations
    DEFAULT_RT_WINDOW = 7  # days
    MIN_CASES_FOR_STATS = 5
    GROWTH_RATE_WINDOW = 3  # days for recent trend

    @staticmethod
    def calculate_rt(
        infected_counts: List[int],
        infectious_period: float,
        time_step: float = 0.5,
        window_days: Optional[float] = None,
    ) -> float:
        """
        calculate effective reproduction number (Rt).

        measures how many people each infected person infects right now.
        Rt > 1 means outbreak is spreading.

        args:
            infected_counts: list of infected counts over time
            infectious_period: average infectious period in days
            time_step: time step of simulation in days
            window_days: number of days to use for calculation (default: 7)

        returns:
            effective reproduction number Rt
        """
        if window_days is None:
            window_days = EpidemicStats.DEFAULT_RT_WINDOW

        if len(infected_counts) < 2:
            return 0.0

        # use recent window of data
        window_steps = max(int(window_days / time_step), 2)
        recent_infected = np.array(
            infected_counts[-window_steps:] if len(infected_counts) >= window_steps else infected_counts
        )

        if len(recent_infected) < 2 or recent_infected[0] <= 0:
            return 0.0

        # calculate growth factor
        growth_factor = recent_infected[-1] / recent_infected[0]

        # Time span for calculation
        time_span = (len(recent_infected) - 1) * time_step

        # time span for calculation
        if time_span > 0 and growth_factor > 0:
            # calculate exponential growth rate: I(t) = I0 * exp(lambda * t)
            lambda_growth = np.log(growth_factor) / time_span
            # rt = 1 + lambda * infectious_period
            rt = 1 + lambda_growth * infectious_period
            return max(0.0, rt)

        return 1.0

    @staticmethod
    def estimate_r0(
        infected_counts: List[int],
        infectious_period: float,
        time_step: float = 0.5,
        population: int = 10000,
    ) -> float:
        """
        estimate basic reproduction number (R0).

        represents average number of secondary cases in susceptible population.
        uses early epidemic phase for estimation.

        args:
            infected_counts: list of infected counts over time
            infectious_period: average infectious period in days
            time_step: time step of simulation in days
            population: total population size

        returns:
            estimated R0 value
        """
        if len(infected_counts) < 2 or population == 0:
            return 0.0

        infected_array = np.array(infected_counts)

        # use early phase (first 10% or first 20 timesteps)
        early_phase_end = max(min(len(infected_array) // 10, int(20 / time_step)), 5)
        early_infected = infected_array[:early_phase_end]

        # find growth phase with sufficient data
        valid_indices = np.where(early_infected > EpidemicStats.MIN_CASES_FOR_STATS)[0]

        if len(valid_indices) < 2:
            return 1.0

        # calculate growth rate in early phase
        i_start = early_infected[valid_indices[0]]
        i_end = early_infected[valid_indices[-1]]
        time_diff = (valid_indices[-1] - valid_indices[0]) * time_step

        if time_diff > 0 and i_start > 0:
            lambda_growth = np.log(i_end / i_start) / time_diff
            # r0 ≈ 1 + lambda * infectious_period
            r0 = 1 + lambda_growth * infectious_period
            return max(0.5, min(r0, 10.0))  # bound between 0.5 and 10.0

        return 1.0

    @staticmethod
    def calculate_doubling_time(
        infected_counts: List[int], time_step: float = 0.5
    ) -> Optional[float]:
        """
        calculate doubling time of infections.

        time required for infected count to double during growth phase.

        args:
            infected_counts: list of infected counts over time
            time_step: time step of simulation in days

        returns:
            doubling time in days, or None if not calculable
        """
        if len(infected_counts) < 2:
            return None

        infected_array = np.array(infected_counts)

        # find a growth phase
        for i in range(1, len(infected_array)):
            if infected_array[i] > infected_array[i - 1] > EpidemicStats.MIN_CASES_FOR_STATS:
                # found growth phase
                baseline = infected_array[i]

                # find where it reaches 2x
                doubling_threshold = 2 * baseline
                future_indices = np.where(infected_array[i:] >= doubling_threshold)[0]

                if len(future_indices) > 0:
                    doubling_index = future_indices[0] + i
                    doubling_time = (doubling_index - i) * time_step
                    return doubling_time

        return None

    @staticmethod
    def calculate_attack_rate(
        susceptible_start: int,
        susceptible_end: int,
        deceased: int,
    ) -> float:
        """
        calculate attack rate.

        percentage of population that gets infected over course of outbreak.

        args:
            susceptible_start: initial susceptible count
            susceptible_end: final susceptible count
            deceased: total deaths

        returns:
            attack rate as percentage (0-100)
        """
        if susceptible_start == 0:
            return 0.0

        total_infected = susceptible_start - susceptible_end
        attack_rate = (total_infected / susceptible_start) * 100
        return min(100.0, max(0.0, attack_rate))

    @staticmethod
    def calculate_case_fatality_rate(
        total_infected: int, total_deceased: int
    ) -> float:
        """
        calculate case fatality rate (CFR).

        percentage of infected individuals who die.

        args:
            total_infected: total infected (recovered + deceased)
            total_deceased: total deaths

        returns:
            CFR as percentage (0-100)
        """
        if total_infected == 0:
            return 0.0

        cfr = (total_deceased / total_infected) * 100
        return min(100.0, max(0.0, cfr))

    @staticmethod
    def calculate_growth_rate(
        infected_counts: List[int],
        time_step: float = 0.5,
        window_days: Optional[float] = None,
    ) -> float:
        """
        calculate recent growth rate.

        proportional change in infections over recent period.

        args:
            infected_counts: list of infected counts over time
            time_step: time step of simulation in days
            window_days: number of days for recent window (default: 3)

        returns:
            growth rate (decimal, 0.1 = 10% growth)
        """
        if window_days is None:
            window_days = EpidemicStats.GROWTH_RATE_WINDOW

        if len(infected_counts) < 2:
            return 0.0

        window_steps = max(int(window_days / time_step), 2)
        recent = np.array(
            infected_counts[-window_steps:] if len(infected_counts) >= window_steps else infected_counts
        )

        if len(recent) < 2:
            return 0.0

        if recent[0] == 0:
            # handle zero start case
            if recent[-1] > 0:
                return 1.0  # represents infinite growth from 0
            return 0.0

        growth_rate = (recent[-1] - recent[0]) / recent[0]
        return float(growth_rate)

    @staticmethod
    def calculate_peak_metrics(infected_counts: List[int], time_step: float = 0.5) -> Tuple[int, int]:
        """
        calculate peak infection metrics.

        args:
            infected_counts: list of infected counts over time
            time_step: time step of simulation in days

        returns:
            tuple of (peak_count, peak_day)
        """
        if len(infected_counts) == 0:
            return 0, 0

        infected_array = np.array(infected_counts)
        peak_count = int(np.max(infected_array))
        peak_index = int(np.argmax(infected_array))
        peak_day = int(peak_index * time_step)

        return peak_count, peak_day

    @staticmethod
    def calculate_epidemic_duration(
        infected_counts: List[int], time_step: float = 0.5, min_threshold: int = 1
    ) -> int:
        """
        calculate total duration of active transmission.

        duration where infected count exceeds threshold.

        args:
            infected_counts: list of infected counts over time
            time_step: time step of simulation in days
            min_threshold: minimum infected count to consider as active

        returns:
            duration in days
        """
        if len(infected_counts) == 0:
            return 0

        infected_array = np.array(infected_counts)
        active_periods = np.sum(infected_array >= min_threshold)
        duration = int(active_periods * time_step)

        return duration

    @staticmethod
    def calculate_trend(metrics_series: List[float], threshold: float = 0.1) -> str:
        """
        determine trend direction from series of metrics.

        args:
            metrics_series: list of metric values over time (e.g., Rt values)
            threshold: threshold for determining stable region

        returns:
            trend string: increasing, decreasing, or stable
        """
        if len(metrics_series) < 2:
            return "stable"

        # use recent values (last 3-5 points)
        recent = metrics_series[-min(5, len(metrics_series)) :]
        avg_recent = np.mean(recent)

        # compare to slightly older values
        if len(metrics_series) >= 10:
            prev = metrics_series[-10:-5]
            avg_prev = np.mean(prev)
        else:
            avg_prev = recent[0]

        change = avg_recent - avg_prev

        if change > threshold:
            return "increasing"
        elif change < -threshold:
            return "decreasing"
        else:
            return "stable"

    @staticmethod
    def smooth_series(data: List[float], window: int = 3) -> List[float]:
        """
        apply moving average smoothing to data series.

        args:
            data: original data series
            window: window size for moving average

        returns:
            smoothed data series
        """
        if len(data) == 0:
            return []

        if window > len(data):
            window = len(data)

        data_array = np.array(data, dtype=float)
        smoothed = np.convolve(data_array, np.ones(window) / window, mode="valid")

        # pad the beginning to maintain length
        pad_size = len(data) - len(smoothed)
        if pad_size > 0:
            smoothed = np.concatenate([data_array[:pad_size], smoothed])

        return smoothed.tolist()

    @staticmethod
    def estimate_secondary_cases(
        infected_counts: List[int],
        infectious_period: float,
        contact_rate: float = 5.0,
    ) -> List[float]:
        """
        estimate secondary cases distribution.

        args:
            infected_counts: list of infected counts
            infectious_period: average infectious period
            contact_rate: average contacts per day

        returns:
            list of estimated secondary cases per timestep
        """
        if len(infected_counts) == 0:
            return []

        infected_array = np.array(infected_counts, dtype=float)

        # estimate contacts during infectious period
        total_contacts = contact_rate * infectious_period

        # secondary cases = current infected * transmission probability
        # simplified model: secondary ~ current_infected * contacts
        secondary_cases = infected_array * total_contacts / max(
            np.max(infected_array), 1
        )

        return secondary_cases.tolist()