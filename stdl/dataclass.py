from dataclasses import asdict, astuple, dataclass
from pprint import pprint
from typing import Any, Mapping

from stdl.fs import Pathlike, json_dump


class Data:
    def __init__(self) -> None:
        pass

    @property
    def dict(self) -> dict:
        return asdict(self)  # type:ignore

    @property
    def tuple(self) -> tuple:
        return astuple(self)  # type:ignore

    def print(self):
        pprint(self.dict)

    def __getitem__(self, key):
        return self.dict[key]

    def __iter__(self):
        for i in self.tuple:
            yield i

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]):
        return cls(**d)

    def json_dump(self, filepath: Pathlike, endcoding="utf-8", indent=4):
        json_dump(self.dict, filepath, endcoding, indent=indent)


__all__ = ["Data", "dataclass"]
