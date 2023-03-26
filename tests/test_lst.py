import pytest

from stdl.lst import *


def test_chunks():
    l = list(range(1, 11))
    assert chunks(l, size=3) == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
    assert chunks(l, size=len(l)) == [l]
    assert chunks(l, size=1) == [[i] for i in l]
    with pytest.raises(ValueError):
        chunks(l, size=len(l) + 1)


def test_split_with_valid_input():
    l = [1, 2, 3, 4, 5]
    assert split(l, 3) == [[1], [2, 3], [4, 5]]


def test_split_with_invalid_input():
    l = [1, 2, 3]
    with pytest.raises(ValueError):
        split(l, 4)
    with pytest.raises(ValueError):
        split(l, 0)
