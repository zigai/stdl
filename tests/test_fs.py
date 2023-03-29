import tempfile
from pathlib import Path

import pytest

from stdl import fs


def test_yield_files_in_without_ext():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        filenames = ["file1.txt", "file2.txt", "file3.txt"]
        files = [temp_dir_path / i for i in filenames]
        [i.touch() for i in files]
        files_found = fs.get_files_in(temp_dir)
    assert set(files_found) == set([str(i) for i in files])


def test_yield_files_in_with_ext():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        filenames = ["file1.txt", "file2.txt", "file3.csv"]
        files = [temp_dir_path / i for i in filenames]
        [i.touch() for i in files]
        files_found = fs.get_files_in(temp_dir, ext="csv")
    assert set(files_found) == {str(files[-1])}


def test_yield_files_in_with_tuple_ext():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        filenames = ["file1.txt", "file2.txt", "file3.csv", "file4.py"]
        files = [temp_dir_path / i for i in filenames]
        [i.touch() for i in files]
        files_found = fs.get_files_in(temp_dir, ext=("py", "csv"))
    assert set(files_found) == {str(files[-1]), str(files[-2])}


def test_yield_files_in_with_recursive():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        filenames = ["file1.txt", "file2.txt", "file3.txt"]
        files = [temp_dir_path / i for i in filenames]
        sub_dir = temp_dir_path / "sub_dir"
        sub_dir.mkdir()
        [i.touch() for i in files]
        sub_file = sub_dir / "sub_file1.txt"
        sub_file.touch()
        files = [temp_dir_path / i for i in filenames]
        files_found = fs.get_files_in(temp_dir, recursive=False)

    assert set(files_found) == set([str(i) for i in files])
