"""Unit tests for weather.report — Report content and file output.

Covers:
- construction: needs at least one station, readable repr
- summary_text: one block per city, every statistic, n/a cases
- figures: named pages in order, one heatmap per city
- save: PDF, one PNG per figure, missing folders, bad suffix, write errors
"""

import datetime
from pathlib import Path

import pytest
from matplotlib.figure import Figure

from weather.exceptions import WeatherDataError
from weather.models import Measurement, WeatherStation
from weather.report import Report


def make_station(
    city: str, days: int, prcp: float | None = 0.0
) -> WeatherStation:
    """A station of *days* consecutive mild days from 2022-01-01."""
    start = datetime.date(2022, 1, 1)
    return WeatherStation(city, [
        Measurement(start + datetime.timedelta(days=i),
                    10.0 + i % 7, 5.0 + i % 7, 15.0 + i % 7, prcp)
        for i in range(days)
    ])


@pytest.fixture
def report() -> Report:
    return Report([make_station("Alpha", 3 * 365),
                   make_station("Beta", 40, prcp=None)])


class TestReportContent:

    def test_needs_a_station(self) -> None:
        with pytest.raises(WeatherDataError, match="at least one"):
            Report([])

    def test_repr(self, report: Report) -> None:
        assert repr(report) == "Report(cities=['Alpha', 'Beta'])"

    def test_summary_has_block_per_city(self, report: Report) -> None:
        text = report.summary_text()
        assert "Alpha\n=====" in text
        assert "Beta\n====" in text
        for label in ("Period", "Mean temperature", "Hottest day",
                      "Coldest day", "Wettest day", "Trend", "Anomaly days",
                      "Frost / hot / rainy", "Longest dry spell"):
            assert text.count(label) == 2

    def test_summary_values(self, report: Report) -> None:
        text = report.summary_text()
        assert "2022-01-01 to 2022-02-09 (40 days)" in text
        assert "Longest dry spell    1095 days" in text

    def test_summary_shows_na(self, report: Report) -> None:
        beta = report.summary_text().split("\n\n")[1]
        assert "n/a (needs 2+ years)" in beta    # 40 days: no trend
        assert "Wettest day          n/a" in beta  # no rain data

    def test_figures_are_named_pages(self, report: Report) -> None:
        figures = report.figures()
        assert list(figures) == ["summary", "temperature", "histogram",
                                 "heatmap_alpha", "heatmap_beta"]
        assert all(isinstance(f, Figure) for f in figures.values())


class TestReportSave:

    def test_pdf(self, report: Report, tmp_path: Path) -> None:
        path = tmp_path / "report.pdf"
        assert report.save(path) == [path]
        assert path.read_bytes().startswith(b"%PDF")

    def test_png_one_file_per_figure(
        self, report: Report, tmp_path: Path
    ) -> None:
        written = report.save(tmp_path / "report.png")
        assert [p.name for p in written] == [
            "report_summary.png", "report_temperature.png",
            "report_histogram.png", "report_heatmap_alpha.png",
            "report_heatmap_beta.png",
        ]
        assert all(p.read_bytes().startswith(b"\x89PNG") for p in written)

    def test_creates_missing_folders(
        self, report: Report, tmp_path: Path
    ) -> None:
        path = tmp_path / "a" / "b" / "report.pdf"
        report.save(path)
        assert path.is_file()

    def test_unsupported_suffix(self, report: Report, tmp_path: Path) -> None:
        with pytest.raises(WeatherDataError, match="Unsupported report"):
            report.save(tmp_path / "report.txt")
        assert list(tmp_path.iterdir()) == []

    def test_write_error(self, report: Report, tmp_path: Path) -> None:
        blocker = tmp_path / "file"
        blocker.write_text("not a folder")
        with pytest.raises(WeatherDataError, match="Cannot write"):
            report.save(blocker / "report.pdf")
