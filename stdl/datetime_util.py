import time
from datetime import date, datetime, timedelta

from dateutil import parser


class Timer:

    def __init__(self, miliseconds: bool = True):
        self.start = time.time()
        self.miliseconds = miliseconds
        self.stops = []

    def stop(self, label: str | None = None):
        diff = time.time() - self.start
        if not self.miliseconds:
            diff = round(diff)
        self.stops.append((diff, label))
        return timedelta(seconds=diff)


def parse_datetime(date: str):
    return parser.parse(date)


def fmt_datetime(
    d: str | float | None | datetime = None,
    fmt: str = "Ymd",
    d_sep: str = "-",
    t_sep: str = ":",
):
    if d is None:
        d = datetime.fromtimestamp(time.time())
    elif isinstance(d, str):
        d = parse_datetime(d)
    elif isinstance(d, float):
        d = datetime.fromtimestamp(d)
    elif isinstance(d, datetime):
        pass
    else:
        raise TypeError(type(d))
    d_fmt = f"%{fmt[0]}{d_sep}%{fmt[1]}{d_sep}%{fmt[2]}"
    t_fmt = f"%H{t_sep}%M{t_sep}%S"
    return d.strftime(f"{d_fmt} {t_fmt}")


def fmt_time(t: float | None = None, sep: str = ":", ms: bool = False):
    if t is None:
        t = time.time()
    tm = datetime.fromtimestamp(t)
    ts = tm.strftime(f'%H{sep}%M{sep}%S')
    if ms:
        ts = f"{ts}.{int(tm.microsecond / 1000)}"
    return ts


def fmt_date(
    d: float | None | date = None,
    fmt: str = "Ymd",
    sep: str = "-",
):
    if d is None:
        d = date.fromtimestamp(time.time())
    elif isinstance(d, float):
        d = date.fromtimestamp(d)
    elif isinstance(d, date):
        pass
    else:
        raise TypeError(type(d))
    return d.strftime(f"%{fmt[0]}{sep}%{fmt[1]}{sep}%{fmt[2]}")


def date_range(start: date, end: date):
    for n in range(int((end - start).days)):
        yield start + timedelta(n)


if __name__ == '__main__':
    timer = Timer()
    print(fmt_date())
    print(fmt_datetime())
    print(fmt_time())
    print(timer.stop())
