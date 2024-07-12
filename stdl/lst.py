import typing as T
from collections import Counter


def chunks(l: list[T.Any], size: int) -> list[list[T.Any]]:
    """
    Splits a list into chunks of a specified size.

    Args:
        l (list): list to be split
        size (int): Size of each chunk.

    Returns:
        list : a list containing the chunks.

    Raises:
        ValueError : if the size is less than 1 or greater than the length of the list
    """
    if size < 1 or size > len(l):
        raise ValueError(size)
    return [l[i : i + size] for i in range(0, len(l), size)]


def split(l: list[T.Any], parts: int) -> list[list[T.Any]]:
    """
    Splits a list into a specified number of parts

    Args:
        l (list): List to be split
        parts (int): Number of parts to split the list into.

    Returns:
        list : a list containing the split parts.

    Raises:
        ValueError : if the parts is less than 1 or greater than the length of the list.
    """
    if parts < 1 or parts > len(l):
        raise ValueError(parts)

    def inner(l: list[T.Any], parts: int) -> list[list[T.Any]]:
        length = len(l)
        si = length // parts
        if length - si > 0:
            return [l[:si]] + inner(l[si:], parts - 1)
        else:
            return [l]

    return inner(l, parts)


def unique(l: list[T.Any]) -> list[T.Any]:
    """
    Filter out all non-unique values from a list.
    Args:
        l (List[Any]): The list to filter.
    Returns:
        List[Any]: A list of only unique values.
    """
    return [i for i, count in Counter(l).items() if count == 1]


def non_unique(l: list[T.Any]) -> list[T.Any]:
    """
    Filter out all unique values from a list.
    Args:
        l (List[Any]): The list to filter.
    Returns:
        List[Any]: A list of only non-unique values.
    """
    return [i for i, count in Counter(l).items() if count > 1]


def every_nth(l: list[T.Any], n: int) -> list[T.Any]:
    """
    Return every nth element from a list
    Args:
        l (List[Any]): The list to extract elements from.
        n (int): The index to extract the element at
    Returns:
        List[Any]: A list of every nth element
    """
    return l[n - 1 :: n]


def occurrences(l: list[T.Any], val: T.Any) -> int:
    """
    Count the number of occurrences of a value in a list
    Args:
        l (List[Any]): The list to count values in.
        val (Any): The value to count
    Returns:
        int: Number of occurrences
    """
    return len([i for i in l if i == val and type(i) == type(val)])


__all__ = [
    "unique",
    "non_unique",
    "every_nth",
    "occurrences",
    "chunks",
    "split",
]
