from stdl.dt import *


def test_fmt_time():
    assert fmt_time(0) == "00:00:00"
    assert fmt_time(0, ms=True) == "00:00:00.000"
    assert fmt_time(1, ms=True) == "00:00:01.000"


def test_fmt_datetime():
    assert fmt_datetime(0.0, utc=True) == "1970-01-01 00:00:00"
    assert fmt_datetime(0) == "1970-01-01 00:00:00"
    assert fmt_datetime(0, fmt="dmY") == "01-01-1970 00:00:00"
    assert fmt_datetime(0, fmt="dmY", dsep="/") == "01/01/1970 00:00:00"
    assert fmt_datetime(0, fmt="dmY", dsep="/", tsep=".") == "01/01/1970 00.00.00"
    # assert fmt_datetime(0.0, utc=False) == "1970-01-01 01:00:00"


def test_fmt_date():
    assert fmt_date(date(1970, 1, 1)) == "1970-01-01"
    assert fmt_date(0) == "1970-01-01"
