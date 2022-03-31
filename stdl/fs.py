from __future__ import annotations

import json
import math
import os
import pickle
import platform
import random
import time
from shutil import copy

import yaml


class File:
    encoding = "utf-8"

    def read(filepath: str):
        with open(filepath, "r", encoding=File.encoding) as f:
            return f.read()

    def write(filepath: str, data):
        with open(filepath, "w", encoding=File.encoding) as f:
            f.write(data)

    def append(filepath: str, data, newline: bool = True):
        with open(filepath, "a", encoding=File.encoding) as f:
            f.write(data)
            if newline:
                f.write("\n")

    def copy_to(filepath: str, target_dir: str):
        copy(filepath, target_dir)

    def readlines(filepath: str):
        with open(filepath, "r", encoding=File.encoding) as f:
            return f.readlines()

    def splitlines(filepath: str):
        with open(filepath, "r", encoding=File.encoding) as f:
            return f.read().splitlines()

    def new_from_list(filepath: str, l: list):
        with open(filepath, 'w') as f:
            for item in l:
                f.write("%s\n" % item)


def pickle_load(filepath: str):
    with open(filepath, "rb") as f:
        return pickle.load(f)


def pickle_dump(filepath: str, data):
    with open(filepath, "wb") as f:
        pickle.dump(data, f)


def json_load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def yaml_load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def json_dump(path: str, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4, default=str)


def yaml_dump(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)


def get_dir_size(directory: str, readable: bool = False):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Skip if it's symbolic link.
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    if readable:
        return bytes_readable(total_size)
    return total_size


def move_files(files: list, target_dir: str, mkdir: bool = False):
    if not os.path.exists(target_dir):
        if mkdir:
            os.mkdir(target_dir)
        else:
            raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

    for file in files:
        new_path = f"{target_dir}{os.sep}{os.path.basename(file)}"
        try:
            os.rename(file, new_path)
        except PermissionError as e:
            print(file, "-", e)


def filename_random(extension: str):
    return f"file.{time.time()}.{random.randrange(100009, 999999)}.{extension}"


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


def make_dirs(dest_dir: str, folder_list: str):
    os.chdir(dest_dir)
    for folder in folder_list:
        if not os.path.exists(folder):
            os.mkdir(folder)


def get_files_in(directory: str, file_ext: tuple | str = None) -> list[str]:
    files = []
    for entry in os.scandir(directory):
        if entry.is_file():
            if file_ext is None:
                files.append(entry.path)
            else:
                if entry.path.lower().endswith(file_ext):
                    files.append(entry.path)
        elif entry.is_dir():
            files.extend(get_files_in(entry.path, file_ext=file_ext))
    return files


def yield_files_in(directory: str, file_ext: tuple | str = None):
    for entry in os.scandir(directory):
        if entry.is_file():
            if file_ext is None:
                yield entry.path
            else:
                if entry.path.lower().endswith(file_ext):
                    yield entry.path
        elif entry.is_dir():
            yield yield_files_in(entry.path, file_ext=file_ext)


def get_dirs_in(directory: str) -> list[str]:
    dirs = []
    for entry in os.scandir(directory):
        if entry.is_dir():
            dirs.append(entry.path)
            dirs.extend(get_dirs_in(entry.path))
    return dirs


def assert_paths_exist(files: str | list):
    if isinstance(files, str):
        if not os.path.exists(files):
            raise FileNotFoundError(files)
    elif isinstance(files, list):
        for file in files:
            if not os.path.exists(file):
                raise FileNotFoundError(file)
