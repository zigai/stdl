from stdl.dt import *


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
