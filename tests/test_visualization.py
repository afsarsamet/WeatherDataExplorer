"""Unit tests for weather.visualization — figure structure, not pixels.

Covers:
- plot_monthly_temperature: one labelled line per city, one point per month
- plot_temperature_histogram: one outline per city on shared bins
- plot_monthly_heatmap: years × 12 grid, NaN for months without data
- every plot handles a single-day station
"""

import datetime

import numpy as np
import pytest
from matplotlib.figure import Figure

from weather.analysis import monthly_averages
from weather.models import Measurement, WeatherStation
from weather.visualization import (
    plot_monthly_heatmap,
    plot_monthly_temperature,
    plot_temperature_histogram,
)


def make_station(city: str, start: datetime.date, days: int) -> WeatherStation:
    """A station with a smooth seasonal cycle, one record per day."""
    measurements = []
    for i in range(days):
        tavg = 10 + 10 * np.sin(2 * np.pi * i / 365)
        measurements.append(Measurement(
            start + datetime.timedelta(days=i), tavg, tavg - 4, tavg + 4, 0.0,
        ))
    return WeatherStation(city, measurements)


@pytest.fixture
def stations() -> list[WeatherStation]:
    # Alpha: 2023-11-01 .. 2024-02-28 (4 months over two years)
    # Beta:  2024-01-01 .. 2024-01-31 (1 month)
    return [
        make_station("Alpha", datetime.date(2023, 11, 1), 120),
        make_station("Beta", datetime.date(2024, 1, 1), 31),
    ]


class TestMonthlyTemperature:

    def test_one_line_per_city(self, stations: list[WeatherStation]) -> None:
        fig = plot_monthly_temperature(stations)
        lines = fig.axes[0].get_lines()
        assert isinstance(fig, Figure)
        assert [line.get_label() for line in lines] == ["Alpha", "Beta"]

    def test_one_point_per_month(
        self, stations: list[WeatherStation]
    ) -> None:
        lines = plot_monthly_temperature(stations).axes[0].get_lines()
        assert len(lines[0].get_ydata()) == 4
        assert list(lines[0].get_ydata()) == pytest.approx(
            list(monthly_averages(stations[0]).values())
        )


class TestTemperatureHistogram:

    def test_one_outline_per_city(
        self, stations: list[WeatherStation]
    ) -> None:
        ax = plot_temperature_histogram(stations).axes[0]
        assert len(ax.patches) == 2
        labels = [t.get_text() for t in ax.get_legend().get_texts()]
        assert labels == ["Alpha", "Beta"]


class TestMonthlyHeatmap:

    def test_grid_has_years_by_months(
        self, stations: list[WeatherStation]
    ) -> None:
        fig = plot_monthly_heatmap(stations[0])
        grid = fig.axes[0].get_images()[0].get_array()
        assert grid.shape == (2, 12)                     # 2023 and 2024
        ticks = [t.get_text() for t in fig.axes[0].get_yticklabels()]
        assert ticks == ["2023", "2024"]

    def test_missing_months_are_nan(
        self, stations: list[WeatherStation]
    ) -> None:
        grid = plot_monthly_heatmap(stations[0]).axes[0].get_images()[0]
        values = np.ma.filled(grid.get_array(), np.nan)
        assert np.isnan(values[0, 0])                    # Jan 2023: no data
        assert values[0, 10] == pytest.approx(           # Nov 2023
            monthly_averages(stations[0])[(2023, 11)]
        )
        assert np.count_nonzero(~np.isnan(values)) == 4

    def test_title_names_city(self, stations: list[WeatherStation]) -> None:
        fig = plot_monthly_heatmap(stations[1])
        assert "Beta" in fig.axes[0].get_title()


@pytest.mark.parametrize("plot", [
    lambda s: plot_monthly_temperature([s]),
    lambda s: plot_temperature_histogram([s]),
    plot_monthly_heatmap,
])
def test_single_day_station(plot) -> None:
    station = make_station("One", datetime.date(2024, 5, 1), 1)
    assert isinstance(plot(station), Figure)
