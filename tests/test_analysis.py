"""Unit tests for weather.analysis — every statistic on hand-made data.

Covers:
- summary: mean / median / stdev, single-day stdev
- extremes: hottest, coldest, wettest (ignoring and lacking prcp)
- monthly_averages: grouping by (year, month), chronological order
- anomaly_days: constant series, one outlier, per-month baseline, threshold
- temperature_trend: constant, warming, cooling, seasonal-only, too short
- day_counts: each category, overlaps, boundaries
- longest_dry_spell: runs, broken by rain or None, no dry days
"""

import datetime
from collections import Counter

import pytest

from weather import analysis
from weather.models import Measurement, WeatherStation

START = datetime.date(2024, 1, 1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def day(
    date: datetime.date,
    tavg: float,
    prcp: float | None = None,
    tmin: float | None = None,
    tmax: float | None = None,
) -> Measurement:
    """A measurement with tmin/tmax defaulting to tavg ∓ 5."""
    return Measurement(
        date,
        tavg,
        tavg - 5 if tmin is None else tmin,
        tavg + 5 if tmax is None else tmax,
        prcp,
    )


def daily(
    temps: list[float], start: datetime.date = START
) -> WeatherStation:
    """A station with one measurement per consecutive day from *start*."""
    return WeatherStation("Test", [
        day(start + datetime.timedelta(days=i), t)
        for i, t in enumerate(temps)
    ])


def rain_station(rain: list[float | None]) -> WeatherStation:
    """A 10 °C station with the given daily precipitation."""
    return WeatherStation("Test", [
        day(START + datetime.timedelta(days=i), 10.0, prcp=p)
        for i, p in enumerate(rain)
    ])


# ---------------------------------------------------------------------------
# summary / extremes / monthly_averages
# ---------------------------------------------------------------------------

class TestSummary:

    def test_known_values(self) -> None:
        result = analysis.summary(daily([1.0, 2.0, 3.0, 4.0]))
        assert result["mean"] == 2.5
        assert result["median"] == 2.5
        assert result["stdev"] == pytest.approx(1.2909944)

    def test_single_day_has_zero_stdev(self) -> None:
        assert analysis.summary(daily([7.0]))["stdev"] == 0.0


class TestExtremes:

    def test_hottest_coldest_wettest(self) -> None:
        hot = day(START, 20.0, prcp=0.0, tmax=35.0)
        cold = day(START + datetime.timedelta(days=1), 0.0, tmin=-12.0)
        wet = day(START + datetime.timedelta(days=2), 10.0, prcp=40.0)
        result = analysis.extremes(WeatherStation("Test", [hot, cold, wet]))
        assert result == {"hottest": hot, "coldest": cold, "wettest": wet}

    def test_wettest_is_none_without_rain_data(self) -> None:
        assert analysis.extremes(daily([1.0, 2.0]))["wettest"] is None


class TestMonthlyAverages:

    def test_two_months(self) -> None:
        station = daily([1.0] * 31 + [4.0, 6.0])   # Jan: 1.0, Feb: 4.0, 6.0
        assert analysis.monthly_averages(station) == {
            (2024, 1): 1.0,
            (2024, 2): 5.0,
        }

    def test_same_month_in_different_years_kept_apart(self) -> None:
        station = WeatherStation("Test", [
            day(datetime.date(2025, 3, 1), 8.0),
            day(datetime.date(2024, 3, 1), 2.0),
        ])
        result = analysis.monthly_averages(station)
        assert list(result) == [(2024, 3), (2025, 3)]
        assert list(result.values()) == [2.0, 8.0]


# ---------------------------------------------------------------------------
# anomaly_days / temperature_trend
# ---------------------------------------------------------------------------

class TestAnomalyDays:

    def test_constant_series_has_none(self) -> None:
        assert analysis.anomaly_days(daily([10.0] * 31)) == []

    def test_single_outlier_flagged(self) -> None:
        station = daily([10.0] * 15 + [30.0] + [10.0] * 15)
        flagged = analysis.anomaly_days(station)
        assert [m.date for m in flagged] == [datetime.date(2024, 1, 16)]

    def test_baseline_is_per_calendar_month(self) -> None:
        # A cold January and a warm July: no day is unusual for its month.
        station = WeatherStation("Test", [
            *(day(datetime.date(2024, 1, d), -5.0) for d in range(1, 11)),
            *(day(datetime.date(2024, 7, d), 25.0) for d in range(1, 11)),
        ])
        assert analysis.anomaly_days(station) == []

    def test_higher_threshold_flags_fewer(self) -> None:
        station = daily([10.0] * 15 + [30.0] + [10.0] * 15)
        assert analysis.anomaly_days(station, threshold=10.0) == []


class TestTemperatureTrend:

    def test_constant_series_is_flat(self) -> None:
        trend = analysis.temperature_trend(daily([10.0] * 3 * 365))
        assert trend == pytest.approx(0.0, abs=1e-9)

    def test_warming_is_positive_and_close_to_rate(self) -> None:
        # Every day of year n is n °C warmer than year 0: +1 °C per year.
        station = WeatherStation("Test", [
            day(datetime.date(2020 + n, 1, 1) + datetime.timedelta(days=i),
                10.0 + n)
            for n in range(6)
            for i in range(365)
        ])
        trend = analysis.temperature_trend(station)
        assert trend == pytest.approx(1.0, rel=0.1)

    def test_cooling_is_negative(self) -> None:
        temps = [20.0 - i / 365 for i in range(3 * 365)]
        assert analysis.temperature_trend(daily(temps)) < 0

    def test_seasons_alone_give_no_trend(self) -> None:
        # 2.5 years where each month has its own fixed temperature: the
        # extra warm half-year at the end must not look like warming.
        station = WeatherStation("Test", [
            day(datetime.date(2023 + (i // 12), i % 12 + 1, 1), 2.0 * (i % 12))
            for i in range(30)
        ])
        trend = analysis.temperature_trend(station)
        assert trend == pytest.approx(0.0, abs=1e-9)

    @pytest.mark.parametrize("days", [1, 31, 2 * 365 - 1])
    def test_under_two_years_is_none(self, days: int) -> None:
        # e.g. one July warming up 0.1 °C a day is not a yearly trend
        temps = [20.0 + i / 10 for i in range(days)]
        assert analysis.temperature_trend(daily(temps)) is None


# ---------------------------------------------------------------------------
# day_counts / longest_dry_spell
# ---------------------------------------------------------------------------

class TestDayCounts:

    def test_categories_and_overlap(self) -> None:
        station = WeatherStation("Test", [
            day(START, 0.0, tmin=-1.0),                     # frost
            day(datetime.date(2024, 7, 1), 25.0, tmax=31.0),  # hot
            day(datetime.date(2024, 3, 1), 5.0, prcp=2.0),    # rainy
            day(datetime.date(2024, 2, 1), 0.0, tmin=-3.0,
                prcp=5.0),                                  # frost + rainy
            day(datetime.date(2024, 5, 1), 15.0, prcp=None),  # nothing
        ])
        assert analysis.day_counts(station) == Counter(
            {"frost": 2, "hot": 1, "rainy": 2}
        )

    def test_boundaries(self) -> None:
        station = WeatherStation("Test", [
            day(START, 5.0, tmin=0.0),                      # not frost
            day(datetime.date(2024, 7, 1), 25.0, tmax=30.0),  # hot
            day(datetime.date(2024, 3, 1), 5.0, prcp=1.0),    # rainy
            day(datetime.date(2024, 3, 2), 5.0, prcp=0.9),    # not rainy
        ])
        counts = analysis.day_counts(station)
        assert counts["frost"] == 0
        assert counts["hot"] == 1
        assert counts["rainy"] == 1


class TestLongestDrySpell:

    def test_longest_run(self) -> None:
        station = rain_station([0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        assert analysis.longest_dry_spell(station) == 3

    def test_missing_value_breaks_run(self) -> None:
        station = rain_station([0.0, 0.0, None, 0.0, 0.0])
        assert analysis.longest_dry_spell(station) == 2

    def test_no_dry_days(self) -> None:
        assert analysis.longest_dry_spell(rain_station([2.0, None])) == 0
