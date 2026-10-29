"""Matplotlib figures for the weather package.

Every function returns a ``matplotlib.figure.Figure`` built directly
(without ``pyplot``), so plotting needs no GUI backend and keeps no global
state.  The caller decides where each figure is saved.
"""

import calendar
import datetime

import numpy as np
from matplotlib.figure import Figure

from .analysis import monthly_averages
from .models import WeatherStation

HISTOGRAM_BINS = 40


def plot_monthly_temperature(stations: list[WeatherStation]) -> Figure:
    """Line chart of monthly mean ``tavg`` over time, one line per city."""
    fig = Figure(figsize=(10, 5), layout="constrained")
    ax = fig.subplots()
    for station in stations:
        monthly = monthly_averages(station)
        months = [datetime.date(year, month, 1) for year, month in monthly]
        ax.plot(months, list(monthly.values()), marker="o", markersize=3,
                label=station.city)
    ax.set(title="Monthly mean temperature", xlabel="Month",
           ylabel="Temperature (°C)")
    ax.grid(alpha=0.3)
    ax.legend()
    return fig


def plot_temperature_histogram(stations: list[WeatherStation]) -> Figure:
    """Overlaid histograms of daily ``tavg``, one outline per city.

    All cities share the same bins so their outlines line up.
    """
    temps = [np.array([m.tavg for m in station]) for station in stations]
    bins = np.histogram_bin_edges(np.concatenate(temps), bins=HISTOGRAM_BINS)

    fig = Figure(figsize=(10, 5), layout="constrained")
    ax = fig.subplots()
    for station, values in zip(stations, temps):
        ax.hist(values, bins=bins, histtype="step", linewidth=1.5,
                label=station.city)
    ax.set(title="Distribution of daily mean temperature",
           xlabel="Temperature (°C)", ylabel="Days")
    ax.legend()
    return fig


def plot_monthly_heatmap(station: WeatherStation) -> Figure:
    """Heatmap of monthly mean ``tavg``: one row per year, one column per
    month.  Months without data stay ``NaN`` and are drawn blank.
    """
    monthly = monthly_averages(station)
    years = sorted({year for year, _ in monthly})
    grid = np.full((len(years), 12), np.nan)
    for (year, month), value in monthly.items():
        grid[years.index(year), month - 1] = value

    fig = Figure(figsize=(10, 1.5 + 0.5 * len(years)), layout="constrained")
    ax = fig.subplots()
    image = ax.imshow(grid, cmap="coolwarm", aspect="auto")
    for (row, col), value in np.ndenumerate(grid):
        if not np.isnan(value):
            ax.text(col, row, f"{value:.0f}", ha="center", va="center",
                    fontsize=8)
    ax.set_xticks(range(12), calendar.month_abbr[1:])
    ax.set_yticks(range(len(years)), [str(year) for year in years])
    ax.set_title(f"{station.city}: monthly mean temperature (°C)")
    fig.colorbar(image, ax=ax, label="°C")
    return fig
