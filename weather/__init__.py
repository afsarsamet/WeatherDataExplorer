"""weather — A Pythonic Analysis Toolkit for historical weather data.

Public API re-exported here for convenient imports::

    from weather import load_station, CSVLoader, JSONLoader
    from weather import Measurement, WeatherStation
    from weather import WeatherDataError, MalformedDataError
    from weather import setup_logging
    from weather import analysis          # analysis.summary(station), ...
"""

from weather.exceptions import MalformedDataError, WeatherDataError
from weather.loaders import BaseLoader, CSVLoader, JSONLoader, load_station
from weather.logger import setup_logging
from weather.models import Measurement, WeatherStation

__all__ = [
    "BaseLoader",
    "CSVLoader",
    "JSONLoader",
    "load_station",
    "Measurement",
    "WeatherStation",
    "WeatherDataError",
    "MalformedDataError",
    "setup_logging",
]
