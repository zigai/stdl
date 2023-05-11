import json
from copy import deepcopy
from dataclasses import asdict, astuple, dataclass
from pprint import pprint
from typing import Any, Mapping

from stdl.fs import Pathlike, json_load


class Data:
    def __init__(self) -> None:
        pass

    def __getitem__(self, key):
        return self.dict()[key]

    def __iter__(self):
        for i in self.tuple():
            yield i

    def dict(self) -> dict:
        return asdict(self)  # type:ignore

    def tuple(self) -> tuple:
        return astuple(self)  # type:ignore

    def json(self):
        return json.dumps(self.dict())

    def copy(self):
        return deepcopy(self)

    @classmethod
    def parse_obj(cls, obj: Mapping[str, Any]):
        return cls(**obj)

    def parse_file(self, filepath: Pathlike):
        return self.parse_obj(json_load(filepath))  # type:ignore

    def print(self):
        pprint(self.dict)


__all__ = ["Data", "dataclass"]
