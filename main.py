
from pathlib import Path

from weather.loaders import CSVLoader
from weather.analysis import WeatherAnalyzer


def main():
    data_path = Path(__file__).resolve().parent / "data" / "budapest.csv"

    station = CSVLoader().load(data_path, "Budapest")
    analyzer = WeatherAnalyzer(station)

    hottest = analyzer.hottest_day()
    coldest = analyzer.coldest_day()

    print("=== Weather Data Explorer ===")
    print(f"City: {station.city}")
    print(f"Records: {len(station)}")

    print(f"Average temperature: {analyzer.average_temperature():.2f} °C")
    print(f"Highest temperature: {hottest.tmax} °C ({hottest.date})")
    print(f"Lowest temperature: {coldest.tmin} °C ({coldest.date})")

    missing_rain = sum(
        m.prcp is None for m in station.measurements
    )
    print(f"Missing precipitation values: {missing_rain}")


if __name__ == "__main__":
    main()
