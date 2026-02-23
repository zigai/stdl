import pytest

from stdl.lst import chunks, split


def test_chunks():
    values = list(range(1, 11))
    assert chunks(values, size=3) == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
    assert chunks(values, size=len(values)) == [values]
    assert chunks(values, size=1) == [[i] for i in values]

    invalid_size = len(values) + 1
    with pytest.raises(ValueError, match=rf"^{invalid_size}$"):
        chunks(values, size=invalid_size)


def test_split_with_valid_input():
    values = [1, 2, 3, 4, 5]
    assert split(values, 3) == [[1], [2, 3], [4, 5]]


def test_split_with_invalid_input():
    values = [1, 2, 3]
    with pytest.raises(ValueError, match=r"^4$"):
        split(values, 4)
    with pytest.raises(ValueError, match=r"^0$"):
        split(values, 0)
