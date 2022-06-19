from __future__ import annotations

import json
import math
import os
import pickle
import platform
import random
import time
from shutil import copy
from typing import Any, Dict, List, Tuple, Union

import yaml


class File:

    @staticmethod
    def read(filepath: str, encoding="utf-8"):
        with open(filepath, "r", encoding=encoding) as f:
            return f.read()

    @staticmethod
    def write(data, filepath: str, encoding="utf-8"):
        with open(filepath, "w", encoding=encoding) as f:
            f.write(data)

    @staticmethod
    def append(data, filepath: str, newline: bool = True, encoding="utf-8"):
        with open(filepath, "a", encoding=encoding) as f:
            f.write(data)
            if newline:
                f.write("\n")

    @staticmethod
    def copy_to(filepath: str, directory: str):
        copy(filepath, directory)

    @staticmethod
    def readlines(filepath: str, encoding="utf-8") -> List[str]:
        with open(filepath, "r", encoding=encoding) as f:
            return f.readlines()

    @staticmethod
    def splitlines(filepath: str, encoding="utf-8") -> List[str]:
        with open(filepath, "r", encoding=encoding) as f:
            return f.read().splitlines()

    @staticmethod
    def new_from_list(filepath: str, l: list, encoding="utf-8"):
        with open(filepath, 'w', encoding=encoding) as f:
            for line in l:
                f.write(f"{line}\n")

    @staticmethod
    def exists(filepath: str) -> bool:
        return os.path.exists(filepath)


def pickle_load(filepath: str):
    with open(filepath, "rb") as f:
        return pickle.load(f)


def pickle_dump(filepath: str, data):
    with open(filepath, "wb") as f:
        pickle.dump(data, f)


def json_load(path: str, encoding="utf-8") -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    with open(path, "r", encoding=encoding) as f:
        return json.load(f)


def yaml_load(path: str, encoding="utf-8") -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    with open(path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)


def json_dump(path: str, data, encoding="utf-8"):
    with open(path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=4, default=str)


def yaml_dump(path: str, data, encoding="utf-8"):
    with open(path, "w", encoding=encoding) as f:
        yaml.safe_dump(data, f)


def get_dir_size(directory: str, readable: bool = False) -> Union[str, int]:
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


def move_files(files: list, directory: str, mkdir: bool = False):
    if not os.path.exists(directory):
        if mkdir:
            os.mkdir(directory)
        else:
            raise FileNotFoundError(f"Target directory does not exist ({directory})")
    for file in files:
        new_path = f"{directory}{os.sep}{os.path.basename(file)}"
        os.rename(file, new_path)


def random_filename(extension: str = "txt", prefix: str = "file") -> str:
    if extension.startswith("."):
        extension = extension[1:]
    return f"{prefix}.{time.time()}.{random.randrange(1000000, 9999999)}.{extension}"


def bytes_readable(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def win32_has_drive(letter: str) -> bool:
    return "Windows" in platform.system() and os.system("vol %s: 2>nul>nul" % letter) == 0


def make_dirs(dest_dir: str, dirs: str):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    for i in dirs:
        if not os.path.exists(i):
            os.mkdir(f"{dest_dir}{os.sep}{i}")


def get_files_in(directory: str,
                 ext: Union[str, Tuple[str], None] = None,
                 recursive: bool = True) -> List[str]:
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


def yield_files_in(directory: str,
                   ext: Union[str, Tuple[str], None] = None,
                   recursive: bool = True):
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


def get_dirs_in(directory: str, recursive: bool = True) -> List[str]:
    dirs = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            dirs.append(entry.path)
            if recursive:
                dirs.extend(get_dirs_in(entry.path, recursive=recursive))
    return dirs


def assert_paths_exist(files: Union[str, list, tuple]):
    if isinstance(files, str):
        if not os.path.exists(files):
            raise FileNotFoundError(files)
    elif isinstance(files, list) or isinstance(files, tuple):
        for file in files:
            if not os.path.exists(file):
                raise FileNotFoundError(file)
    else:
        raise TypeError(files)


def filename_append(filepath: str, front: str = "", back: str = "") -> str:
    if len(front) == 0 and len(back) == 0:
        return filepath
    dname, fname = os.path.split(filepath)
    if "." in fname:
        ext = "." + fname.split(".")[-1]
    else:
        ext = ""
    fname = ".".join(fname.split(".")[:-1])
    fname = f"{front}{fname}{back}"
    return f"{dname}{os.sep}{fname}{ext}"
