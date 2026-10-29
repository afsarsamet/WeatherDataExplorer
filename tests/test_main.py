"""End-to-end tests for the command-line interface in main.py.

Covers:
- PDF and PNG reports from CSV and JSON files, summary on stdout
- --start / --end period selection and the default output path
- data and output errors: one ERROR line, exit code 1
- argument errors: argparse usage message, exit code 2
- -v shows the package's debug messages
"""

import datetime
import json
import logging
from pathlib import Path

import pytest

from main import main


@pytest.fixture(autouse=True)
def reset_weather_logger():
    """``-v`` changes the ``weather`` logger level; undo it after each test."""
    yield
    logging.getLogger("weather").setLevel(logging.NOTSET)


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    """Alpha: January 2024 as CSV."""
    rows = [f"2024-01-{d:02d},{d},{d - 3},{d + 3},0.0" for d in range(1, 32)]
    path = tmp_path / "alpha.csv"
    path.write_text("date,tavg,tmin,tmax,prcp\n" + "\n".join(rows) + "\n")
    return path


@pytest.fixture
def json_file(tmp_path: Path) -> Path:
    """Beta: January 2024 as JSON."""
    start = datetime.date(2024, 1, 1)
    records = [
        {"date": str(start + datetime.timedelta(days=i)),
         "tavg": 5.0, "tmin": 1.0, "tmax": 9.0, "prcp": None}
        for i in range(31)
    ]
    path = tmp_path / "beta.json"
    path.write_text(json.dumps(records))
    return path


# ---------------------------------------------------------------------------
# Successful runs
# ---------------------------------------------------------------------------

class TestReports:

    def test_pdf_for_two_cities(
        self, csv_file: Path, json_file: Path, tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        out = tmp_path / "report.pdf"
        assert main([str(csv_file), str(json_file), "-o", str(out)]) == 0
        assert out.read_bytes().startswith(b"%PDF")
        printed = capsys.readouterr().out
        assert "Alpha\n=====" in printed
        assert "Beta\n====" in printed

    def test_png_one_file_per_figure(
        self, csv_file: Path, tmp_path: Path
    ) -> None:
        assert main([str(csv_file), "-o", str(tmp_path / "r.png")]) == 0
        assert sorted(p.name for p in tmp_path.glob("r_*.png")) == [
            "r_heatmap_alpha.png", "r_histogram.png",
            "r_summary.png", "r_temperature.png",
        ]

    def test_period_selection(
        self, csv_file: Path, tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        code = main([str(csv_file), "--start", "2024-01-05",
                     "--end", "2024-01-10", "-o", str(tmp_path / "r.pdf")])
        assert code == 0
        assert "2024-01-05 to 2024-01-10 (6 days)" in capsys.readouterr().out

    def test_default_output(
        self, csv_file: Path, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main([str(csv_file)]) == 0
        assert (tmp_path / "output" / "report.pdf").is_file()

    def test_verbose_shows_package_debug(
        self, csv_file: Path, tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        main([str(csv_file), "-v", "-o", str(tmp_path / "r.pdf")])
        assert "Reading alpha.csv with CSVLoader" in caplog.text
        assert "Alpha: 31 of 31 records" in caplog.text
        assert logging.getLogger("weather").level == logging.DEBUG


# ---------------------------------------------------------------------------
# Data and output errors → exit code 1
# ---------------------------------------------------------------------------

class TestDataErrors:

    @pytest.mark.parametrize("extra_args, message", [
        (["--start", "2030-01-01"], "No data for Alpha"),
        (["-o", "report.txt"], "Unsupported report format"),
    ])
    def test_returns_1_with_error(
        self, csv_file: Path, tmp_path: Path, extra_args: list[str],
        message: str, caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main([str(csv_file), *extra_args]) == 1
        assert message in caplog.text
        assert not (tmp_path / "output").exists()

    def test_missing_file(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        assert main([str(tmp_path / "nowhere.csv")]) == 1
        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(errors) == 1
        assert "File not found" in errors[0].getMessage()


# ---------------------------------------------------------------------------
# Argument errors → argparse exits with code 2
# ---------------------------------------------------------------------------

class TestArgumentErrors:

    @pytest.mark.parametrize("args, message", [
        ([], "required: FILE"),
        (["x.csv", "--start", "2024-13-01"], "expected a date"),
        (["x.csv", "--start", "2024-02-01", "--end", "2024-01-01"],
         "--start must not be after --end"),
    ])
    def test_exits_2(
        self, args: list[str], message: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(args)
        assert exc_info.value.code == 2
        assert message in capsys.readouterr().err
