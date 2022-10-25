import math
from collections import Counter


def get_unique(l: list) -> list:
    return [item for item, count in Counter(l).items() if count == 1]


def get_non_unique(l: list) -> list:
    return [item for item, count in Counter(l).items() if count > 1]


def get_every_nth(l: list, n: int) -> list:
    return l[n - 1 :: n]


def count_occurrences(value, l: list) -> int:
    return len([x for x in l if x == value and type(x) == type(value)])


def chunks(l: list, chunk_size: int):
    return [l[i : i + chunk_size] for i in range(0, len(l), chunk_size)]


def split(l: list, n: int):
    chunk_size = math.ceil(len(l) / n)
    return chunks(l, chunk_size)


__all__ = [
    "get_unique",
    "get_non_unique",
    "get_every_nth",
    "count_occurrences",
    "chunks",
    "split",
]
