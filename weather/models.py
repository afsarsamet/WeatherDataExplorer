"""Domain models for the weather package.

``Measurement`` is an immutable dataclass representing a single day's
weather readings.  ``WeatherStation`` is a container that groups
measurements under a city name and exposes Pythonic iteration, length,
and date-filtering.
"""

from __future__ import annotations

import datetime
import math
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Measurement:
    """A single day's weather observation.

    Attributes
    ----------
    date : datetime.date
        The calendar date of the reading.
    tavg : float
        Average temperature in °C.
    tmin : float
        Minimum temperature in °C.
    tmax : float
        Maximum temperature in °C.
    prcp : float | None
        Precipitation in mm.  ``None`` when the value is missing.
    """

    date: datetime.date
    tavg: float
    tmin: float
    tmax: float
    prcp: float | None = None

    # -- validation -------------------------------------------------------

    def __post_init__(self) -> None:
        """Reject impossible readings so no invalid instance can exist."""
        values = (self.tavg, self.tmin, self.tmax, self.prcp)
        if not all(math.isfinite(v) for v in values if v is not None):
            raise ValueError(f"Non-finite value in {values}")
        if not self.tmin <= self.tavg <= self.tmax:
            raise ValueError(
                f"Temperature order violated: tmin={self.tmin}, "
                f"tavg={self.tavg}, tmax={self.tmax}"
            )
        if self.prcp is not None and self.prcp < 0:
            raise ValueError(f"Negative precipitation: {self.prcp}")

    # -- comparison dunder for natural chronological sorting ------------

    def __lt__(self, other: object) -> bool:
        """Support ``sorted()`` by comparing dates chronologically."""
        if not isinstance(other, Measurement):
            return NotImplemented
        return self.date < other.date

    # -- human-readable representation ----------------------------------

    def __repr__(self) -> str:
        prcp_str = f"{self.prcp:.1f}" if self.prcp is not None else "N/A"
        return (
            f"Measurement({self.date}, tavg={self.tavg}, "
            f"tmin={self.tmin}, tmax={self.tmax}, prcp={prcp_str})"
        )


class WeatherStation:
    """A named collection of daily ``Measurement`` objects for one city.

    Parameters
    ----------
    city : str
        Human-readable city label (e.g. ``"Budapest"``).
    measurements : list[Measurement]
        Daily readings, stored sorted by date ascending.
    """

    def __init__(self, city: str, measurements: list[Measurement]) -> None:
        self.city = city
        self.measurements = sorted(measurements)

    # -- dunder methods --------------------------------------------------

    def __len__(self) -> int:
        """Return the number of recorded days."""
        return len(self.measurements)

    def __iter__(self) -> Iterator[Measurement]:
        """Iterate over measurements in chronological order."""
        return iter(self.measurements)

    def __repr__(self) -> str:
        return f"WeatherStation(city={self.city!r}, records={len(self)})"

    # -- public helpers --------------------------------------------------

    def filter_dates(
        self,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ) -> WeatherStation:
        """Return a **new** ``WeatherStation`` whose measurements lie within
        the closed interval ``[start_date, end_date]``.

        Either bound may be ``None`` to leave that side open.
        """
        filtered = [
            m
            for m in self.measurements
            if (start_date is None or m.date >= start_date)
            and (end_date is None or m.date <= end_date)
        ]
        return WeatherStation(self.city, filtered)
