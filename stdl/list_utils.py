from collections import Counter


def get_unique(l: list) -> list:
    return [item for item, count in Counter(l).items() if count == 1]


def get_non_unique(l: list) -> list:
    return [item for item, count in Counter(l).items() if count > 1]


def get_every_nth(l: list, n: int) -> list:
    return l[n - 1::n]


def count_occurrences(value, l: list) -> int:
    return len([x for x in l if x == value and type(x) == type(value)])
