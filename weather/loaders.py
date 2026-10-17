import csv
import logging
from datetime import datetime
from pathlib import Path

from .models import Measurement, WeatherStation

logger = logging.getLogger(__name__)


class WeatherDataError(Exception):
    pass


class CSVLoader:
    def load(self, file_path, city):
        path = Path(file_path)

        if not path.is_file():
            raise WeatherDataError(f"File not found: {path}")

        measurements = []

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            required = {"date", "tavg", "tmin", "tmax"}

            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise WeatherDataError("Missing required CSV columns")

            for line_no, row in enumerate(reader, start=2):
                try:
                    day = datetime.fromisoformat(row["date"]).date()

                    avg = float(row["tavg"])
                    low = float(row["tmin"])
                    high = float(row["tmax"])

                    rainfall = row.get("prcp")
                    rain = float(rainfall) if rainfall and rainfall.strip() else None

                    if not low <= avg <= high:
                        raise ValueError("Temperature values are inconsistent")

                    if rain is not None and rain < 0:
                        raise ValueError("Negative rainfall")

                    measurements.append(
                        Measurement(day, avg, low, high, rain)
                    )

                except (ValueError, TypeError, KeyError) as error:
                    logger.warning("Skipping row %s: %s", line_no, error)

        if not measurements:
            raise WeatherDataError("No valid records found")

        return WeatherStation(city, measurements)
