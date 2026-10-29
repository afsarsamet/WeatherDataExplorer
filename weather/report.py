"""Report assembly: per-city statistics plus figures, saved as PDF or PNG.

``Report`` is the only place that combines ``analysis`` and
``visualization``.  The summary is itself a figure (monospace text), so a
PDF and a set of PNGs are written from the same list of figures.
"""

import logging
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


class Report:
    """Statistics and plots for one or more stations.

    Parameters
    ----------
    stations : list[WeatherStation]
        Non-empty stations, one per city, already cut to the wanted period.
    """

    def __init__(self, stations: list[WeatherStation]) -> None:
        if not stations:
            raise WeatherDataError("A report needs at least one station")
        self.stations = stations

    def __repr__(self) -> str:
        cities = [station.city for station in self.stations]
        return f"Report(cities={cities})"

    # -- content -----------------------------------------------------------

    def summary_text(self) -> str:
        """Plain-text statistics, one block per city."""
        return "\n\n".join(_city_summary(s) for s in self.stations)

    def figures(self) -> dict[str, Figure]:
        """All report pages by name: summary, line chart, histogram, then
        one heatmap per city (``heatmap_<city>``)."""
        heatmaps = {
            f"heatmap_{station.city.lower()}": plot_monthly_heatmap(station)
            for station in self.stations
        }
        return {
            "summary": self._summary_page(),
            "temperature": plot_monthly_temperature(self.stations),
            "histogram": plot_temperature_histogram(self.stations),
            **heatmaps,
        }

    def _summary_page(self) -> Figure:
        """An A4 page holding the title and ``summary_text`` in monospace."""
        fig = Figure(figsize=(8.27, 11.69))
        fig.text(0.07, 0.95, "Weather Data Explorer report",
                 fontsize=16, weight="bold", va="top")
        fig.text(0.07, 0.91, self.summary_text(),
                 family="monospace", fontsize=9, va="top")
        return fig

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
