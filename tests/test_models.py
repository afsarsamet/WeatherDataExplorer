"""Unit tests for weather.models — Measurement and WeatherStation.

Covers:
- Dataclass construction and attribute access
- Optional precipitation (None default)
- __lt__ sorting by date
- __len__ and __iter__ on WeatherStation
- filter_dates with both, one, and no bounds
- __repr__ readability
"""

import datetime

import pytest

from weather.models import Measurement, WeatherStation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_measurements() -> list[Measurement]:
    """Five measurements spanning 2024-01-01 … 2024-01-05, out of order."""
    return [
        Measurement(datetime.date(2024, 1, 3), 2.0, -1.0, 5.0, 0.5),
        Measurement(datetime.date(2024, 1, 1), 0.0, -3.0, 4.0, None),
        Measurement(datetime.date(2024, 1, 5), 4.0, 1.0, 8.0, 1.2),
        Measurement(datetime.date(2024, 1, 2), 1.0, -2.0, 6.0, 0.0),
        Measurement(datetime.date(2024, 1, 4), 3.0, 0.0, 7.0),
    ]


@pytest.fixture
def station(sample_measurements: list[Measurement]) -> WeatherStation:
    return WeatherStation("TestCity", sample_measurements)


# ---------------------------------------------------------------------------
# Measurement tests
# ---------------------------------------------------------------------------

class TestMeasurement:
    """Verify Measurement dataclass behaviour."""

    def test_construction_with_all_fields(self) -> None:
        m = Measurement(datetime.date(2024, 6, 15), 22.0, 18.0, 28.0, 3.5)
        assert m.date == datetime.date(2024, 6, 15)
        assert m.tavg == 22.0
        assert m.tmin == 18.0
        assert m.tmax == 28.0
        assert m.prcp == 3.5

    def test_precipitation_defaults_to_none(self) -> None:
        m = Measurement(datetime.date(2024, 1, 1), 5.0, 0.0, 10.0)
        assert m.prcp is None

    def test_frozen_raises_on_assignment(self) -> None:
        m = Measurement(datetime.date(2024, 1, 1), 5.0, 0.0, 10.0)
        with pytest.raises(AttributeError):
            m.tavg = 99.0  # type: ignore[misc]

    def test_lt_compares_by_date(self) -> None:
        early = Measurement(datetime.date(2024, 1, 1), 0.0, -1.0, 1.0)
        later = Measurement(datetime.date(2024, 1, 2), 0.0, -1.0, 1.0)
        assert early < later
        assert not later < early

    def test_lt_returns_not_implemented_for_other_types(self) -> None:
        m = Measurement(datetime.date(2024, 1, 1), 0.0, -1.0, 1.0)
        assert m.__lt__("not a measurement") is NotImplemented

    def test_sorted_produces_chronological_order(
        self, sample_measurements: list[Measurement]
    ) -> None:
        ordered = sorted(sample_measurements)
        dates = [m.date for m in ordered]
        assert dates == [
            datetime.date(2024, 1, 1),
            datetime.date(2024, 1, 2),
            datetime.date(2024, 1, 3),
            datetime.date(2024, 1, 4),
            datetime.date(2024, 1, 5),
        ]

    def test_repr_with_prcp(self) -> None:
        m = Measurement(datetime.date(2024, 3, 1), 10.0, 5.0, 15.0, 2.3)
        r = repr(m)
        assert "tavg=10.0" in r
        assert "prcp=2.3" in r

    def test_repr_without_prcp(self) -> None:
        m = Measurement(datetime.date(2024, 3, 1), 10.0, 5.0, 15.0)
        assert "prcp=N/A" in repr(m)

    def test_equality(self) -> None:
        a = Measurement(datetime.date(2024, 1, 1), 5.0, 0.0, 10.0, 1.0)
        b = Measurement(datetime.date(2024, 1, 1), 5.0, 0.0, 10.0, 1.0)
        assert a == b

    def test_inequality(self) -> None:
        a = Measurement(datetime.date(2024, 1, 1), 5.0, 0.0, 10.0, 1.0)
        b = Measurement(datetime.date(2024, 1, 1), 5.0, 0.0, 10.0, 2.0)
        assert a != b


# ---------------------------------------------------------------------------
# WeatherStation tests
# ---------------------------------------------------------------------------

class TestWeatherStation:
    """Verify WeatherStation container behaviour."""

    def test_len(self, station: WeatherStation) -> None:
        assert len(station) == 5

    def test_iter_yields_measurements_in_order(
        self, station: WeatherStation
    ) -> None:
        dates = [m.date for m in station]
        assert dates == sorted(dates)

    def test_constructor_sorts_measurements(
        self, station: WeatherStation
    ) -> None:
        assert station.measurements[0].date == datetime.date(2024, 1, 1)
        assert station.measurements[-1].date == datetime.date(2024, 1, 5)

    def test_city_attribute(self, station: WeatherStation) -> None:
        assert station.city == "TestCity"

    def test_repr(self, station: WeatherStation) -> None:
        r = repr(station)
        assert "TestCity" in r
        assert "5" in r

    def test_filter_dates_both_bounds(self, station: WeatherStation) -> None:
        sub = station.filter_dates(
            datetime.date(2024, 1, 2), datetime.date(2024, 1, 4)
        )
        assert len(sub) == 3
        assert sub.measurements[0].date == datetime.date(2024, 1, 2)
        assert sub.measurements[-1].date == datetime.date(2024, 1, 4)

    def test_filter_dates_open_start(self, station: WeatherStation) -> None:
        sub = station.filter_dates(end_date=datetime.date(2024, 1, 3))
        assert len(sub) == 3

    def test_filter_dates_open_end(self, station: WeatherStation) -> None:
        sub = station.filter_dates(start_date=datetime.date(2024, 1, 4))
        assert len(sub) == 2

    def test_filter_dates_no_bounds(self, station: WeatherStation) -> None:
        sub = station.filter_dates()
        assert len(sub) == len(station)

    def test_filter_returns_new_station(self, station: WeatherStation) -> None:
        sub = station.filter_dates(
            datetime.date(2024, 1, 2), datetime.date(2024, 1, 4)
        )
        assert sub is not station
        assert sub.city == station.city

    def test_empty_station(self) -> None:
        s = WeatherStation("Empty", [])
        assert len(s) == 0
        assert list(s) == []
