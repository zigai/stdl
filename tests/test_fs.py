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


def test_bytes_readable():
    assert fs.bytes_readable(0) == "0B"
    assert fs.bytes_readable(512) == "512.0 B"
    assert fs.bytes_readable(1024) == "1.0 KB"
    assert fs.bytes_readable(1048576) == "1.0 MB"
    assert fs.bytes_readable(1073741824) == "1.0 GB"
    assert fs.bytes_readable(1500) == "1.46 KB"

    with pytest.raises(ValueError):
        fs.bytes_readable(-1)


def test_readable_size_to_bytes():
    assert fs.readable_size_to_bytes("512B") == 512
    assert fs.readable_size_to_bytes("1KB") == 1024
    assert fs.readable_size_to_bytes("1MB") == 1048576
    assert fs.readable_size_to_bytes("1GB") == 1073741824
    assert fs.readable_size_to_bytes("1.5KB") == 1536
    assert fs.readable_size_to_bytes("1kb") == 1024
    assert fs.readable_size_to_bytes("1 KB") == 1024
    assert fs.readable_size_to_bytes("1KB", kb_size=1000) == 1000

    with pytest.raises(ValueError):
        fs.readable_size_to_bytes("1XB")
    with pytest.raises(ValueError):
        fs.readable_size_to_bytes("-1KB")
    with pytest.raises(ValueError):
        fs.readable_size_to_bytes("1KB", kb_size=1023)
