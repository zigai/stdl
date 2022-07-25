from __future__ import annotations

import json
import math
import os
import pickle
import platform
import random
import shutil
import sys
import time
from collections.abc import Iterable
from pathlib import Path

import yaml

from stdl.str_util import FilterStr


class File:

    def __init__(self, path: str | Path, encoding="utf-8") -> None:
        self.path = path
        self.encoding = encoding
        if isinstance(path, Path):
            self.path = str(path)

    def __str__(self):
        return self.path

    @property
    def exists(self):
        return os.path.isfile(self.path)

    @property
    def dirname(self):
        return os.path.dirname(self.path)

    @property
    def basename(self):
        return os.path.basename(self.path)

    @property
    def ext(self):
        if "." in self.basename:
            return self.basename.split(".")[-1]
        return None

    @property
    def created(self):
        return os.path.getctime(self.path)

    @property
    def modified(self):
        return os.path.getmtime(self.path)

    @property
    def abspath(self):
        return os.path.abspath(self.path)

    def size(self, readable: bool = False) -> int | str:
        size = os.path.getsize(self.path)
        if readable:
            return bytes_readable(size)
        return size

    def to_path(self) -> Path:
        return Path(self.path)

    def read(self) -> str:
        with open(self.path, "r", encoding=self.encoding) as f:
            return f.read()

    def write(self, data, add_newline: bool = True):
        with open(self.path, "w", encoding=self.encoding) as f:
            f.write(data)
            if add_newline:
                f.write("\n")

    def write_iter(self, data: Iterable, sep="\n", add_newline: bool = True):
        with open(self.path, 'w', encoding=self.encoding) as f:
            for entry in data:
                f.write(f"{entry}{sep}")
            if add_newline:
                f.write("\n")

    def append(self, data, add_newline: bool = True):
        with open(self.path, "a", encoding=self.encoding) as f:
            f.write(data)
            if add_newline:
                f.write("\n")

    def append_iter(self, data: Iterable, sep="\n", add_newline: bool = True):
        with open(self.path, "a", encoding=self.encoding) as f:
            for entry in data:
                f.write(f"{entry}{sep}")
            if add_newline:
                f.write("\n")

    def readlines(self) -> list[str]:
        with open(self.path, "r", encoding=self.encoding) as f:
            return f.readlines()

    def splitlines(self):
        return self.read().splitlines()

    def move_to(self, directory: str):
        move_path = f"{directory}{os.sep}{os.path.basename(self.path)}"
        os.rename(self.path, move_path)
        self.path = move_path
        return self

    def copy_to(self, directory, mkdir=False):
        if not os.path.isdir(directory):
            if mkdir:
                os.mkdir(directory)
            else:
                raise FileNotFoundError(f"No such directory: '{directory}'")
        self.path = shutil.copy2(self.path, directory)
        return self

    def get_xattr(self, name: str, group="user"):
        return os.getxattr(self.path, f'{group}.{name}').decode()

    def set_xattr(self, value: str | bytes, name: str, group="user"):
        if isinstance(value, str):
            value = value.encode()
        os.setxattr(self.path, f'{group}.{name}', value)


def pickle_load(filepath: str | Path):
    with open(filepath, "rb") as f:
        return pickle.load(f)


def pickle_dump(data, filepath: str | Path):
    with open(filepath, "wb") as f:
        pickle.dump(data, f)


def json_load(path: str | Path, encoding="utf-8") -> dict | list[dict]:
    with open(path, "r", encoding=encoding) as f:
        return json.load(f)


def yaml_load(path: str | Path, encoding="utf-8") -> dict | list[dict]:
    with open(path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)


def json_dump(data, path: str | Path, encoding="utf-8", default=str, indent=4):
    with open(path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=indent, default=default)


def yaml_dump(data, path: str | Path, encoding="utf-8"):
    with open(path, "w", encoding=encoding) as f:
        yaml.safe_dump(data, f)


def get_dir_size(directory: str | Path, readable: bool = False) -> str | int:
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Skip if it's symbolic link.
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    if readable:
        return bytes_readable(total_size)
    return total_size


def move_files(files: list, directory: str, mkdir: bool = False) -> None:
    if not os.path.exists(directory):
        if mkdir:
            os.mkdir(directory)
        else:
            raise FileNotFoundError(f"{directory} is not a directory")
    for file in files:
        os.rename(file, f"{directory}{os.sep}{os.path.basename(file)}")


def get_random_filename(extension: str = "txt", prefix: str = "file") -> str:
    if extension.startswith("."):
        extension = extension[1:]
    return f"{prefix}.{time.time()}.{random.randrange(1000000, 9999999)}.{extension}"


def bytes_readable(size_bytes: int) -> str:
    if size_bytes < 0:
        raise ValueError(size_bytes)
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def windows_has_drive(letter: str) -> bool:
    if sys.platform != "win32":
        return False
    return os.path.exists(f"{letter}:{os.sep}")


def make_dirs(dest: str, dirs: list):
    if not os.path.exists(dest):
        os.makedirs(dest)
    for i in dirs:
        if not os.path.exists(i):
            os.mkdir(f"{dest}{os.sep}{i}")


def get_files_in(
    directory: str,
    ext: str | tuple[str] | None = None,
    recursive: bool = True,
) -> list[str]:
    files = []
    if not recursive:
        for entry in os.scandir(directory):
            if not entry.is_file():
                continue
            path = os.path.abspath(entry.path)
            if ext is None:
                files.append(path)
            else:
                if entry.path.endswith(ext):
                    files.append(path)
    else:
        if ext is None:
            for entry in os.scandir(directory):
                if entry.is_file():
                    files.append(os.path.abspath(entry.path))
                elif entry.is_dir():
                    files.extend(get_files_in(entry.path, ext=ext, recursive=recursive))
        else:
            for entry in os.scandir(directory):
                if entry.is_file():
                    if entry.path.lower().endswith(ext):
                        files.append(os.path.abspath(entry.path))
                elif entry.is_dir():
                    files.extend(get_files_in(entry.path, ext=ext, recursive=recursive))
    return files


def yield_files_in(directory: str, ext: str | tuple[str] | None = None, recursive: bool = True):
    if not recursive:
        for entry in os.scandir(directory):
            if not entry.is_file():
                continue
            path = os.path.abspath(entry.path)
            if ext is None:
                yield path
            else:
                if entry.path.endswith(ext):
                    yield path
    else:
        if ext is None:
            for entry in os.scandir(directory):
                if entry.is_file():
                    yield os.path.abspath(entry.path)
                elif entry.is_dir():
                    yield yield_files_in(entry.path, ext=ext, recursive=recursive)
        else:
            for entry in os.scandir(directory):
                if entry.is_file():
                    if entry.path.lower().endswith(ext):
                        yield os.path.abspath(entry.path)
                elif entry.is_dir():
                    yield yield_files_in(entry.path, ext=ext, recursive=recursive)


def get_dirs_in(directory: str | Path, recursive: bool = True) -> list[str]:
    dirs = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            dirs.append(entry.path)
            if recursive:
                dirs.extend(get_dirs_in(entry.path, recursive=recursive))
    return dirs


def yield_dirs_in(directory: str | Path, recursive: bool = True):
    for entry in os.scandir(directory):
        if entry.is_dir():
            yield entry.path
            if recursive:
                yield get_dirs_in(entry.path, recursive=recursive)


def assert_paths_exist(files: str | Iterable):
    if isinstance(files, str):
        if not os.path.exists(files):
            raise FileNotFoundError(f"No such file or directory: '{files}'")
    elif isinstance(files, Iterable):
        for file in files:
            if not os.path.exists(file):
                raise FileNotFoundError(f"No such file or directory: '{file}'")
    else:
        raise TypeError(type(files))


def filename_append(filepath: str, front: str = "", back: str = "") -> str:
    if len(front) == 0 and len(back) == 0:
        return filepath
    dirname, filename = os.path.split(filepath)
    if "." in filename:
        ext = "." + filename.split(".")[-1]
    else:
        ext = ""
    filename = ".".join(filename.split(".")[:-1])
    filename = FilterStr.filename(f"{front}{filename}{back}")
    return f"{dirname}{os.sep}{filename}{ext}"
