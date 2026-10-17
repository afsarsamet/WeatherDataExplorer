# Weather Data Explorer: Final Project Blueprint

> **Status:** Phase 1 complete (✅). Phases 2–5 pending. See [walkthrough.md](walkthrough.md) for the walkthrough of the current state.
> Legend in the layout below: ✅ exists now, ⏳ planned.

## 1. Repository Layout

Plaintext

```
WeatherDataExplorer/
│
├── data/
│   ├── budapest.csv               # ✅ Historical daily CSV for Budapest (1,827 rows)
│   ├── kecskemet.csv              # ⏳ Second city CSV to fulfill multi-city analysis
│   └── budapest.json              # ⏳ Sample JSON export for loader parity verification
│
├── weather/
│   ├── __init__.py                # ✅ Package exports
│   ├── exceptions.py              # ✅ WeatherDataError & MalformedDataError
│   ├── logger.py                  # ✅ setup_logging() utility
│   ├── models.py                  # ✅ Measurement dataclass & WeatherStation class
│   ├── loaders.py                 # ✅ CSVLoader (with REQUIRED_COLUMNS check); ⏳ BaseLoader(ABC) + JSONLoader
│   ├── analysis.py                # ✅ placeholder WeatherAnalyzer; ⏳ replaced by pure functions (statistics + numpy + collections + itertools)
│   ├── visualization.py           # ⏳ Matplotlib figures (line, hist, heatmap)
│   └── report.py                  # ⏳ Report class (multi-city aggregation & PDF/PNG export)
│
├── tests/                         # no __init__.py needed: pyproject.toml sets pythonpath
│   ├── test_models.py             # ✅ 21 tests: entity checks & dunder contracts
│   ├── test_loaders.py            # ⏳ CSV/JSON ingestion & malformed row tolerance
│   └── test_analysis.py           # ⏳ Verification of math & aggregations
│
├── docs/
│   ├── walkthrough.md             # ✅ Tour of the current codebase (update after each phase)
│   ├── roadmap.md                 # ✅ This file
│   ├── design_document.md         # ⏳ Architecture summary & design choices
│   └── class_diagram.png          # ⏳ UML diagram (Measurement, WeatherStation, Loaders, Report)
│
├── .vscode/settings.json          # ✅ Use .venv interpreter, hide cache folders
├── main.py                        # ✅ simple demo script; ⏳ becomes argparse CLI (multi-city support)
├── pyproject.toml                 # ✅ pytest config (testpaths, pythonpath)
├── requirements.txt               # ✅ numpy, matplotlib, pytest
├── .gitignore                     # ✅ Ignores .venv, __pycache__, output files, .pytest_cache
├── README.md                      # ✅ minimal; ⏳ full setup, CLI flags, sample commands
└── Task.md                        # ✅ Original assignment
```

## 2. Module Blueprint & Technical Mapping

### `weather/logger.py`

A single helper to configure standard Python logging without boilerplate:

Python

```
import logging

def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )
```

### `weather/exceptions.py`

Two focused classes:

- `WeatherDataError(Exception)`: Package root exception (missing file, bad header, no valid records).
- `MalformedDataError(WeatherDataError)`: Carries `line_number` and `reason`; raised for invalid dates, non-numeric temperatures, `tmin <= tavg <= tmax` violations, or negative precipitation.

### `weather/models.py`

- **`Measurement` (`@dataclass(frozen=True, slots=True)`):** ✅
    - Attributes: `date: datetime.date`, `tavg: float`, `tmin: float`, `tmax: float`, `prcp: float | None = None`.
    - `__lt__(self, other)`: Compares dates (returns `NotImplemented` for other types); `__repr__` shows `N/A` for missing prcp.
- **`WeatherStation`:** ✅
    - Attributes: `city: str`, `measurements: list[Measurement]` (sorted chronologically on construction).
    - `__len__`, `__iter__` (typed `Iterator[Measurement]`), `__repr__`.
    - `filter_dates(start_date, end_date) -> WeatherStation`: Returns a new `WeatherStation` using a list comprehension.

### `weather/loaders.py`

Polymorphic loaders satisfying inheritance and multi-format requirements:

- **`BaseLoader(ABC)`** (Phase 2): Defines `@abstractmethod def load(self, path: Path, city: str) -> WeatherStation:`; move the shared row validation here so both loaders reuse it.
- **`CSVLoader`** (✅ exists standalone; Phase 2 makes it inherit `BaseLoader`): `csv.DictReader` with `utf-8-sig`, rejects files missing `REQUIRED_COLUMNS`, skips corrupted rows (catching `MalformedDataError`/`ValueError`), logs warnings via the module logger, raises `WeatherDataError` if no valid rows remain.
- **`JSONLoader(BaseLoader)`**: Reads structured JSON arrays via `json.load()` using the same validation logic.
- **`load_dataset(path: Path, city: str) -> WeatherStation`**: Simple dispatch function matching file extensions (`.csv` vs `.json`) to the correct loader.

### `weather/analysis.py`

Currently a placeholder `WeatherAnalyzer` class (`average_temperature`, `hottest_day`, `coldest_day`) used by `main.py`. In Phase 3, replace it with a pure functional layer combining the Standard Library and NumPy (and update `main.py`/`__init__.py` exports and the walkthrough.md accordingly):

- **`statistics` module:** Computes high-level scalar summaries for textual reports (`statistics.mean`, `statistics.median`, `statistics.stdev` on valid temperature arrays).
- **`numpy`:** Vectorized computations on arrays:
    - Rolling 7-day temperature means.
    - Anomaly detection: isolating days where $\vert{}T_{avg} - \mu\vert{} > 2\sigma$.
    - Extreme records ($T_{max}$, $T_{min}$, max rainfall).
- **`collections.defaultdict`:** Groups measurements by `(year, month)` to produce monthly average tables.
- **`collections.Counter`:** Counts weather categories (e.g., Freezing Days: $T_{min} < 0$, Rain Days: $Prcp > 0$, Heatwave Days: $T_{max} \ge 30$).
- **`itertools.groupby`:** Detects continuous runs (e.g., longest consecutive streak of dry days where $Prcp == 0$ or `None`).

### `weather/visualization.py`

Three plotting functions returning Matplotlib `Figure` objects:

- `plot_temperature_trends(stations, anomalies_by_city)`: Multi-line plot supporting one or several cities over time, with anomaly scatter points.
- `plot_precipitation_hist(stations)`: Comparative or single-city rainfall distribution histogram.
- `plot_monthly_heatmap(monthly_data, city_name)`: Grid heatmap showing month-by-month temperature variations.

### `weather/report.py`

The orchestration class requested by the project prompt:

- **`Report`:**
    - Initialized with: `stations: list[WeatherStation]`, `output_path: Path`.
    - `generate(format: str = "pdf") -> None`:
        1. Computes text summary statistics using `statistics` and `analysis.py`.
        2. Builds the three Matplotlib figures from `visualization.py`.
        3. Writes a multi-page PDF via `matplotlib.backends.backend_pdf.PdfPages` (or a multi-panel PNG dashboard), embedding both the formatted summary tables and the figures.
        4. Explicitly closes figures to free memory.

### `main.py`

CLI interface driven by `argparse`:

- Flags:
    - `--files` / `-f`: Accepts one or more paths (e.g., `--files data/budapest.csv data/kecskemet.csv`).
    - `--cities` / `-c`: Optional city label overrides matching input files.
    - `--start-date` / `--end-date`: ISO date strings (`YYYY-MM-DD`).
    - `--format`: `pdf` (default) or `png`.
    - `--output` / `-o`: Output filepath for the report.
    - `--verbose` / `-v`: Flag calling `setup_logging(verbose=True)`.

## 3. Five-Step Implementation Order

1. **Phase 1: Package Skeleton & Domain Models** ✅ **DONE**
    - `requirements.txt`, `pyproject.toml` (pytest config), `.venv` + `.vscode/settings.json`.
    - `weather/logger.py`, `weather/exceptions.py`, `weather/models.py`.
    - A working `CSVLoader`, placeholder `WeatherAnalyzer`, and demo `main.py`.
    - 21 passing tests in `tests/test_models.py`.
2. **Phase 2: Ingestion & Validation** ⏳ **NEXT**
    - Extract `BaseLoader(ABC)`, make `CSVLoader` inherit it, add `JSONLoader` and `load_dataset()` in `weather/loaders.py`.
    - Add `data/kecskemet.csv` and a sample `data/budapest.json`.
    - Verify corrupted rows trigger `MalformedDataError`, get logged as warnings, and don't halt processing.
    - Add loader assertions to `tests/test_loaders.py`.
3. **Phase 3: Computations (Standard Library & NumPy)**
    - Implement scalar summary metrics using `statistics` in `weather/analysis.py`.
    - Implement NumPy array conversion, rolling means, and anomaly calculations.
    - Add aggregations using `defaultdict`, `Counter`, and `itertools.groupby`.
    - Add assertions with synthetic data in `tests/test_analysis.py`.
4. **Phase 4: Plotting & Report Orchestration**
    - Write line, histogram, and heatmap generators in `weather/visualization.py`.
    - Implement the `Report` class in `weather/report.py` to compile plots and metrics into PDF/PNG.
5. **Phase 5: CLI, Test Suite & Documentation**
    - Wire multi-city arguments and date filtering in `main.py`.
    - Run full test pass via `pytest tests/`.
    - Create `docs/design_document.md` and export `docs/class_diagram.png`.
    - Remove scratch scripts (`inspect_data.py`) and write `README.md`.