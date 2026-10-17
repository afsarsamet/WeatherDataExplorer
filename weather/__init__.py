"""weather — A Pythonic Analysis Toolkit for historical weather data.

Public API re-exported here for convenient imports::

    from weather import CSVLoader, WeatherAnalyzer
    from weather import Measurement, WeatherStation
    from weather import WeatherDataError, MalformedDataError
    from weather import setup_logging
"""

from weather.analysis import WeatherAnalyzer
from weather.exceptions import MalformedDataError, WeatherDataError
from weather.loaders import CSVLoader
from weather.logger import setup_logging
from weather.models import Measurement, WeatherStation

__all__ = [
    "CSVLoader",
    "WeatherAnalyzer",
    "Measurement",
    "WeatherStation",
    "WeatherDataError",
    "MalformedDataError",
    "setup_logging",
]
