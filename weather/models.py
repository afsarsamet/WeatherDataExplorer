from dataclasses import dataclass
from datetime import date


@dataclass
class Measurement:
    date: date
    tavg: float
    tmin: float
    tmax: float
    prcp: float | None = None


class WeatherStation:
    def __init__(self, city: str, measurements: list[Measurement]):
        self.city = city
        self.measurements = measurements

    def __len__(self):
        return len(self.measurements)
