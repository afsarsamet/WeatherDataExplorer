"""CSV data loader for the weather package.

``CSVLoader`` reads a CSV file produced by Meteostat/NOAA, validates
each row, and returns a ``WeatherStation`` populated with clean
``Measurement`` objects.  Malformed rows are logged and skipped so that
a handful of bad records never crash the pipeline.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

from .exceptions import MalformedDataError, WeatherDataError
from .models import Measurement, WeatherStation

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = frozenset({"date", "tavg", "tmin", "tmax"})


class CSVLoader:
    """Load weather observations from a CSV file.

    Expected columns (minimum): ``date``, ``tavg``, ``tmin``, ``tmax``.
    An optional ``prcp`` column is read when present.
    """

    def load(self, file_path: str | Path, city: str) -> WeatherStation:
        """Parse *file_path* and return a ``WeatherStation`` for *city*.

        Parameters
        ----------
        file_path : str | Path
            Path to the source CSV.
        city : str
            Human-readable city label attached to the station.

        Returns
        -------
        WeatherStation
            A station populated with all valid rows.

        Raises
        ------
        WeatherDataError
            If the file is missing, lacks required columns, or yields
            zero valid records.
        """
        path = Path(file_path)

        if not path.is_file():
            raise WeatherDataError(f"File not found: {path}")

        measurements: list[Measurement] = []

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
            if missing:
                raise WeatherDataError(
                    f"Missing required CSV columns: {sorted(missing)}"
                )

            for line_no, row in enumerate(reader, start=2):
                try:
                    day = datetime.fromisoformat(row["date"]).date()

                    avg = float(row["tavg"])
                    low = float(row["tmin"])
                    high = float(row["tmax"])

                    rainfall = row.get("prcp")
                    rain = (
                        float(rainfall)
                        if rainfall and rainfall.strip()
                        else None
                    )

                    if not low <= avg <= high:
                        raise MalformedDataError(
                            line_no,
                            f"Temperature order violated: "
                            f"tmin={low}, tavg={avg}, tmax={high}",
                        )

                    if rain is not None and rain < 0:
                        raise MalformedDataError(
                            line_no, f"Negative precipitation: {rain}"
                        )

                    measurements.append(
                        Measurement(day, avg, low, high, rain)
                    )

                except MalformedDataError as exc:
                    logger.warning("Skipping row %d: %s", line_no, exc.reason)

                except (ValueError, TypeError, KeyError) as exc:
                    logger.warning("Skipping row %d: %s", line_no, exc)

        if not measurements:
            raise WeatherDataError(
                f"No valid records found in {path.name}"
            )

        logger.info(
            "Loaded %d records for %s from %s",
            len(measurements), city, path.name,
        )
        return WeatherStation(city, measurements)
