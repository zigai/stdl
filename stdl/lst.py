from collections import Counter
from collections.abc import Sequence
from typing import Any, TypeVar

T = TypeVar("T")


def chunks(items: list[T], size: int) -> list[list[T]]:
    """
    Splits a list into chunks of a specified size.

    Args:
        items (list[T]): list to be split
        size (int): Size of each chunk.

    Returns:
        list[list[T]] : a list containing the chunks.

    Raises:
        ValueError : if the size is less than 1 or greater than the length of the list
    """
    if size < 1 or size > len(items):
        raise ValueError(size)
    return [items[i : i + size] for i in range(0, len(items), size)]


def split(items: list[T], parts: int) -> list[list[T]]:
    """
    Splits a list into a specified number of parts.

    Args:
        items (list[T]): List to be split
        parts (int): Number of parts to split the list into.

    Returns:
        list[list[T]] : a list containing the split parts.

    Raises:
        ValueError : if the parts is less than 1 or greater than the length of the list.
    """
    if parts < 1 or parts > len(items):
        raise ValueError(parts)

    def inner(remaining: list[T], remaining_parts: int) -> list[list[T]]:
        length = len(remaining)
        split_index = length // remaining_parts
        if length - split_index > 0:
            return [remaining[:split_index], *inner(remaining[split_index:], remaining_parts - 1)]
        return [remaining]

    return inner(items, parts)


def unique(items: Sequence[T]) -> list[T]:
    """
    Filter out all non-unique values from a list.

    Args:
        items (Sequence[T]): The list to filter.

    Returns:
        list[T]: A list of only unique values.
    """
    return [i for i, count in Counter(items).items() if count == 1]


def non_unique(items: Sequence[T]) -> list[T]:
    """
    Filter out all unique values from a list.

    Args:
        items (Sequence[T]): The list to filter.

    Returns:
        list[T]: A list of only non-unique values.
    """
    return [i for i, count in Counter(items).items() if count > 1]


def every_nth(items: list[T], n: int) -> list[T]:
    """
    Return every nth element from a list.

    Args:
        items (list[T]): The list to extract elements from.
        n (int): The index to extract the element at.

    Returns:
        list[T]: A list of every nth element.
    """
    return items[n - 1 :: n]


def occurrences(items: Sequence[T], val: object) -> int:
    """
    Count the number of occurrences of a value in a list.

    Args:
        items (Sequence[T]): The list to count values in.
        val (object): The value to count.

    Returns:
        int: Number of occurrences.
    """
    return len([i for i in items if i == val and type(i) is type(val)])


def nodups(items: Sequence[T]) -> list[T]:
    """Remove duplicates from a list and maintain the order."""
    result: list[T] = []
    for i in items:
        if i not in result:
            result.append(i)
    return result


def replace_sublists(items: list[Any], sublist: list[Any], replacement: list[Any]) -> list[Any]:
    """
    Replaces all occurrences of sublist `sublist` with `replacement` in `main`.

    Args:
        items: The list in which to search for sublists.
        sublist: The sublist to replace.
        replacement: The sublist to replace `sublist` with.

    Example:
        >>> replace_all_sublist([1, 2, 3, 2, 3], [2, 3], [5])
        [1, 5, 5]
    """
    result = []
    i = 0
    len_old = len(sublist)
    while i <= len(items) - len_old:
        if items[i : i + len_old] == sublist:
            result.extend(replacement)
            i += len_old
        else:
            result.append(items[i])
            i += 1
    result.extend(items[i:])
    return result


def contains_sublist(items: list[Any], sublist: list[Any]) -> bool:
    """
    Checks if list contains a sublist.

    Args:
        items: The list to search.
        sublist: The sublist to search for.

    """
    len_b = len(sublist)
    return any(items[i : i + len_b] == sublist for i in range(len(items) - len_b + 1))


__all__ = [
    "chunks",
    "contains_sublist",
    "every_nth",
    "non_unique",
    "occurrences",
    "replace_sublists",
    "split",
    "unique",
]
