from dataclasses import asdict, astuple, dataclass
from pprint import pprint


class Data:
    def __init__(self) -> None:
        pass

    @property
    def dict(self) -> dict:
        return asdict(self)

    @property
    def tuple(self) -> tuple:
        return astuple(self)

    def print(self):
        pprint(self.dict)

    def __getitem__(self, key):
        return self.dict[key]

    def __iter__(self):
        for i in self.tuple:
            yield i


__all__ = ["Data", "dataclass"]
