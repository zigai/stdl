from __future__ import annotations

import json
import math
import os
import pickle
import platform
import random
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from queue import Queue
from typing import TypeAlias

import yaml

from stdl.dt import fmt_datetime

SEP = os.sep

AUDIO_EXT = (".mp3", ".aac", ".ogg", ".flac", ".wav", ".aiff", ".dsd", ".pcm")
IMAGE_EXT = (
    ".jpg",
    ".png",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".jfif",
    ".heic",
    ".dib",
    ".jp2",
    ".jpx",
    ".j2k",
    ".jxl",
)
VIDEO_EXT = (
    ".mp4",
    ".mkv",
    ".avi",
    ".flv",
    ".mov",
    ".webm",
    ".mpg",
    ".mpeg",
    ".mpe",
    ".mpv",
    ".ogg",
    ".m4p",
    ".m4v",
    ".wmv",
    ".f4v",
    ".swf",
)


class File:
    def __init__(self, path: str | Path | File | bytes, encoding="utf-8", *, abspath=True) -> None:
        if isinstance(path, (Path, File)):
            path = str(path)
        elif isinstance(path, bytes):
            path = path.decode()
        if abspath:
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

    def to_str(self) -> str:
        return str(self)

    def create(self):
        if self.exists:
            return
        open(self.path, "a", encoding=self.encoding).close()

    def remove(self):
        if not self.exists:
            return
        os.remove(self.path)

    def clear(self):
        if not self.exists:
            return
        open(self.path, "w", encoding=self.encoding).close()

    def read(self) -> str:
        with open(self.path, "r", encoding=self.encoding) as f:
            return f.read()

    def __write(self, data, mode: str, *, newline: bool = True):
        with open(self.path, mode, encoding=self.encoding) as f:
            f.write(data)
            if newline:
                f.write("\n")

    def __write_iter(self, data: Iterable, mode: str, sep="\n") -> None:
        with open(self.path, mode, encoding=self.encoding) as f:
            for entry in data:
                f.write(f"{entry}{sep}")

    def write(self, data, *, newline: bool = True) -> None:
        self.__write(data, "w", newline=newline)

    def append(self, data, *, newline: bool = True) -> None:
        self.__write(data, "a", newline=newline)

    def write_iter(self, data: Iterable, sep="\n") -> None:
        self.__write_iter(data, "w", sep=sep)

    def append_iter(self, data: Iterable, sep="\n") -> None:
        self.__write_iter(data, "a", sep=sep)

    def readlines(self) -> list[str]:
        with open(self.path, "r", encoding=self.encoding) as f:
            return f.readlines()

    def splitlines(self) -> list[str]:
        return self.read().splitlines()

    def move_to(self, directory: str, *, overwrite=True):
        mv_path = f"{directory}{SEP}{self.basename}"
        if os.path.exists(mv_path) and not overwrite:
            raise FileExistsError(mv_path)
        os.rename(self.path, mv_path)
        self.path = mv_path
        return self

    def copy_to(self, directory, *, mkdir=False, overwrite=True):
        if not os.path.isdir(directory):
            if mkdir:
                os.mkdir(directory)
            else:
                raise FileNotFoundError(f"No such directory: '{directory}'")
        copy_path = f"{directory}{SEP}{self.basename}"
        if os.path.exists(copy_path) and not overwrite:
            raise FileExistsError(copy_path)
        self.path = shutil.copy2(self.path, directory)
        return self

    def get_xattr(self, name: str, group="user") -> str:
        return os.getxattr(self.path, f"{group}.{name}").decode()

    def set_xattr(self, value: str | bytes, name: str, group="user") -> None:
        if isinstance(value, str):
            value = value.encode()
        os.setxattr(self.path, f"{group}.{name}", value)

    def remove_xattr(self, name: str, group="user") -> None:
        os.removexattr(self.path, f"{group}.{name}")

    def with_ext(self, ext: str):
        if not ext.startswith("."):
            ext = f".{ext}"
        self.path = f"{self.dirname}{SEP}{self.stem}{ext}"
        return self

    def with_suffix(self, suffix: str):
        ext = self.ext
        if ext is None:
            ext = ""
        else:
            ext = f".{ext}"
        filename = f"{self.stem}{suffix}{ext}"
        self.path = f"{self.dirname}{SEP}{filename}"
        return self

    def with_prefix(self, prefix: str):
        ext = self.ext
        if ext is None:
            ext = ""
        else:
            ext = f".{ext}"
        filename = f"{prefix}{self.stem}{ext}"
        self.path = f"{self.dirname}{SEP}{filename}"
        return self

    @classmethod
    def rand(cls, prefix: str = "file", ext: str = ""):
        return File(rand_filename(prefix, ext))


Pathlike: TypeAlias = str | Path | File | bytes


def pathlike_to_str(path: Pathlike) -> str:
    if isinstance(path, bytes):
        return path.decode()
    return str(path)


def pickle_load(filepath: Pathlike):
    with open(pathlike_to_str(filepath), "rb") as f:
        return pickle.load(f)


def pickle_dump(data, filepath: Pathlike) -> None:
    with open(pathlike_to_str(filepath), "wb") as f:
        pickle.dump(data, f)


def json_load(path: Pathlike, encoding="utf-8") -> dict | list[dict]:
    with open(pathlike_to_str(path), "r", encoding=encoding) as f:
        return json.load(f)


def json_append(
    data: dict | list[dict],
    filepath: Pathlike,
    encoding="utf-8",
    default=None,
    indent=4,
):
    file = File(filepath)
    if not file.exists or file.size() == 0:
        json_dump([data], filepath, encoding=encoding, indent=indent, default=default)
        return
    path = pathlike_to_str(filepath)
    with open(path, "a+", encoding=encoding) as f:
        f.seek(0)
        first_char = f.read(1)
        if first_char == "[":
            f.seek(0, os.SEEK_END)
            f.seek(f.tell() - 2, os.SEEK_SET)
            f.truncate()
            f.write(",\n")
            json.dump(data, f, indent=indent, default=default)
            f.write("]\n")
        elif first_char == "{":
            file_data = first_char + f.read()
            f.seek(0)
            f.truncate()
            f.seek(0)
            f.write("[\n")
            f.write(file_data)
            f.write(",\n")
            json.dump(data, f, indent=indent, default=default)
            f.write("]\n")
        else:
            raise ValueError(f"Cannot parse '{path}' as JSON.")


def yaml_load(path: Pathlike, encoding="utf-8") -> dict | list[dict]:
    with open(pathlike_to_str(path), "r", encoding=encoding) as f:
        return yaml.safe_load(f)


def json_dump(data, path: Pathlike, encoding="utf-8", default=str, indent=4) -> None:
    with open(pathlike_to_str(path), "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, default=default)


def yaml_dump(data, path: Pathlike, encoding="utf-8") -> None:
    with open(pathlike_to_str(path), "w", encoding=encoding) as f:
        yaml.safe_dump(data, f)


def get_dir_size(directory: str | Path, *, readable: bool = False) -> str | int:
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


def move_files(files: list[Pathlike], directory: str | Path, *, mkdir: bool = False) -> None:
    directory = str(directory)
    if not os.path.exists(directory):
        if mkdir:
            os.makedirs(directory)
        else:
            raise FileNotFoundError(f"{directory} is not a directory")
    for file in files:
        file = pathlike_to_str(file)
        os.rename(file, f"{directory}{SEP}{os.path.basename(file)}")


def rand_filename(prefix: str = "file", ext: str = "") -> str:
    if len(ext) and not ext.startswith("."):
        ext = f".{ext}"
    creation_time = fmt_datetime(d_sep="-", t_sep="-", ms=True).replace(" ", ".")
    num = str(random.randrange(10000000, 99999999)).zfill(8)
    return f"{prefix}.{creation_time}.{num}{ext}"


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


def readable_size_to_bytes(size: str, kb_size: int = 1024) -> int:
    # Based on https://stackoverflow.com/a/42865957/2002471
    KB_UNITS = {
        1024: {"B": 1, "KB": 2**10, "MB": 2**20, "GB": 2**30, "TB": 2**40},
        1000: {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12},
    }
    if not kb_size in KB_UNITS:
        raise ValueError(kb_size)
    if re.fullmatch(r"[\d]+", size):
        return int(size)
    size = size.upper()
    if not re.match(r" ", size):
        size = re.sub(r"([KMGT]?B)", r" \1", size)
    number, unit = [string.strip() for string in size.split()]
    return int(float(number) * KB_UNITS[kb_size][unit])


def windows_has_drive(letter: str) -> bool:
    if sys.platform != "win32":
        return False
    return os.path.exists(f"{letter}:{SEP}")


def is_wsl():
    return sys.platform == "linux" and "microsoft" in platform.platform()


def make_dirs(dest: str, dirs: list[str]):
    if not os.path.exists(dest):
        os.makedirs(dest)
    for i in dirs:
        if not os.path.exists(i):
            os.mkdir(f"{dest}{SEP}{i}")


def yield_files_in(
    directory: str | Path, ext: str | tuple | None = None, *, recursive: bool = True
):
    if not recursive:
        for entry in os.scandir(directory):
            if not entry.is_file():
                continue
            path = os.path.abspath(entry.path)
            if ext is None:
                yield path
            else:
                if path.lower().endswith(ext):
                    yield path
        return

    queue = Queue()
    queue.put(directory)

    if ext is None:
        while not queue.empty():
            next_dir = queue.get()
            for entry in os.scandir(next_dir):
                if entry.is_dir():
                    queue.put(entry.path)
                elif entry.is_file():
                    yield os.path.abspath(entry.path)
        return

    while not queue.empty():
        next_dir = queue.get()
        for entry in os.scandir(next_dir):
            if entry.is_dir():
                queue.put(entry.path)
            elif entry.is_file():
                path = os.path.abspath(entry.path)
                if path.lower().endswith(ext):
                    yield path


def get_files_in(
    directory: str | Path,
    ext: str | tuple | None = None,
    *,
    recursive: bool = True,
) -> list[str]:
    return list(yield_files_in(directory, ext, recursive=recursive))


def yield_dirs_in(directory: str | Path, *, recursive: bool = True):
    queue = Queue()
    queue.put(directory)
    while not queue.empty():
        next_dir = queue.get()
        for entry in os.scandir(next_dir):
            if entry.is_dir():
                yield os.path.abspath(entry.path)
                if recursive:
                    queue.put(entry.path)


def get_dirs_in(directory: str | Path, *, recursive: bool = True) -> list[str]:
    return list(yield_dirs_in(directory, recursive=recursive))


def __assert_path_exists(path: Pathlike):
    if not os.path.exists(pathlike_to_str(path)):
        raise FileNotFoundError(f"No such file or directory: '{path}'")


def assert_paths_exist(*args: Pathlike | Iterable[Pathlike]):
    for path in args:
        if isinstance(path, (str, bytes)):
            __assert_path_exists(path)
        elif isinstance(path, Iterable):
            for i in path:
                __assert_path_exists(i)


def exec_cmd(
    cmd: str | list[str],
    timeout: float = None,
    shell=False,
    check=False,
    capture_output=True,
    text=True,
    env: dict = None,
    cwd=None,
    stdin=None,
    stdout=None,
    stderr=None,
    input: str | bytes = None,
    *args,
    **kwargs,
):
    """
    Wrapper for subprocess.run with nicer default arguments.
    """
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    return subprocess.run(
        cmd,
        timeout=timeout,
        shell=shell,
        check=check,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        capture_output=capture_output,
        text=text,
        input=input,
        env=env,
        cwd=cwd,
        *args,
        **kwargs,
    )


__all__ = [
    "IMAGE_EXT",
    "AUDIO_EXT",
    "VIDEO_EXT",
    "File",
    "Pathlike",
    "pathlike_to_str",
    "pickle_load",
    "pickle_dump",
    "json_load",
    "json_append",
    "yaml_load",
    "json_dump",
    "yaml_dump",
    "get_dir_size",
    "move_files",
    "rand_filename",
    "bytes_readable",
    "readable_size_to_bytes",
    "windows_has_drive",
    "is_wsl",
    "make_dirs",
    "yield_files_in",
    "get_files_in",
    "yield_dirs_in",
    "get_dirs_in",
    "assert_paths_exist",
    "exec_cmd",
    "SEP",
    "os",
]
