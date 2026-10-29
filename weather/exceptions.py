"""Custom exception hierarchy for the weather package.

Two focused exception classes provide structured error handling:
- WeatherDataError is the package-level root exception.
- MalformedDataError targets individual rows with invalid data.
"""


class WeatherDataError(Exception):
    """Base exception for all weather-data related errors.

    Raised when a systemic problem prevents processing, such as a
    missing file or a CSV that contains none of the required columns.
    """


class MalformedDataError(WeatherDataError):
    """Raised when a single data row contains invalid or inconsistent values.

    Examples include non-numeric temperature fields, unparsable dates,
    or logically impossible values (tmin > tmax).

    Attributes:
        line_number: The 1-based line number in the source file.
        reason: Human-readable description of the problem.
    """

    def __init__(self, line_number: int, reason: str) -> None:
        self.line_number = line_number
        self.reason = reason
        super().__init__(f"Line {line_number}: {reason}")
