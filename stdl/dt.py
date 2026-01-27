import random
import time
from collections.abc import Generator
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone, tzinfo

from dateutil.parser import parse as parse_datetime_str

local_timezone: tzinfo | None = datetime.now().astimezone().tzinfo


@dataclass
class TimerStop:
    total: timedelta
    since_last: timedelta
    at: float
    label: str | None = None

    def __str__(self) -> str:
        if self.label is None:
            return f"total={self.total}, since_last=({self.since_last}), at={datetime_fmt(self.at)}"
        return f"{self.label} | total={self.total}, since_last={self.since_last}, at={datetime_fmt(self.at)}"

    def total_seconds(self, *, r: int | None = None) -> float:
        seconds = self.total.total_seconds()
        if r is not None:
            return round(seconds, r)
        return seconds


class Timer:
    """A simple timer class that keeps track of all the stops."""

    def __init__(self, *, ms: bool = True) -> None:
        self.ms = ms
        self.reset()

    def stop(self, label: str | None = None) -> TimerStop:
        """
        Stop the timer.

        Args:
            label (str | None, optional): Label for the stop.

        Returns:
            TimerStop: The stop data
        """
        t = time.perf_counter()
        elapsed_total = t - self.start
        since_last = t - self.stops[-1].at if self.stops else 0
        if not self.ms:
            elapsed_total = round(elapsed_total)
            since_last = round(since_last)

        elapsed_total = timedelta(seconds=elapsed_total)
        since_last = timedelta(seconds=since_last)

        timer_stop = TimerStop(
            total=elapsed_total,
            since_last=since_last,
            at=t,
            label=label,
        )
        self.stops.append(timer_stop)
        return timer_stop

    def taken_seconds(self, r: int | None = None) -> float:
        """Returns the total time taken by the timer in seconds."""
        return self.stop().total_seconds(r=r)

    def taken(self) -> timedelta:
        """Returns the total time taken by the timer as timedelta."""
        return self.stop().total

    def reset(self) -> None:
        """Reset the timer."""
        self.start = time.perf_counter()
        self.stops: list[TimerStop] = [
            TimerStop(
                total=timedelta(seconds=0),
                since_last=timedelta(seconds=0),
                at=self.start,
                label="start",
            )
        ]


def datetime_fmt(
    d: str | float | int | None | datetime = None,
    fmt: str = "Ymd",
    dsep: str = "-",
    tsep: str = ":",
    *,
    ms: bool = False,
    utc: bool = True,
) -> str:
    """
    Format date and time

    Args:
        d (str | float | None | datetime, optional): Input datetime. Defaults to current date and time.
        fmt (str, optional): Date format.
        dsep (str, optional): Date values separator.
        tsep (str, optional): Time values separator.
        ms (bool, optional): include milliseconds.
        utc (bool, optional):  Use the UTC timezone when building a datetime object from a timestamp.

    Raises:
        TypeError: Raises TypeError if the type of ``d`` is not one of the following: float, str, None, datetime, int

    Returns:
        str: Formatted date and time.

    Example:
        ```python
        >>> fmt_datetime()
        '2022-11-22 22:40:04' # current date and time
        >>> fmt_datetime(0)
        "1970-01-01 00:00:00"
        >>> fmt_datetime(0, fmt="dmY", dsep="/")
        "01/01/1970 00:00:00"
        ```
    """
    if d is None:
        d = datetime.fromtimestamp(time.time(), **{"tz": timezone.utc} if utc else {})

    elif isinstance(d, str):
        d = parse_datetime_str(d)
    elif isinstance(d, (float, int)):
        d = datetime.fromtimestamp(d, **{"tz": timezone.utc} if utc else {})
    elif isinstance(d, datetime):
        pass
    else:
        raise TypeError(type(d))
    date_fmt = f"%{fmt[0]}{dsep}%{fmt[1]}{dsep}%{fmt[2]}"
    time_fmt = f"%H{tsep}%M{tsep}%S"
    if ms:
        time_fmt += ".%f"
    dt_str = d.strftime(f"{date_fmt} {time_fmt}")
    return dt_str[:-3] if ms else dt_str


def time_fmt(
    t: float | datetime | int | None = None, sep: str = ":", *, ms: bool = False, utc: bool = True
) -> str:
    """
    Format time

    Args:
        t (float | datetime | int | None, optional): Input time. Defaults to current time.
        sep (str, optional): Character(s) that separates hours, minutes, seconds...
        ms (bool, optional): include milliseconds.
        utc (bool, optional): Use the UTC timezone when building a time object from a timestamp.

    Raises:
        TypeError: Raises TypeError if the type of ``t`` is not one of the following: float, None, datetime, int

    Returns:
        str: Formatted time.
    """
    if t is None:
        tm = datetime.fromtimestamp(time.time(), **{"tz": timezone.utc} if utc else {})
    elif isinstance(t, datetime):
        tm = t.time()
    elif isinstance(t, (int, float)):
        tm = datetime.fromtimestamp(t, **{"tz": timezone.utc} if utc else {})
    else:
        raise TypeError(type(t))
    ts = tm.strftime(f"%H{sep}%M{sep}%S")
    if ms:
        ms_str = f"{int(tm.microsecond / 1000)}".zfill(3)
        ts = f"{ts}.{ms_str}"
    return ts


def date_fmt(
    d: float | date | datetime | int | None = None,
    fmt: str = "Ymd",
    sep: str = "-",
) -> str:
    """
    Format date

    Args:
        d (float | date | datetime | int | None ): Input date. Defaults to current date.
        fmt (str, optional): Date format.
        sep (str, optional): Character(s) that separates days, months and years.

    Raises:
        TypeError: Raises TypeError if the type of ``d`` is not one of the following: float, None, date, datetime, int

    Returns:
        str: Formatted date.

    Example:
        ```python
        >>> fmt_date(date(2022,11,22))
        '2022-11-22'
        >>> fmt_date(date(2022,11,22), sep="/")
        '2022/11/22'
        >>> fmt_date(date(2022,11,22), sep="/", fmt="dmY")
        '22/11/2022'
        >>> fmt_date()
        '2022-11-22'
        ```
    """
    if d is None:
        d = date.fromtimestamp(time.time())
    elif isinstance(d, (float, int)):
        d = date.fromtimestamp(d)
    elif isinstance(d, datetime):
        d = d.date()
    elif isinstance(d, date):
        pass
    else:
        raise TypeError(type(d))
    return d.strftime(f"%{fmt[0]}{sep}%{fmt[1]}{sep}%{fmt[2]}")


def date_range(start: date, end: date) -> Generator[date, None, None]:
    """
    Returns a generator for dates between ``start`` and ``end``

    Example:
        ```python
        >>> for i in date_range(date(2022,11,19), date(2022,11,22)): print(i)
        2022-11-19
        2022-11-20
        2022-11-21
        ```
    """
    for n in range(int((end - start).days)):
        yield start + timedelta(n)


def datetime_range(
    start: datetime,
    end: datetime,
    step: timedelta,
) -> Generator[datetime, None, None]:
    """
    Returns a generator for datetimes between ``start`` and ``end`` with a given ``step``.

    Example:
        ```python
        >>> for dt in datetime_range(
        ...     datetime(2026, 1, 27, 0, 0),
        ...     datetime(2026, 1, 27, 3, 0),
        ...     timedelta(hours=1)
        ... ):
        ...     print(dt)
        2026-01-27 00:00:00
        2026-01-27 01:00:00
        2026-01-27 02:00:00
        ```
    """
    current = start
    if step.total_seconds() == 0:
        raise ValueError("step cannot be zero")
    if step.total_seconds() > 0:
        while current < end:
            yield current
            current += step
    else:
        while current > end:
            yield current
            current += step


def sleep(lo: float, hi: float | None = None) -> float:
    """
    Sleeps for a random duration within a specified range.

    Args:
        lo (float): The lower bound of the sleep duration range (inclusive).
        hi (float, optional): The upper bound of the sleep duration range (inclusive). If not provided, the function will sleep for the exact duration specified by `lo`.

    Returns:
        float: The actual sleep duration.

    Raises:
        ValueError: If `hi` is provided and `lo` is greater than `hi`.
    """
    if hi is None:
        time.sleep(lo)
        return lo
    if lo < hi:
        raise ValueError(f"Minimum sleep time is higher that maximum. {(lo, hi)}")
    t = random.uniform(lo, hi)
    time.sleep(t)
    return t


def seconds_to_hms(time: int | float, ms: bool = False) -> str:
    """
    Converts time in seconds to a string in the format HH:MM:SS[.mmm]

    Example:
        >>> seconds_to_hms(123.456)
        '00:02:03'
        >>> seconds_to_hms(123.456, ms=True)
        '00:02:03.456'
        >>> seconds_to_hms(-123.456, ms=True)
        '-00:02:03.456'
    """
    sign = "-" if time < 0 else ""
    time = abs(time)

    s = int(time % 60)
    m = int((time // 60) % 60)
    h = int(time // 3600)
    time_str = f"{sign}{h:02d}:{m:02d}:{s:02d}"

    if ms:
        milis = int(round((time - int(time)) * 1000))
        time_str += f".{milis:03d}"
    return time_str


def hms_to_seconds(time: str, ms: bool = False) -> float | None:
    """
    Converts a string in the format HH:MM:SS[.mmm] or h:m:s or m:s to time in seconds.

    Example:
        >>> hms_to_seconds('00:02:03')
        123.0
        >>> hms_to_seconds('00:02:03.456', ms=True)
        123.456
    """
    if time is None:
        return None

    negative = False
    time = time.strip()
    if time.startswith("-"):
        negative = True
        time = time[1:]

    parts = time.split(":")
    if len(parts) == 1:
        return float(parts[0])
    time_milis = 0.0

    if ms:
        if "." in parts[-1]:
            dot_split = parts[-1].split(".", 1)
            parts[-1], millis_str = dot_split
            if not millis_str.isdigit():
                raise ValueError(f"Invalid milliseconds in time: '{time}'")
            millis = int(millis_str.ljust(3, "0"))
            time_milis = millis / 1000

    if len(parts) not in (2, 3):
        raise ValueError("Invalid number of time segments.")

    if len(parts) == 2:
        minute_part, second_part = parts
        m = int(minute_part)
        s = int(second_part)
        if s >= 60:
            raise ValueError(f"Seconds ({s}) must be < 60.")
        total = m * 60 + s
    else:
        hour_part, minute_part, second_part = parts
        h = int(hour_part)
        m = int(minute_part)
        s = int(second_part)
        if m >= 60 or s >= 60:
            raise ValueError(f"Minutes ({m}) or seconds ({s}) must be < 60.")
        total = h * 3600 + m * 60 + s

    result = total + time_milis
    return -result if negative else result


__all__ = [
    "Timer",
    "parse_datetime_str",
    "datetime_fmt",
    "time_fmt",
    "date_fmt",
    "date_range",
    "datetime_range",
    "sleep",
    "local_timezone",
    "timezone",
    "date",
    "datetime",
    "time",
]
