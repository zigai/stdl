from datetime import date, datetime, timedelta
from time import time


class Timer:

    def __init__(self):
        self.start_time = time()

    def stop(self, msg: str = "Time:"):
        run_time = timedelta(seconds=round(time() - self.start_time))
        print(f"{msg} {run_time}")
        return run_time


class Date:

    @staticmethod
    def now() -> date:
        """
        YYYY-MM-DD
        2021-03-03
        """
        return date.today()

    @staticmethod
    def yesterday() -> date:
        return Date.now() - timedelta(days=1)

    @staticmethod
    def tommorow() -> date:
        return Date.now() + timedelta(days=1)

    @staticmethod
    def from_ts(t: float) -> date:
        return date.fromtimestamp(t)

    @staticmethod
    def range(start_date: date, end_date: date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    @staticmethod
    def format(d: date, fmt: str = "Ymd", sep: str = "-") -> str:
        return d.strftime(f"%{fmt[0]}{sep}%{fmt[1]}{sep}%{fmt[2]}")

    @staticmethod
    def today_as_str(fmt: str = "Ymd", sep: str = "-") -> str:
        return Date.format(Date.now(), fmt=fmt, sep=sep)

    @staticmethod
    def from_ts_as_str(t: float, fmt: str = "Ymd", sep="-") -> str:
        return Date.format(Date.from_ts(t), fmt=fmt, sep=sep)


class DateTime:

    @staticmethod
    def now() -> datetime:
        return datetime.now()

    @staticmethod
    def from_ts(t: float) -> datetime:
        return datetime.fromtimestamp(t)

    @staticmethod
    def format(d: datetime, fmt: str = "Ymd", date_sep: str = ".", time_sep: str = ":") -> str:
        return d.strftime(
            f"%{fmt[0]}{date_sep}%{fmt[1]}{date_sep}%{fmt[2]} %H{time_sep}%M{time_sep}%S")

    @staticmethod
    def from_ts_as_str(t: float, fmt: str = "Ymd", date_sep: str = ".", time_sep: str = ":") -> str:
        return DateTime.format(DateTime.from_ts(t), fmt=fmt, date_sep=date_sep, time_sep=time_sep)


class Time:

    @staticmethod
    def now() -> float:
        return time()

    @staticmethod
    def format(t: float, sep: str = ":", ms: bool = False) -> str:
        tm = datetime.fromtimestamp(t)
        ts = tm.strftime(f'%H{sep}%M{sep}%S')
        if ms:
            ts = f"{ts}.{int(tm.microsecond / 1000)}"
        return ts

    @staticmethod
    def now_as_str(sep: str = ":", ms: bool = False) -> str:
        return Time.format(Time.now(), sep=sep, ms=ms)


if __name__ == '__main__':
    timer = Timer()
    print("\nTime")
    print(Time.now_as_str())
    print(Time.now_as_str(sep=".", ms=False))
    print(Time.now_as_str(sep=":", ms=True))
    print(Time.format(time()))

    print("\nDate")
    print(Date.today_as_str())
    print(Date.from_ts_as_str(time(), sep="/"))
    print(Date.from_ts(time()))

    print("\nDateTime")
    print(DateTime.from_ts(time()))
    print(DateTime.now())
    print(DateTime.format(DateTime.now()))
    timer.stop(msg="Timer:")
