"""Weather Data Explorer — quick demo entry point.

This will be replaced with a full ``argparse``-driven CLI in Phase 5.
For now it loads every bundled city and prints its statistics to verify
the package works end-to-end.
"""

from pathlib import Path

from weather import analysis
from weather.loaders import load_station
from weather.logger import setup_logging

DATA_FILES = ("budapest.csv", "debrecen.csv", "vienna.json")


def main() -> None:
    setup_logging()

    data_dir = Path(__file__).resolve().parent / "data"

    for name in DATA_FILES:
        station = load_station(data_dir / name)
        stats = analysis.summary(station)
        ext = analysis.extremes(station)
        counts = analysis.day_counts(station)
        wettest = ext["wettest"]

        print(f"\n=== {station.city} ===")
        print(f"Records: {len(station)}  "
              f"({station.measurements[0].date} → "
              f"{station.measurements[-1].date})")
        print(f"Temperature: mean {stats['mean']:.2f} °C, "
              f"median {stats['median']:.2f} °C, "
              f"stdev {stats['stdev']:.2f} °C")
        print(f"Hottest: {ext['hottest'].tmax} °C ({ext['hottest'].date})")
        print(f"Coldest: {ext['coldest'].tmin} °C ({ext['coldest'].date})")
        if wettest is not None:
            print(f"Wettest: {wettest.prcp} mm ({wettest.date})")
        print(f"Trend: {analysis.temperature_trend(station):+.2f} °C/year")
        print(f"Anomaly days: {len(analysis.anomaly_days(station))}")
        print(f"Frost / hot / rainy days: {counts['frost']} / "
              f"{counts['hot']} / {counts['rainy']}")
        print(f"Longest dry spell: {analysis.longest_dry_spell(station)} days")
        print(f"Months covered: {len(analysis.monthly_averages(station))}")


if __name__ == "__main__":
    main()
