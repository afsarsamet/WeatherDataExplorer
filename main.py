"""Weather Data Explorer — quick demo entry point.

This will be replaced with a full ``argparse``-driven CLI in Phase 5.
For now it loads every bundled city, prints the report summary and
writes ``output/report.pdf`` to verify the package works end-to-end.
"""

from pathlib import Path

from weather.loaders import load_station
from weather.logger import setup_logging
from weather.report import Report

ROOT = Path(__file__).resolve().parent
DATA_FILES = ("budapest.csv", "debrecen.csv", "vienna.json")


def main() -> None:
    setup_logging()

    stations = [load_station(ROOT / "data" / name) for name in DATA_FILES]
    report = Report(stations)

    print(report.summary_text())
    report.save(ROOT / "output" / "report.pdf")


if __name__ == "__main__":
    main()
