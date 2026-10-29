"""Quick-start analysis helpers (Phase 1 placeholder).

A lightweight ``WeatherAnalyzer`` that wraps a ``WeatherStation`` and
exposes scalar summaries.  This module will be significantly expanded in
Phase 3 with NumPy vectorised computations, ``collections`` aggregations,
and ``itertools`` streak detection.
"""

from statistics import mean

from .models import Measurement, WeatherStation


class WeatherAnalyzer:
    """Compute basic scalar statistics for a single ``WeatherStation``."""

    def __init__(self, station: WeatherStation) -> None:
        self.station = station

    def average_temperature(self) -> float:
        """Mean of daily ``tavg`` values across all measurements."""
        return mean(m.tavg for m in self.station)

    def hottest_day(self) -> Measurement:
        """Return the ``Measurement`` with the highest ``tmax``."""
        return max(self.station, key=lambda m: m.tmax)

    def coldest_day(self) -> Measurement:
        """Return the ``Measurement`` with the lowest ``tmin``."""
        return min(self.station, key=lambda m: m.tmin)
