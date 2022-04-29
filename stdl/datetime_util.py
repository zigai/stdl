from datetime import date, datetime, timedelta
from time import time


class Timer:

    def __init__(self, msg: str = "Time:"):
        self.msg = msg
        self.start_time = time()

    def stop(self):
        run_time = timedelta(seconds=round(time() - self.start_time))
        print(f"\n{self.msg} {run_time}")
        return run_time


class Date:

    @staticmethod
    def now():
        """
        YYYY-MM-DD
        2021-03-03
        """
        return date.today()

    @staticmethod
    def yesterday():
        return Date.now() - timedelta(days=1)

    @staticmethod
    def tommorow():
        return Date.now() + timedelta(days=1)

    @staticmethod
    def today_as_str(fmt: str = "dmY", sep: str = "-") -> str:
        return Date.now().strftime(f"%{fmt[0]}{sep}%{fmt[1]}{sep}%{fmt[2]}")

    @staticmethod
    def from_timestamp(t: float):
        return datetime.fromtimestamp(t)

    @staticmethod
    def from_timestamp_as_str(t: float, sep="-"):
        return datetime.fromtimestamp(t).strftime(f'%d{sep}%m{sep}%Y')

    @staticmethod
    def range(start_date: date, end_date: date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)


class DateTime:

    @staticmethod
    def format(d: datetime, fmt: str = "dmY", sep: str = "-"):
        return d.strftime(f"%{fmt[0]}{sep}%{fmt[1]}{sep}%{fmt[2]}")

    @staticmethod
    def from_timestamp(t: float):
        return datetime.fromtimestamp(t)

    @staticmethod
    def from_timestamp_as_str(t: float, date_sep: str = "/", time_sep: str = ":"):
        return DateTime.from_timestamp(t).strftime(
            f'%d{date_sep}%m{date_sep}%Y, %H{time_sep}%M{time_sep}%S')


class Time:

    @staticmethod
    def now_str(sep: str = ":", ms: bool = False):
        t = datetime.now()
        if ms:
            return f"{t.strftime(f'%H{sep}%M{sep}%S')}.{int(t.microsecond / 1000)}"
        return t.strftime(f'%H{sep}%M{sep}%S')

    @staticmethod
    def from_timestamp(t: float):
        return datetime.fromtimestamp(t)

    @staticmethod
    def from_timestamp_as_str(t: float, sep=":"):
        return Time.from_timestamp(t).strftime(f'%H{sep}%M{sep}%S')


if __name__ == '__main__':
    timer = Timer()
    print(Date.today_as_str())
    print(Time.now_str(sep=".", ms=False))
    print(Time.now_str(sep=":", ms=True))
    print(Time.from_timestamp_as_str(time()))
    print(Date.from_timestamp_as_str(time()))
    print(DateTime.from_timestamp_as_str(time()))
    timer.stop()
