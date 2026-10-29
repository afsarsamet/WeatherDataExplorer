"""Report assembly: per-city statistics plus figures, saved as PDF or PNG.

``Report`` is the only place that combines ``analysis`` and
``visualization``.  The summary is itself a figure (monospace text), so a
PDF and a set of PNGs are written from the same list of figures.
"""

import logging
from collections import Counter
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from . import analysis
from .exceptions import WeatherDataError
from .models import WeatherStation
from .visualization import (
    plot_monthly_heatmap,
    plot_monthly_temperature,
    plot_temperature_histogram,
)

logger = logging.getLogger(__name__)

FORMATS = (".pdf", ".png")
CITIES_PER_PAGE = 5  # city summaries that fit on one A4 summary page


class Report:
    """Statistics and plots for one or more stations.

    Parameters
    ----------
    stations : list[WeatherStation]
        Non-empty stations, one per city, already cut to the wanted period.

    Raises
    ------
    WeatherDataError
        If *stations* is empty or names the same city twice.
    """

    def __init__(self, stations: list[WeatherStation]) -> None:
        if not stations:
            raise WeatherDataError("A report needs at least one station")
        counts = Counter(station.city for station in stations)
        repeated = [city for city, n in counts.items() if n > 1]
        if repeated:
            raise WeatherDataError(
                f"City given more than once: {', '.join(repeated)}"
            )
        self.stations = stations

    def __repr__(self) -> str:
        cities = [station.city for station in self.stations]
        return f"Report(cities={cities})"

    # -- content -----------------------------------------------------------

    def summary_text(self) -> str:
        """Plain-text statistics, one block per city."""
        return _summaries(self.stations)

    def figures(self) -> dict[str, Figure]:
        """All report pages by name: summary page(s), line chart, histogram,
        then one heatmap per city (``heatmap_<city>``).

        Summaries take one page per ``CITIES_PER_PAGE`` cities:
        ``summary``, then ``summary_2``, ``summary_3``, ...
        """
        groups = [
            self.stations[i:i + CITIES_PER_PAGE]
            for i in range(0, len(self.stations), CITIES_PER_PAGE)
        ]
        summaries = {
            "summary" if n == 1 else f"summary_{n}": _summary_page(group)
            for n, group in enumerate(groups, start=1)
        }
        heatmaps = {
            f"heatmap_{station.city.lower()}": plot_monthly_heatmap(station)
            for station in self.stations
        }
        return {
            **summaries,
            "temperature": plot_monthly_temperature(self.stations),
            "histogram": plot_temperature_histogram(self.stations),
            **heatmaps,
        }

    # -- output ------------------------------------------------------------

    def save(self, path: str | Path) -> list[Path]:
        """Write the report and return the files written.

        ``.pdf`` writes one multi-page PDF.  ``.png`` writes one PNG per
        figure, named ``<stem>_<figure name>.png`` next to *path*.  Missing
        parent folders are created.

        Raises
        ------
        WeatherDataError
            If the suffix is not ``.pdf``/``.png`` or the file can't be
            written.
        """
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix not in FORMATS:
            raise WeatherDataError(
                f"Unsupported report format {path.suffix or path.name!r}: "
                f"use {' or '.join(FORMATS)}"
            )

        figures = self.figures()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if suffix == ".pdf":
                with PdfPages(path) as pdf:
                    for fig in figures.values():
                        pdf.savefig(fig)
                written = [path]
            else:
                written = []
                for name, fig in figures.items():
                    png_path = path.with_name(f"{path.stem}_{name}.png")
                    fig.savefig(png_path, dpi=150)
                    written.append(png_path)
        except OSError as exc:
            raise WeatherDataError(f"Cannot write report: {exc}") from exc

        logger.info("Wrote %s", ", ".join(str(p) for p in written))
        return written


def _summary_page(stations: list[WeatherStation]) -> Figure:
    """An A4 page holding the title and the stations' summaries."""
    fig = Figure(figsize=(8.27, 11.69))
    fig.text(0.07, 0.95, "Weather Data Explorer report",
             fontsize=16, weight="bold", va="top")
    fig.text(0.07, 0.91, _summaries(stations),
             family="monospace", fontsize=9, va="top")
    return fig


def _summaries(stations: list[WeatherStation]) -> str:
    """The summary blocks of *stations*, separated by blank lines."""
    return "\n\n".join(_city_summary(station) for station in stations)


def _city_summary(station: WeatherStation) -> str:
    """Aligned ``label  value`` lines with every statistic for one city."""
    stats = analysis.summary(station)
    ext = analysis.extremes(station)
    trend = analysis.temperature_trend(station)
    counts = analysis.day_counts(station)
    hottest, coldest, wettest = ext["hottest"], ext["coldest"], ext["wettest"]
    first, last = station.measurements[0].date, station.measurements[-1].date

    rows = [
        ("Period", f"{first} to {last} ({len(station)} days)"),
        ("Mean temperature", f"{stats['mean']:.1f} °C"),
        ("Median / stdev",
         f"{stats['median']:.1f} / {stats['stdev']:.1f} °C"),
        ("Hottest day", f"{hottest.tmax:.1f} °C on {hottest.date}"),
        ("Coldest day", f"{coldest.tmin:.1f} °C on {coldest.date}"),
        ("Wettest day", "n/a" if wettest is None
         else f"{wettest.prcp:.1f} mm on {wettest.date}"),
        ("Trend", "n/a (needs 2+ years)" if trend is None
         else f"{trend:+.2f} °C/year"),
        ("Anomaly days", str(len(analysis.anomaly_days(station)))),
        ("Frost / hot / rainy",
         f"{counts['frost']} / {counts['hot']} / {counts['rainy']} days"),
        ("Longest dry spell",
         f"{analysis.longest_dry_spell(station)} days"),
    ]
    width = max(len(label) for label, _ in rows) + 2
    lines = [f"  {label:<{width}}{value}" for label, value in rows]
    return "\n".join([station.city, "=" * len(station.city), *lines])
