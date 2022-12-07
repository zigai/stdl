import random
from collections import Counter
from copy import deepcopy
from typing import Any


def chunks(l: list[Any], size: int, *, rand: bool = False) -> list[list[Any]]:
    if size < 1 or size > len(l):
        raise ValueError(size)
    if rand:
        l = deepcopy(l)
        random.shuffle(l)
    return [l[i : i + size] for i in range(0, len(l), size)]


def split(l: list[Any], parts: int, *, rand: bool = False) -> list[list[Any]]:
    if parts < 1 or parts > len(l):
        raise ValueError(parts)
    if rand:
        l = deepcopy(l)
        random.shuffle(l)

    def inner(l: list[Any], parts: int) -> list[list[Any]]:
        length = len(l)
        si = length // parts
        if length - si > 0:
            return [l[:si]] + inner(l[si:], parts - 1)
        else:
            return [l]

    return inner(l, parts)


def get_unique(l: list[Any]) -> list[Any]:
    # The code inside this function is from a modified snippet from
    # https://www.30secondsofcode.org/python and is licensed under
    # CC-BY-4.0 License (https://creativecommons.org/licenses/by/4.0/)
    return [item for item, count in Counter(l).items() if count == 1]


def get_non_unique(l: list[Any]) -> list[Any]:
    # The code inside this function is from a modified snippet from
    # https://www.30secondsofcode.org/python and is licensed under
    # CC-BY-4.0 License (https://creativecommons.org/licenses/by/4.0/)
    return [item for item, count in Counter(l).items() if count > 1]


def get_every_nth(l: list[Any], n: int) -> list[Any]:
    # The code inside this function is from a modified snippet from
    # https://www.30secondsofcode.org/python and is licensed under
    # CC-BY-4.0 License (https://creativecommons.org/licenses/by/4.0/)
    return l[n - 1 :: n]


def count_occurrences(l: list[Any], val: Any) -> int:
    # The code inside this function is from a modified snippet from
    # https://www.30secondsofcode.org/python and is licensed under
    # CC-BY-4.0 License (https://creativecommons.org/licenses/by/4.0/)
    return len([x for x in l if x == val and type(x) == type(val)])


__all__ = [
    "get_unique",
    "get_non_unique",
    "get_every_nth",
    "count_occurrences",
    "chunks",
    "split",
]
