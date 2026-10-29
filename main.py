"""Weather Data Explorer — command-line entry point.

Loads one data file per city, keeps the selected period, prints the
statistics and writes a PDF (or PNG) report with plots::

    python main.py data/budapest.csv data/vienna.json \\
        --start 2023-01-01 --end 2025-12-31 -o output/report.pdf

Exit codes: 0 on success, 1 for a data or output problem (logged as one
``ERROR`` line), 2 for invalid arguments (reported by argparse).
"""

import argparse
import logging
from datetime import date
from pathlib import Path

from weather.exceptions import WeatherDataError
from weather.loaders import load_station
from weather.logger import setup_logging
from weather.models import WeatherStation
from weather.report import Report

logger = logging.getLogger("weather")

DEFAULT_OUTPUT = Path("output/report.pdf")


def iso_date(text: str) -> date:
    """argparse type for ``YYYY-MM-DD`` dates with a readable error."""
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"expected a date as YYYY-MM-DD, got {text!r}"
        ) from None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments (``sys.argv`` when *argv* is None)."""
    parser = argparse.ArgumentParser(
        description="Generate a weather report with statistics and plots "
                    "for selected cities and periods.",
        epilog="example: python main.py data/budapest.csv data/vienna.json "
               "--start 2023-01-01 --end 2025-12-31",
    )
    parser.add_argument(
        "files", nargs="+", type=Path, metavar="FILE",
        help="city data file (.csv or .json); the file name is the city",
    )
    parser.add_argument(
        "--start", type=iso_date, metavar="YYYY-MM-DD",
        help="first day to include (default: earliest record)",
    )
    parser.add_argument(
        "--end", type=iso_date, metavar="YYYY-MM-DD",
        help="last day to include (default: latest record)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_OUTPUT, metavar="PATH",
        help=".pdf for one PDF, .png for one PNG per figure "
             "(default: %(default)s)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show debug logging",
    )
    args = parser.parse_args(argv)
    if args.start and args.end and args.start > args.end:
        parser.error("--start must not be after --end")
    return args


def select_period(
    station: WeatherStation, start: date | None, end: date | None
) -> WeatherStation:
    """Cut *station* to ``[start, end]``; fail if nothing is left."""
    selected = station.filter_dates(start, end)
    logger.debug("%s: %d of %d records in the selected period",
                 station.city, len(selected), len(station))
    if not len(selected):
        raise WeatherDataError(
            f"No data for {station.city} in the selected period"
        )
    return selected


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    args = parse_args(argv)
    setup_logging(args.verbose)

    try:
        stations = [
            select_period(load_station(path), args.start, args.end)
            for path in args.files
        ]
        report = Report(stations)
        report.save(args.output)
    except WeatherDataError as exc:
        logger.error("%s", exc)
        return 1

    print(report.summary_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
