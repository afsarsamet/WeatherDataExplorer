# WeatherDataExplorer

A Python toolkit for historical weather data analysis. It loads daily weather for several cities from CSV or JSON, validates it, computes statistics, and writes a PDF or PNG report with plots:
- **Statistics:** monthly averages, extremes, the temperature trend, anomaly days, frost/hot/rainy day counts and the longest dry spell.
- **Plots:** a line chart, a histogram and a heatmap.

## Requirements

- Python **3.10 or newer**
- NumPy, Matplotlib and pytest, installed from `requirements.txt`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
python main.py FILE [FILE ...] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [-o PATH] [-v]
```

| Argument | Meaning |
|---|---|
| `FILE` | One data file per city (`.csv` or `.json`). The city name is taken from the file name. |
| `--start`, `--end` | Keep only this period (both ends included). Without them, all records are used. |
| `-o`, `--output` | Report path, default `output/report.pdf`. `.pdf` writes one multi-page PDF; `.png` writes one PNG per figure. |
| `-v`, `--verbose` | Show debug messages. |

Examples:

```bash
# All three cities over the period they share → output/report.pdf
python main.py data/budapest.csv data/debrecen.csv data/vienna.json --end 2026-03-18

# Budapest in 2024 as PNGs → output/bp2024_summary.png, _temperature.png, _histogram.png, _heatmap_budapest.png
python main.py data/budapest.csv --start 2024-01-01 --end 2024-12-31 -o output/bp2024.png

# Two cities, two years
python main.py data/budapest.csv data/vienna.json --start 2023-01-01 --end 2024-12-31 -o output/compare.pdf
```

**What you get**
- The statistics for each city are printed to the terminal.
- The report has a summary page, a monthly-temperature line chart, a temperature histogram, and one month-by-year heatmap per city.
- Rows with invalid values are skipped and logged as warnings.
- A problem with the input or output gives one `ERROR` line and exit code 1.
- An invalid argument gives a usage message and exit code 2.

## Data

| File | City | Period | Source |
|---|---|---|---|
| `data/budapest.csv` | Budapest | 2021-10-17 → 2026-10-17 | Meteostat |
| `data/debrecen.csv` | Debrecen | 2021-10-17 → 2026-03-18 | Meteostat station 12882 |
| `data/vienna.json` | Vienna | 2021-10-17 → 2026-03-18 | Meteostat station 11035 (Wien Hohe Warte) |

Weather data by [Meteostat](https://meteostat.net), licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

**Adding a city:** add a file named after the city (for example `data/graz.csv`).
- It needs the columns `date` (`YYYY-MM-DD`), `tavg`, `tmin` and `tmax` in °C, plus an optional `prcp` in mm.
- A JSON file is an array of objects with the same keys.

## Tests

```bash
pytest
```

## Project layout

```
weather/            the package: models, loaders, analysis, visualization, report
main.py             command-line interface
tests/              pytest suite, one file per module
data/               city data files
docs/design.md      design document with class diagram
docs/projectGuide.md  task, architecture and project status
```
