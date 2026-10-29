"""Weather Data Explorer — quick demo entry point.

This will be replaced with a full ``argparse``-driven CLI in Phase 5.
For now it loads the Budapest dataset and prints basic statistics to
verify the package works end-to-end.
"""

from pathlib import Path

from weather.logger import setup_logging
from weather.loaders import load_station
from weather.analysis import WeatherAnalyzer


def main() -> None:
    setup_logging()

    data_path = Path(__file__).resolve().parent / "data" / "budapest.csv"

    station = load_station(data_path)
    analyzer = WeatherAnalyzer(station)

    hottest = analyzer.hottest_day()
    coldest = analyzer.coldest_day()

    print("=== Weather Data Explorer ===")
    print(f"City: {station.city}")
    print(f"Records: {len(station)}")
    print(f"Date range: {station.measurements[0].date} → "
          f"{station.measurements[-1].date}")
    print()
    print(f"Average temperature: {analyzer.average_temperature():.2f} °C")
    print(f"Highest temperature: {hottest.tmax} °C ({hottest.date})")
    print(f"Lowest temperature:  {coldest.tmin} °C ({coldest.date})")

    missing_rain = sum(1 for m in station if m.prcp is None)
    print(f"Missing precipitation values: {missing_rain}")


if __name__ == "__main__":
    main()
