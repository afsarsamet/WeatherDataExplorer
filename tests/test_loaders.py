"""Unit tests for weather.loaders — CSVLoader, JSONLoader, load_station.

Covers:
- CSV and JSON files with the same data load the same measurements
- Malformed rows are skipped and logged, valid rows still load
- File-level problems raise WeatherDataError
- parse_row wraps every bad value in MalformedDataError
- load_station dispatches on extension and names the city from the file
"""

import datetime
import json
import logging
from pathlib import Path

import pytest

from weather.exceptions import MalformedDataError, WeatherDataError
from weather.loaders import CSVLoader, JSONLoader, load_station, parse_row
from weather.models import Measurement

CSV_TEXT = (
    "date,tavg,tmin,tmax,prcp\n"
    "2024-01-01 00:00:00,1.0,-2.0,4.0,0.5\n"
    "2024-01-02 00:00:00,2.0,-1.0,5.0,\n"
)

RECORDS = [
    {"date": "2024-01-01", "tavg": 1.0, "tmin": -2.0, "tmax": 4.0,
     "prcp": 0.5},
    {"date": "2024-01-02", "tavg": 2.0, "tmin": -1.0, "tmax": 5.0,
     "prcp": None},
]

EXPECTED = [
    Measurement(datetime.date(2024, 1, 1), 1.0, -2.0, 4.0, 0.5),
    Measurement(datetime.date(2024, 1, 2), 2.0, -1.0, 5.0, None),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "test_city.csv"
    path.write_text(CSV_TEXT, encoding="utf-8")
    return path


@pytest.fixture
def json_file(tmp_path: Path) -> Path:
    path = tmp_path / "test_city.json"
    path.write_text(json.dumps(RECORDS), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# parse_row tests
# ---------------------------------------------------------------------------

class TestParseRow:
    """Verify conversion of a single raw record."""

    def test_string_values(self) -> None:
        row = {"date": "2024-01-01", "tavg": "1", "tmin": "-2",
               "tmax": "4", "prcp": "0.5"}
        assert parse_row(row, 2) == EXPECTED[0]

    def test_numeric_values(self) -> None:
        assert parse_row(RECORDS[0], 1) == EXPECTED[0]

    @pytest.mark.parametrize("prcp", ["", "  ", None])
    def test_empty_precipitation_is_none(self, prcp: str | None) -> None:
        row = {"date": "2024-01-01", "tavg": 1, "tmin": 0, "tmax": 2,
               "prcp": prcp}
        assert parse_row(row, 2).prcp is None

    @pytest.mark.parametrize("row, reason", [
        ({"date": "not-a-date", "tavg": 1, "tmin": 0, "tmax": 2}, "date"),
        ({"date": "2024-01-01", "tavg": "abc", "tmin": 0, "tmax": 2}, "float"),
        ({"date": "2024-01-01", "tavg": None, "tmin": 0, "tmax": 2}, "float"),
        ({"date": "2024-01-01", "tavg": "nan", "tmin": 0, "tmax": 2},
         "Non-finite"),
        ({"date": "2024-01-01", "tmin": 0, "tmax": 2}, "Missing field"),
        ({"date": "2024-01-01", "tavg": 5, "tmin": 0, "tmax": 2},
         "Temperature order"),
        ({"date": "2024-01-01", "tavg": 1, "tmin": 0, "tmax": 2, "prcp": -1},
         "Negative precipitation"),
    ])
    def test_bad_rows_raise_malformed(self, row: dict, reason: str) -> None:
        with pytest.raises(MalformedDataError, match=reason) as exc_info:
            parse_row(row, 7)
        assert exc_info.value.line_number == 7


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------

class TestLoaders:
    """Verify CSVLoader and JSONLoader behaviour."""

    def test_csv_loads_measurements(self, csv_file: Path) -> None:
        station = CSVLoader().load(csv_file, "Test")
        assert station.city == "Test"
        assert station.measurements == EXPECTED

    def test_json_loads_same_measurements(self, json_file: Path) -> None:
        station = JSONLoader().load(json_file, "Test")
        assert station.measurements == EXPECTED

    def test_bad_csv_row_skipped_and_logged(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        path = tmp_path / "bad.csv"
        path.write_text(CSV_TEXT + "2024-01-03,oops,0,1,\n", encoding="utf-8")
        with caplog.at_level(logging.WARNING):
            station = CSVLoader().load(path, "Test")
        assert len(station) == 2
        assert "Skipping row 4" in caplog.text

    def test_bad_json_record_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(RECORDS + [{"date": "x"}, 42]),
                        encoding="utf-8")
        assert len(JSONLoader().load(path, "Test")) == 2

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(WeatherDataError, match="File not found"):
            CSVLoader().load(tmp_path / "nope.csv", "Test")

    def test_missing_csv_columns(self, tmp_path: Path) -> None:
        path = tmp_path / "cols.csv"
        path.write_text("date,tavg\n2024-01-01,1.0\n", encoding="utf-8")
        with pytest.raises(WeatherDataError, match="tmax"):
            CSVLoader().load(path, "Test")

    def test_non_utf8_file(self, tmp_path: Path) -> None:
        path = tmp_path / "binary.csv"
        path.write_bytes(b"\xff\xfe\x00garbage")
        with pytest.raises(WeatherDataError, match="Cannot read"):
            CSVLoader().load(path, "Test")

    def test_invalid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "broken.json"
        path.write_text("[{", encoding="utf-8")
        with pytest.raises(WeatherDataError, match="Invalid JSON"):
            JSONLoader().load(path, "Test")

    def test_json_not_a_list(self, tmp_path: Path) -> None:
        path = tmp_path / "obj.json"
        path.write_text(json.dumps(RECORDS[0]), encoding="utf-8")
        with pytest.raises(WeatherDataError, match="JSON array"):
            JSONLoader().load(path, "Test")

    def test_no_valid_rows(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.csv"
        path.write_text("date,tavg,tmin,tmax\nx,y,z,w\n", encoding="utf-8")
        with pytest.raises(WeatherDataError, match="No valid records"):
            CSVLoader().load(path, "Test")


# ---------------------------------------------------------------------------
# load_station tests
# ---------------------------------------------------------------------------

class TestLoadStation:
    """Verify extension dispatch and city naming."""

    def test_csv_city_from_file_name(self, csv_file: Path) -> None:
        assert load_station(csv_file).city == "Test_City"

    def test_json_dispatch(self, json_file: Path) -> None:
        assert load_station(json_file).measurements == EXPECTED

    def test_unsupported_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "data.txt"
        path.write_text("hello", encoding="utf-8")
        with pytest.raises(WeatherDataError, match="Unsupported file type"):
            load_station(path)
