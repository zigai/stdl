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

IMAGE_EXT = (".jpg", ".png", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff")
VIDEO_EXT = (".mp4", ".mkv", ".avi", ".flv", ".mov", ".webm", ".mpg", ".mpeg", ".mpe", ".mpv",
             ".ogg", ".m4p", ".m4v", ".wmv", ".f4v", ".swf")
SONG_EXT = (".mp3", ".aac", ".ogg", ".flac", ".wav", ".aiff", ".dsd", ".pcm")


class File:

    def __init__(self, path: str | Path, encoding="utf-8") -> None:
        if isinstance(path, Path):
            path = str(path)
        self.path = os.path.abspath(path)
        self.encoding = encoding

    def __str__(self):
        return self.path

    @property
    def exists(self) -> bool:
        return os.path.isfile(self.path)

    @property
    def dirname(self) -> str:
        return os.path.dirname(self.path)

    @property
    def created(self) -> float:
        return os.path.getctime(self.path)

    @property
    def modified(self) -> float:
        return os.path.getmtime(self.path)

    @property
    def basename(self) -> str:
        return os.path.basename(self.path)

    @property
    def ext(self) -> str | None:
        if "." in self.basename:
            return self.basename.split(".")[-1]
        return None

    @property
    def abspath(self) -> str:
        return os.path.abspath(self.path)

    @property
    def stem(self):
        base = self.basename
        if "." not in base:
            return base
        return ".".join(base.split(".")[:-1])

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

    def __write(self, data, mode: str, newline: bool = True):
        with open(self.path, mode, encoding=self.encoding) as f:
            f.write(data)
            if newline:
                f.write("\n")

    def __write_iter(self, data: Iterable, mode: str, sep="\n", newline: bool = True) -> None:
        with open(self.path, mode, encoding=self.encoding) as f:
            for entry in data:
                f.write(f"{entry}{sep}")
            if newline:
                f.write("\n")

    def write(self, data, newline: bool = True) -> None:
        self.__write(data, "w", newline=newline)

    def append(self, data, newline: bool = True) -> None:
        self.__write(data, "a", newline=newline)

    def write_iter(self, data: Iterable, sep="\n", newline: bool = True) -> None:
        self.__write_iter(data, "w", sep=sep, newline=newline)

    def append_iter(self, data: Iterable, sep="\n", newline: bool = True) -> None:
        self.__write_iter(data, "a", sep=sep, newline=newline)

    def readlines(self) -> list[str]:
        with open(self.path, "r", encoding=self.encoding) as f:
            return f.readlines()

    def splitlines(self) -> list[str]:
        return self.read().splitlines()

    def move_to(self, directory: str, overwrite=True):
        mv_path = f"{directory}{os.sep}{os.path.basename(self.path)}"
        if os.path.exists(mv_path) and not overwrite:
            raise FileExistsError(mv_path)
        os.rename(self.path, mv_path)
        self.path = mv_path
        return self

    def copy_to(self, directory, mkdir=False, overwrite=True):
        if not os.path.isdir(directory):
            if mkdir:
                os.mkdir(directory)
            else:
                raise FileNotFoundError(f"No such directory: '{directory}'")
        copy_path = f"{directory}{os.sep}{self.basename}"
        if os.path.exists(copy_path) and not overwrite:
            raise FileExistsError(copy_path)

        self.path = shutil.copy2(self.path, directory)
        return self

    def get_xattr(self, name: str, group="user") -> str:
        return os.getxattr(self.path, f'{group}.{name}').decode()

    def set_xattr(self, value: str | bytes, name: str, group="user") -> None:
        if isinstance(value, str):
            value = value.encode()
        os.setxattr(self.path, f'{group}.{name}', value)

    def with_ext(self, ext: str):
        if not ext.startswith("."):
            ext = f",{ext}"
        self.path = f"{self.dirname}{os.sep}{self.stem}{ext}"
        return self

    def with_suffix(self, suffix: str):
        ext = self.ext
        if ext is None:
            ext = ""
        else:
            ext = f".{ext}"
        filename = f"{self.stem}{suffix}{ext}"
        self.path = f"{self.dirname}{os.sep}{filename}"
        return self

    def with_prefix(self, prefix: str):
        ext = self.ext
        if ext is None:
            ext = ""
        else:
            ext = f".{ext}"
        filename = f"{prefix}{self.stem}{ext}"
        self.path = f"{self.dirname}{os.sep}{filename}"
        return self


def pickle_load(filepath: str | Path):
    with open(filepath, "rb") as f:
        return pickle.load(f)


def pickle_dump(data, filepath: str | Path) -> None:
    with open(filepath, "wb") as f:
        pickle.dump(data, f)


def json_load(path: str | Path, encoding="utf-8") -> dict | list[dict]:
    with open(path, "r", encoding=encoding) as f:
        return json.load(f)


def json_append(data: dict | list[dict], filepath: str | Path, encoding="utf-8", default=None, indent=4):
    file = File(filepath)
    if not file.exists or file.size() == 0:
        json_dump(data, filepath)
        return
    with open(filepath, 'a+', encoding=encoding) as f:
        f.seek(0)
        first_char = f.read(1)
        if first_char == "[":
            f.seek(0, os.SEEK_END)
            f.seek(f.tell() - 2, os.SEEK_SET)
            f.truncate()
            f.write(',\n')
            json.dump(data, f, indent=indent, default=default)
            f.write(']\n')
        elif first_char == "{":
            file_data = first_char + f.read()
            f.seek(0)
            f.truncate()
            f.seek(0)
            f.write("[\n")
            f.write(file_data)
            f.write(",\n")
            json.dump(data, f, indent=indent, default=default)
            f.write(']\n')
        else:
            raise ValueError(f"Cannot parse '{filepath}' as JSON.")


def yaml_load(path: str | Path, encoding="utf-8") -> dict | list[dict]:
    with open(path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)


def json_dump(data, path: str | Path, encoding="utf-8", default=str, indent=4) -> None:
    with open(path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=indent, default=default)


def yaml_dump(data, path: str | Path, encoding="utf-8") -> None:
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


def random_filename(ext: str = "", prefix: str = "file") -> str:
    if len(ext) and not ext.startswith("."):
        ext = f".{ext}"
    return f"{prefix}.{time.time()}.{random.randrange(1000000, 9999999)}{ext}"


def bytes_readable(size_bytes: int) -> str:
    if size_bytes < 0:
        raise ValueError(size_bytes)
    if size_bytes == 0:
        return "0B"
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
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
    directory: str | Path,
    ext: str | tuple | None = None,
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
                    files.extend(get_files_in(
                        entry.path, ext=ext, recursive=recursive))
        else:
            for entry in os.scandir(directory):
                if entry.is_file():
                    if entry.path.lower().endswith(ext):
                        files.append(os.path.abspath(entry.path))
                elif entry.is_dir():
                    files.extend(get_files_in(
                        entry.path, ext=ext, recursive=recursive))
    return files


def yield_files_in(directory: str | Path, ext: str | tuple | None = None, recursive: bool = True):
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
                yield yield_dirs_in(entry.path, recursive=recursive)


def assert_paths_exist(files: str | Iterable, *args):
    if isinstance(files, str):
        if not os.path.exists(files):
            raise FileNotFoundError(f"No such file or directory: '{files}'")
    elif isinstance(files, Iterable):
        for file in files:
            if not os.path.exists(file):
                raise FileNotFoundError(f"No such file or directory: '{file}'")
    for file in args:
        if not os.path.exists(file):
            raise FileNotFoundError(f"No such file or directory: '{files}'")
