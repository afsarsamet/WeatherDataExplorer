"""Statistics for a single ``WeatherStation``.

Every function is pure: it takes a station and returns plain data, so each
one can be tested with a few hand-made measurements.  Scalar summaries use
the ``statistics`` module, seasonal and trend work uses NumPy, and grouping
and counting use ``collections`` and ``itertools``.

All functions expect a non-empty station; the loaders and the CLI make sure
of that.
"""

from collections import Counter, defaultdict
from itertools import groupby
from statistics import mean, median, stdev

import numpy as np

from .models import Measurement, WeatherStation

FROST_TMIN = 0.0    # frost day: tmin below this (°C)
HOT_TMAX = 30.0     # hot day: tmax at or above this (°C)
RAINY_PRCP = 1.0    # rainy day: prcp at or above this (mm)
MIN_TREND_YEARS = 2  # shortest span temperature_trend will fit


def summary(station: WeatherStation) -> dict[str, float]:
    """Mean, median and sample standard deviation of daily ``tavg``.

    ``stdev`` is 0.0 for a single-day station.
    """
    temps = [m.tavg for m in station]
    return {
        "mean": mean(temps),
        "median": median(temps),
        "stdev": stdev(temps) if len(temps) > 1 else 0.0,
    }


def extremes(station: WeatherStation) -> dict[str, Measurement | None]:
    """The hottest (max ``tmax``), coldest (min ``tmin``) and wettest
    (max ``prcp``) days.  ``wettest`` is ``None`` if no day has ``prcp``.
    """
    with_rain = [m for m in station if m.prcp is not None]
    return {
        "hottest": max(station, key=lambda m: m.tmax),
        "coldest": min(station, key=lambda m: m.tmin),
        "wettest": max(with_rain, key=lambda m: m.prcp, default=None),
    }


def monthly_averages(station: WeatherStation) -> dict[tuple[int, int], float]:
    """Mean ``tavg`` per ``(year, month)``, in chronological order."""
    groups: defaultdict[tuple[int, int], list[float]] = defaultdict(list)
    for m in station:
        groups[(m.date.year, m.date.month)].append(m.tavg)
    return {key: mean(temps) for key, temps in sorted(groups.items())}


def _month_stats(
    station: WeatherStation,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(tavg, month_mean, month_std)`` as arrays, one entry per day.

    ``month_mean[i]`` and ``month_std[i]`` are the mean and population
    standard deviation of ``tavg`` over every day, in any year, that shares
    day ``i``'s calendar month.  This is the seasonal baseline used by
    ``anomaly_days`` and ``temperature_trend``.
    """
    tavg = np.array([m.tavg for m in station])
    months = np.array([m.date.month for m in station])
    month_mean = np.zeros_like(tavg)
    month_std = np.zeros_like(tavg)
    for month in np.unique(months):
        in_month = months == month
        month_mean[in_month] = tavg[in_month].mean()
        month_std[in_month] = tavg[in_month].std()
    return tavg, month_mean, month_std


def anomaly_days(
    station: WeatherStation, threshold: float = 2.0
) -> list[Measurement]:
    """Days whose ``tavg`` is more than *threshold* standard deviations
    from the mean of their own calendar month (across all years).

    Comparing against the month rather than the whole year means a normal
    January day is not flagged just for being cold.
    """
    tavg, month_mean, month_std = _month_stats(station)
    is_anomaly = np.abs(tavg - month_mean) > threshold * month_std
    return [m for m, flagged in zip(station, is_anomaly) if flagged]


def temperature_trend(station: WeatherStation) -> float | None:
    """Linear warming (+) or cooling (−) trend of ``tavg`` in °C per year.

    Each day's calendar-month mean is subtracted first to remove the
    seasons, then a straight line is fitted (``np.polyfit``) against days
    since the first record.  Removing the seasons keeps a partial year at
    either end from skewing the slope.

    Returns ``None`` when the records span less than ``MIN_TREND_YEARS``:
    a trend needs several years to compare, and a slope fitted inside one
    season would be a meaningless °C-per-year figure.
    """
    first = station.measurements[0].date
    span_days = (station.measurements[-1].date - first).days
    if span_days < MIN_TREND_YEARS * 365:
        return None
    tavg, month_mean, _ = _month_stats(station)
    days = np.array([(m.date - first).days for m in station])
    slope_per_day = np.polyfit(days, tavg - month_mean, 1)[0]
    return float(slope_per_day * 365.25)


def day_counts(station: WeatherStation) -> Counter[str]:
    """Count ``"frost"``, ``"hot"`` and ``"rainy"`` days.

    Frost: ``tmin < 0``.  Hot: ``tmax >= 30``.  Rainy: ``prcp >= 1.0`` mm.
    A day can fall into several categories; a missing category counts 0.
    """
    return Counter(
        label
        for m in station
        for label, matches in (
            ("frost", m.tmin < FROST_TMIN),
            ("hot", m.tmax >= HOT_TMAX),
            ("rainy", m.prcp is not None and m.prcp >= RAINY_PRCP),
        )
        if matches
    )


def longest_dry_spell(station: WeatherStation) -> int:
    """Length of the longest run of consecutive records with ``prcp == 0``.

    A missing ``prcp`` (``None``) is unknown, not dry, so it ends a run.
    """
    runs = (
        sum(1 for _ in run)
        for is_dry, run in groupby(station, key=lambda m: m.prcp == 0)
        if is_dry
    )
    return max(runs, default=0)
