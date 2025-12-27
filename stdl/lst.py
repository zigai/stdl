from collections import Counter
from collections.abc import Sequence
from typing import Any, TypeVar

T = TypeVar("T")


def chunks(l: list[T], size: int) -> list[list[T]]:
    """
    Splits a list into chunks of a specified size.

    Args:
        l (list[T]): list to be split
        size (int): Size of each chunk.

    Returns:
        list[list[T]] : a list containing the chunks.

    Raises:
        ValueError : if the size is less than 1 or greater than the length of the list
    """
    if size < 1 or size > len(l):
        raise ValueError(size)
    return [l[i : i + size] for i in range(0, len(l), size)]


def split(l: list[T], parts: int) -> list[list[T]]:
    """
    Splits a list into a specified number of parts

    Args:
        l (list[T]): List to be split
        parts (int): Number of parts to split the list into.

    Returns:
        list[list[T]] : a list containing the split parts.

    Raises:
        ValueError : if the parts is less than 1 or greater than the length of the list.
    """
    if parts < 1 or parts > len(l):
        raise ValueError(parts)

    def inner(l: list[T], parts: int) -> list[list[T]]:
        length = len(l)
        si = length // parts
        if length - si > 0:
            return [l[:si], *inner(l[si:], parts - 1)]
        else:
            return [l]

    return inner(l, parts)


def unique(l: Sequence[T]) -> list[T]:
    """
    Filter out all non-unique values from a list.

    Args:
        l (Sequence[T]): The list to filter.

    Returns:
        list[T]: A list of only unique values.
    """
    return [i for i, count in Counter(l).items() if count == 1]


def non_unique(l: Sequence[T]) -> list[T]:
    """
    Filter out all unique values from a list.

    Args:
        l (Sequence[T]): The list to filter.

    Returns:
        list[T]: A list of only non-unique values.
    """
    return [i for i, count in Counter(l).items() if count > 1]


def every_nth(l: list[T], n: int) -> list[T]:
    """
    Return every nth element from a list
    Args:
        l (list[T]): The list to extract elements from.
        n (int): The index to extract the element at
    Returns:
        list[T]: A list of every nth element
    """
    return l[n - 1 :: n]


def occurrences(l: Sequence[T], val: Any) -> int:
    """
    Count the number of occurrences of a value in a list
    Args:
        l (Sequence[T]): The list to count values in.
        val (Any): The value to count
    Returns:
        int: Number of occurrences
    """
    return len([i for i in l if i == val and type(i) is type(val)])


def nodups(l: Sequence[T]) -> list[T]:
    """Remove duplicates from a list and maintain the order"""
    result: list[T] = []
    for i in l:
        if i not in result:
            result.append(i)
    return result


def replace_sublists(l: list[Any], sublist: list[Any], replacement: list[Any]) -> list[Any]:
    """
    Replaces all occurrences of sublist `sublist` with `replacement` in `main`.

    Args:
        l: The list in which to search for sublists.
        sublist: The sublist to replace.
        replacement: The sublist to replace `sublist` with.

    Example:
        >>> replace_all_sublist([1, 2, 3, 2, 3], [2, 3], [5])
        [1, 5, 5]
    """
    result = []
    i = 0
    len_old = len(sublist)
    while i <= len(l) - len_old:
        if l[i : i + len_old] == sublist:
            result.extend(replacement)
            i += len_old
        else:
            result.append(l[i])
            i += 1
    result.extend(l[i:])
    return result


def contains_sublist(l: list[Any], sublist: list[Any]) -> bool:
    """
    Checks if list contains a sublist.

    Args:
        l: The list to search.
        sublist: The sublist to search for.

    """
    len_b = len(sublist)
    for i in range(len(l) - len_b + 1):
        if l[i : i + len_b] == sublist:
            return True
    return False


__all__ = [
    "unique",
    "non_unique",
    "every_nth",
    "occurrences",
    "chunks",
    "split",
    "replace_sublists",
    "contains_sublist",
]
