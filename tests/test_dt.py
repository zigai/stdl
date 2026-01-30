from datetime import date, datetime, timedelta
from typing import Type

import pytest

from stdl.dt import date_fmt, datetime_fmt, datetime_range, hms_to_seconds, seconds_to_hms, time_fmt


@pytest.mark.parametrize(
    "time_input, ms, expected_output",
    [
        (123.456, False, "00:02:03"),
        (123.456, True, "00:02:03.456"),
        (123, False, "00:02:03"),
        (123.0, True, "00:02:03.000"),
        (-123.456, False, "-00:02:03"),
        (-123.456, True, "-00:02:03.456"),
        (-0.5, True, "-00:00:00.500"),
        (0, False, "00:00:00"),
        (0.0, True, "00:00:00.000"),
        (3600, False, "01:00:00"),
        (3661.5, True, "01:01:01.500"),
        (90321.789, False, "25:05:21"),
        (90321.789, True, "25:05:21.789"),
    ],
)
def test_seconds_to_hms(time_input: float, ms: bool, expected_output: Type[Exception]):
    assert seconds_to_hms(time_input, ms) == expected_output


@pytest.mark.parametrize(
    "time_input, ms, expected_output, expected_exception",
    [
        ("00:02:03", False, 123.0, None),
        ("1:02:03", False, 3723.0, None),
        ("2:3", False, 123.0, None),
        ("0:0:0", False, 0.0, None),
        ("123", False, 123.0, None),
        ("-1:02:03", False, -3723.0, None),  # Negative time
        ("00:02:03.456", True, 123.456, None),
        ("00:02:03.4", True, 123.4, None),
        ("00:02:03.45", True, 123.45, None),
        ("00:02:03.045", True, 123.045, None),
        ("23:59:59.999", True, 23 * 3600 + 59 * 60 + 59.999, None),
        ("12:34.567", True, 12 * 60 + 34.567, None),  # Valid m:s.ms format
        ("00:00:00", False, 0.0, None),
        ("0:0", False, 0.0, None),
        ("1:60", False, None, ValueError),  # Invalid seconds
        ("1:02:60", False, None, ValueError),  # Invalid seconds
        ("invalid_time", False, None, ValueError),
        ("1:2:3:4", False, None, ValueError),  # Too many parts
        ("12:34:56.789x", True, None, ValueError),  # Invalid characters in ms
    ],
)
def test_hms_to_seconds(
    time_input: str,
    ms: bool,
    expected_output: str,
    expected_exception: Type[Exception],
):
    if expected_exception:
        with pytest.raises(expected_exception):
            x = hms_to_seconds(time_input, ms)
            print(time_input, ms, x)
    else:
        result = hms_to_seconds(time_input, ms)
        assert result == pytest.approx(expected_output, abs=1e-9)


def test_documentation_examples():
    assert seconds_to_hms(123.456) == "00:02:03"
    assert seconds_to_hms(123.456, ms=True) == "00:02:03.456"
    assert hms_to_seconds("00:02:03.456", ms=True) == pytest.approx(123.456)
    assert hms_to_seconds("2:3", ms=True) == pytest.approx(123.0)
    assert hms_to_seconds("-00:02:03", ms=False) == -123.0
    assert hms_to_seconds("00:02:03", ms=False) == 123.0
    assert hms_to_seconds("-1:02:03", ms=False) == pytest.approx(-3723.0)


def test_millisecond_padding():
    assert hms_to_seconds("00:00:00.1", ms=True) == pytest.approx(0.1)
    assert hms_to_seconds("00:00:00.01", ms=True) == pytest.approx(0.01)
    assert hms_to_seconds("00:00:00.001", ms=True) == pytest.approx(0.001)


def test_negative_time_roundtrip():
    original_seconds = -123.456
    time_str = seconds_to_hms(original_seconds, ms=True)
    parsed_seconds = hms_to_seconds(time_str, ms=True)
    assert parsed_seconds == original_seconds


def test_time_fmt():
    assert time_fmt(0) == "00:00:00"
    assert time_fmt(0, ms=True) == "00:00:00.000"
    assert time_fmt(1, ms=True) == "00:00:01.000"


def test_datetime_fmt():
    assert datetime_fmt(0.0, utc=True) == "1970-01-01 00:00:00"
    assert datetime_fmt(0) == "1970-01-01 00:00:00"
    assert datetime_fmt(0, fmt="dmY") == "01-01-1970 00:00:00"
    assert datetime_fmt(0, fmt="dmY", dsep="/") == "01/01/1970 00:00:00"
    assert datetime_fmt(0, fmt="dmY", dsep="/", tsep=".") == "01/01/1970 00.00.00"


def test_date_fmt():
    assert date_fmt(date(1970, 1, 1)) == "1970-01-01"
    assert date_fmt(0) == "1970-01-01"


class TestDatetimeRange:
    def test_basic_positive_step(self):
        """Test datetime_range with positive step."""
        start = datetime(2026, 1, 27, 0, 0)
        end = datetime(2026, 1, 27, 3, 0)
        step = timedelta(hours=1)
        result = list(datetime_range(start, end, step))
        expected = [
            datetime(2026, 1, 27, 0, 0),
            datetime(2026, 1, 27, 1, 0),
            datetime(2026, 1, 27, 2, 0),
        ]
        assert result == expected

    def test_basic_negative_step(self):
        """Test datetime_range with negative step (going backwards)."""
        start = datetime(2026, 1, 27, 3, 0)
        end = datetime(2026, 1, 27, 0, 0)
        step = timedelta(hours=-1)
        result = list(datetime_range(start, end, step))
        expected = [
            datetime(2026, 1, 27, 3, 0),
            datetime(2026, 1, 27, 2, 0),
            datetime(2026, 1, 27, 1, 0),
        ]
        assert result == expected

    def test_zero_step_raises(self):
        """Test that zero step raises ValueError."""
        start = datetime(2026, 1, 27, 0, 0)
        end = datetime(2026, 1, 27, 3, 0)
        step = timedelta(0)
        with pytest.raises(ValueError, match="step cannot be zero"):
            list(datetime_range(start, end, step))

    def test_empty_range_positive_step(self):
        """Test when start >= end with positive step."""
        start = datetime(2026, 1, 27, 3, 0)
        end = datetime(2026, 1, 27, 0, 0)
        step = timedelta(hours=1)
        result = list(datetime_range(start, end, step))
        assert result == []

    def test_empty_range_negative_step(self):
        """Test when start <= end with negative step."""
        start = datetime(2026, 1, 27, 0, 0)
        end = datetime(2026, 1, 27, 3, 0)
        step = timedelta(hours=-1)
        result = list(datetime_range(start, end, step))
        assert result == []

    def test_minute_step(self):
        """Test with minute-level precision."""
        start = datetime(2026, 1, 27, 0, 0)
        end = datetime(2026, 1, 27, 0, 5)
        step = timedelta(minutes=1)
        result = list(datetime_range(start, end, step))
        expected = [
            datetime(2026, 1, 27, 0, 0),
            datetime(2026, 1, 27, 0, 1),
            datetime(2026, 1, 27, 0, 2),
            datetime(2026, 1, 27, 0, 3),
            datetime(2026, 1, 27, 0, 4),
        ]
        assert result == expected

    def test_second_step(self):
        """Test with second-level precision."""
        start = datetime(2026, 1, 27, 0, 0, 0)
        end = datetime(2026, 1, 27, 0, 0, 3)
        step = timedelta(seconds=1)
        result = list(datetime_range(start, end, step))
        expected = [
            datetime(2026, 1, 27, 0, 0, 0),
            datetime(2026, 1, 27, 0, 0, 1),
            datetime(2026, 1, 27, 0, 0, 2),
        ]
        assert result == expected

    def test_day_step(self):
        """Test with day-level step across multiple days."""
        start = datetime(2026, 1, 27)
        end = datetime(2026, 1, 30)
        step = timedelta(days=1)
        result = list(datetime_range(start, end, step))
        expected = [
            datetime(2026, 1, 27),
            datetime(2026, 1, 28),
            datetime(2026, 1, 29),
        ]
        assert result == expected

    def test_partial_step(self):
        """Test when end is not exactly reachable by step."""
        start = datetime(2026, 1, 27, 0, 0)
        end = datetime(2026, 1, 27, 2, 30)
        step = timedelta(hours=1)
        result = list(datetime_range(start, end, step))
        expected = [
            datetime(2026, 1, 27, 0, 0),
            datetime(2026, 1, 27, 1, 0),
            datetime(2026, 1, 27, 2, 0),
        ]
        assert result == expected

    def test_documentation_example(self):
        """Test the exact example from the docstring."""
        result = list(
            datetime_range(
                datetime(2026, 1, 27, 0, 0),
                datetime(2026, 1, 27, 3, 0),
                timedelta(hours=1),
            )
        )
        expected = [
            datetime(2026, 1, 27, 0, 0),
            datetime(2026, 1, 27, 1, 0),
            datetime(2026, 1, 27, 2, 0),
        ]
        assert result == expected
