"""Data loaders for the weather package.

``BaseLoader`` holds the shared loading steps (file check, row parsing,
skipping malformed rows, logging); subclasses only say how to read raw
rows from their format.  ``CSVLoader`` and ``JSONLoader`` produce the same
``WeatherStation`` from equivalent files, and ``load_station`` picks the
right loader from the file extension.
"""

import csv
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from .exceptions import MalformedDataError, WeatherDataError
from .models import Measurement, WeatherStation

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = frozenset({"date", "tavg", "tmin", "tmax"})


def parse_row(row: dict, line_no: int) -> Measurement:
    """Convert one raw record into a ``Measurement``.

    Values may be strings (CSV) or numbers/``null`` (JSON).  An empty or
    missing ``prcp`` becomes ``None``.

    Raises
    ------
    MalformedDataError
        For any unparsable, missing, or physically impossible value.
    """
    if not isinstance(row, dict):
        raise MalformedDataError(line_no, "Record is not an object")

    try:
        rain = row.get("prcp")
        has_rain = rain is not None and str(rain).strip() != ""
        return Measurement(
            date=datetime.fromisoformat(str(row["date"])).date(),
            tavg=float(row["tavg"]),
            tmin=float(row["tmin"]),
            tmax=float(row["tmax"]),
            prcp=float(rain) if has_rain else None,
        )
    except KeyError as exc:
        raise MalformedDataError(line_no, f"Missing field {exc}") from exc
    except (ValueError, TypeError) as exc:
        raise MalformedDataError(line_no, str(exc)) from exc


class BaseLoader(ABC):
    """Template for loaders: subclasses implement ``read_rows`` only."""

    #: Line/record number of the first data row (used in warnings).
    FIRST_ROW = 1

    def load(self, file_path: str | Path, city: str) -> WeatherStation:
        """Parse *file_path* and return a ``WeatherStation`` for *city*.

        Malformed rows are logged as warnings and skipped.

        Raises
        ------
        WeatherDataError
            If the file is missing, unreadable, invalid for its format, or
            yields zero valid records.
        """
        path = Path(file_path)

        if not path.is_file():
            raise WeatherDataError(f"File not found: {path}")

        measurements: list[Measurement] = []

        try:
            rows = self.read_rows(path)
        except (OSError, UnicodeDecodeError) as exc:
            raise WeatherDataError(f"Cannot read {path.name}: {exc}") from exc

        for line_no, row in enumerate(rows, start=self.FIRST_ROW):
            try:
                measurements.append(parse_row(row, line_no))
            except MalformedDataError as exc:
                logger.warning("Skipping row %d: %s", line_no, exc.reason)

        if not measurements:
            raise WeatherDataError(f"No valid records found in {path.name}")

        logger.info(
            "Loaded %d records for %s from %s",
            len(measurements), city, path.name,
        )
        return WeatherStation(city, measurements)

    @abstractmethod
    def read_rows(self, path: Path) -> list[dict]:
        """Return the raw records of *path* as a list of dicts."""


class CSVLoader(BaseLoader):
    """Load a CSV with ``date, tavg, tmin, tmax`` and optional ``prcp``."""

    FIRST_ROW = 2  # line 1 is the header

    def read_rows(self, path: Path) -> list[dict]:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
            if missing:
                raise WeatherDataError(
                    f"Missing required CSV columns: {sorted(missing)}"
                )

            return list(reader)


class JSONLoader(BaseLoader):
    """Load a JSON array of objects using the same keys as the CSV."""

    def read_rows(self, path: Path) -> list[dict]:
        with path.open("r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as exc:
                raise WeatherDataError(
                    f"Invalid JSON in {path.name}: {exc}"
                ) from exc

        if not isinstance(data, list):
            raise WeatherDataError(
                f"Expected a JSON array of records in {path.name}"
            )
        return data


LOADERS: dict[str, type[BaseLoader]] = {".csv": CSVLoader, ".json": JSONLoader}


def load_station(file_path: str | Path) -> WeatherStation:
    """Load *file_path* with the loader matching its extension.

    The city name comes from the file name: ``vienna.json`` → ``"Vienna"``.
    """
    path = Path(file_path)
    loader_cls = LOADERS.get(path.suffix.lower())
    if loader_cls is None:
        raise WeatherDataError(
            f"Unsupported file type: {path.suffix or path.name}"
        )
    return loader_cls().load(path, path.stem.title())
