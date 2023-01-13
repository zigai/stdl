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
from typing import IO, Any, Generator, TypeAlias

import yaml

from stdl.dt import fmt_datetime

SEP = os.sep
HOME = os.path.expanduser("~")
abspath = os.path.abspath
basename = os.path.basename
dirname = os.path.dirname
joinpath = os.path.join
splitpath = os.path.split

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
        """Initialize a File object.

        Args:
            path (str | Path | bytes): File path.
            encoding (str, optional): The file's encoding. Defaults to "utf-8".
            abspath (bool, keyword-only): Whether to use the absolute path. Defaults to True.
        """
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
        """The file's directory name."""
        return os.path.dirname(self.path)

    @property
    def created(self) -> float:
        """The time when the file was created as a UNIX timestamp."""
        return os.path.getctime(self.path)

    @property
    def modified(self) -> float:
        """The time when the file was last modified as a UNIX timestamp."""
        return os.path.getmtime(self.path)

    @property
    def basename(self) -> str:
        """The file's base name (without the directory)."""
        return os.path.basename(self.path)

    @property
    def ext(self) -> str | None:
        """The file's extension (without the dot).
        Returns None if the file has no extension."""
        if "." in self.basename:
            return self.basename.split(".")[-1]
        return None

    @property
    def abspath(self) -> str:
        """The file's absolute path."""
        return os.path.abspath(self.path)

    @property
    def stem(self):
        """The file's stem (base name without extension)."""
        base = self.basename
        if "." not in base:
            return base
        return ".".join(base.split(".")[:-1])

    def size(self, readable: bool = False) -> int | str:
        """The file's size in bytes or a human-readable format if readable is set to True."""
        size = os.path.getsize(self.path)
        if readable:
            return bytes_readable(size)
        return size

    def to_path(self) -> Path:
        """Convert to  pathlib.Path"""
        return Path(self.path)

    def to_str(self) -> str:
        return str(self)

    def create(self):
        """Create an empty file if it doesn't exist."""
        if self.exists:
            return
        open(self.path, "a", encoding=self.encoding).close()

    def remove(self):
        """Remove the file."""
        if not self.exists:
            return
        os.remove(self.path)

    def clear(self):
        """Clear the contents of a file if it exists"""
        if not self.exists:
            return
        open(self.path, "w", encoding=self.encoding).close()

    def read(self) -> str:
        """Read the contents of a file."""
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
        """
        Write data to a file, overwriting any existing data.

        Args:
            data (Any): The data to write.
            newline (bool, optional): Whether to add a newline at the end of the data. Defaults to True.
        """
        self.__write(data, "w", newline=newline)

    def append(self, data, *, newline: bool = True) -> None:
        """
        Append data to a file.

        Args:
            data (Any): The data to append.
            newline (bool, optional): Whether to add a newline at the end of the data. Defaults to True.
        """
        self.__write(data, "a", newline=newline)

    def write_iter(self, data: Iterable, sep="\n") -> None:
        """Write data from an iterable to a file, overwriting any existing data.

        Args:
            data (Iterable): The data to write.
            sep (str, optional): The separator to use between items. Defaults to "\\n".
        """
        self.__write_iter(data, "w", sep=sep)

    def append_iter(self, data: Iterable, sep="\n") -> None:
        """Append data from an iterable to a file.

        Args:
            data (Iterable): The data to append.
            sep (str, optional): The separator to use between items. Defaults to "\\n".
        """
        self.__write_iter(data, "a", sep=sep)

    def readlines(self) -> list[str]:
        """Equivalent to TextIOWrapper.readlines()"""
        with open(self.path, "r", encoding=self.encoding) as f:
            return f.readlines()

    def splitlines(self) -> list[str]:
        """Equivalent to File.read().splitlines()"""
        return self.read().splitlines()

    def move_to(self, directory: str, *, overwrite=True):
        """
        Move the file to a new directory.

        Args:
            directory (str): The destination directory.
            overwrite (bool, optional): Whether to overwrite the file if it already exists in the destination directory. Defaults to True.
        """
        mv_path = f"{directory}{SEP}{self.basename}"
        if os.path.exists(mv_path) and not overwrite:
            raise FileExistsError(mv_path)
        os.rename(self.path, mv_path)
        self.path = mv_path
        return self

    def copy_to(self, directory, *, mkdir=False, overwrite=True):
        """
        Copy the file to a new directory.

        Args:
            directory (str): The destination directory.
            overwrite (bool, optional): Whether to overwrite the file if it already exists in the destination directory. Defaults to True.
        """
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
        """Retrieve the value of an extended attribute for the file.

        Args:
            name (str): The name of the extended attribute.
            group (str, optional): The group of the extended attribute. Defaults to "user".

        Returns:
            str: The value of the extended attribute.
        """
        return os.getxattr(self.path, f"{group}.{name}").decode()

    def set_xattr(self, value: str | bytes, name: str, group="user") -> None:
        """Set an extended attribute for the file.

        Args:
            value (str | bytes): The value of the extended attribute.
            name (str): The name of the extended attribute.
            group (str, optional): The group of the extended attribute. Defaults to "user".
        """
        if isinstance(value, str):
            value = value.encode()
        os.setxattr(self.path, f"{group}.{name}", value)

    def remove_xattr(self, name: str, group="user") -> None:
        """Remove an extended attribute from the file.

        Args:
            name (str): The name of the extended attribute.
            group (str, optional): The group of the extended attribute. Defaults to "user".
        """
        os.removexattr(self.path, f"{group}.{name}")

    def with_ext(self, ext: str):
        """Change the extension of the file and return the new File object

        Args:
            ext (str): The new extension of the file.

        Returns:
            File: The File object with the new extension.
        """
        if not ext.startswith("."):
            ext = f".{ext}"
        self.path = f"{self.dirname}{SEP}{self.stem}{ext}"
        return self

    def with_suffix(self, suffix: str):
        """Add a suffix to the file's name and return the new File object."""
        ext = self.ext
        if ext is None:
            ext = ""
        else:
            ext = f".{ext}"
        filename = f"{self.stem}{suffix}{ext}"
        self.path = f"{self.dirname}{SEP}{filename}"
        return self

    def with_prefix(self, prefix: str):
        """Add a prefix to the file's name and return the new File object."""
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
        """
        Create a new random file with a specified prefix and extension.

        Args:
            prefix (str, optional): The prefix for the file name. Defaults to "file".
            ext (str, optional): The extension for the file name. Defaults to "".

        Returns:
            File: A new File object with a random name.
        """
        return File(rand_filename(prefix, ext))


Pathlike: TypeAlias = str | Path | File | bytes


def pathlike_to_str(path: Pathlike) -> str:
    """Converts a pathlike object to a string."""
    if isinstance(path, bytes):
        return path.decode()
    return str(path)


def pickle_load(filepath: Pathlike):
    """Loads a pickled file."""
    with open(pathlike_to_str(filepath), "rb") as f:
        return pickle.load(f)


def pickle_dump(data: Any, filepath: Pathlike) -> None:
    """Dumps an object to the specified filepath."""

    with open(pathlike_to_str(filepath), "wb") as f:
        pickle.dump(data, f)


def json_load(path: Pathlike, encoding="utf-8") -> dict | list[dict]:
    """Load a JSON file from the given path.

    Args:
        path (Pathlike): The path of the JSON file to load.
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".

    Returns:
        dict | list[dict]: The JSON data loaded from the file.
    """
    with open(pathlike_to_str(path), "r", encoding=encoding) as f:
        return json.load(f)


def json_append(
    data: dict | list[dict],
    filepath: Pathlike,
    encoding="utf-8",
    default=None,
    indent=4,
):
    """Appends data to a JSON file.
    Args:
        data (Union[dict, List[dict]]): The data to be appended
        filepath (Pathlike): The path of the JSON file
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".
        default : A function that gets called for objects that can’t otherwise be serialized.
                  See json.dump() documentation for more information.
        indent (int, optional): The number of spaces to use for indentation. Defaults to 4.
    """

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
    """Load a YAML file from the given path.

    Args:
        path (Pathlike): The path of the YAML file to load.
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".

    Returns:
        dict | list[dict]: The YAML data loaded from the file.
    """
    with open(pathlike_to_str(path), "r", encoding=encoding) as f:
        return yaml.safe_load(f)


def json_dump(data, path: Pathlike, encoding="utf-8", default=str, indent=4) -> None:
    """
    Dumps data to a JSON file

    Args:
        data: data to be dumped
        path (Pathlike): path to the output file
        encoding (str): encoding of the output file. Default: 'utf-8'
        default: A function that gets called on objects that cannot be serialized. Default: str
        indent (int): number of spaces to use when indenting the output json. Default: 4
    """
    with open(pathlike_to_str(path), "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, default=default)


def yaml_dump(data, path: Pathlike, encoding="utf-8") -> None:
    """
    Dumps data to a YAML file
    Args:
        data: data to be dumped
        path (Pathlike): path to the output file
        encoding (str): encoding of the output file. Default: 'utf-8'
    """
    with open(pathlike_to_str(path), "w", encoding=encoding) as f:
        yaml.safe_dump(data, f)


def get_dir_size(directory: str | Path, *, readable: bool = False) -> str | int:
    """Moves files to a specified directory

    Args:
        files (list): List of files to be moved
        directory (str, Path): target directory
        mkdir (bool, optional): whether to create the directory if it doesn't exist. Default: False

    Raises:
        FileNotFoundError : if the target directory does not exist and mkdir is False
    """
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
    """Moves files to a specified directory

    Args:
        files (list[Pathlike]): List of files to be moved
        directory (str | Path): target directory
        mkdir (bool): whether to create the directory if it doesn't exist. Default: False

    Raises:
        FileNotFoundError : if the target directory does not exist and mkdir is False.
    """
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
    """
    Generates a random filename with the given prefix and extension.
    Current date and time are also included in the filename.
    Args:
        prefix (str, optional): Filename prefix. Defaults to "file".
        ext (str, optional): Filename extension. Defaults to "".
    Returns:
        str: The generated random filename.
    """
    if len(ext) and not ext.startswith("."):
        ext = f".{ext}"
    creation_time = fmt_datetime(d_sep="-", t_sep="-", ms=True).replace(" ", ".")
    num = str(random.randrange(10000000, 99999999)).zfill(8)
    return f"{prefix}.{creation_time}.{num}{ext}"


def bytes_readable(size_bytes: int) -> str:
    """Convert bytes to a human-readable string.
    Args:
        size_bytes (int): The number of bytes
    Returns:
        str : The number of bytes in a human-readable format
    """
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
    """Convert human-readable string to bytes.
    Args:
        size (str): The number of bytes in human-readable format
        kb_size (int, optional): The byte size of a kilobyte (1000 or 1024). Defaults to 1024.
    Returns:
        int: The number of bytes
    """
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
    """
    Check if a drive letter exists on Windows.
    Will always return False if the platform is not Windows.
    Args:
        letter (str): The letter of the drive.
    Returns:
        bool: Whether the drive exists.
    """
    if sys.platform != "win32":
        return False
    return os.path.exists(f"{letter}:{SEP}")


def is_wsl() -> bool:
    """
    Check if the current platform is Windows Subsystem for Linux (WSL).
    """
    return sys.platform == "linux" and "microsoft" in platform.platform()


def make_dirs(dest: str, directories: list[str]) -> None:
    """Creates directories inside a destination directory.
    Args:
        dest (str): The destination directory.
        dirs (list[str]): A list of directories to be created in the destination directory.
    """
    if not os.path.exists(dest):
        os.makedirs(dest)
    for i in directories:
        if not os.path.exists(i):
            os.mkdir(f"{dest}{SEP}{i}")


def make_dir(directory: str):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)


def yield_files_in(
    directory: str | Path, ext: str | tuple | None = None, *, recursive: bool = True
) -> Generator[str, None, None]:
    """
    Yields the paths of files in a directory.

    This function searches for files in a directory and yields their paths.
    If the `ext` parameter is provided, only files with that extension are yielded. The `ext` parameter is case-insensitive.
    If the `recursive` parameter is set to `True`, the function will search for files in subdirectories recursively.
    Yielded paths are converted to absolute paths.

    Args:
        directory (str | Path): The directory to search.
        ext (str | tuple[str, ...], optional): If provided, only yield files with provided extensions. Defaults to None.
        recursive (bool, optional): Whether to search recursively. Defaults to True.

    Yields:
        Generator[str, None, None]: The absolute paths of the files in the directory, matching the provided extension.
    """
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
    """
    Returns the paths of files in a directory.

    This function searches for files in a directory and yields their paths.
    If the `ext` parameter is provided, only files with that extension are returned. The `ext` parameter is case-insensitive.
    If the `recursive` parameter is set to `True`, the function will search for files in subdirectories recursively.
    Returned paths are converted to absolute paths.

    Args:
        directory (Union[str, Path]): The directory to search.
        ext (Union[str, Tuple[str, ...]], optional): If provided, only yield files with provided extensions. Defaults to None.
        recursive (bool, optional): Whether to search recursively. Defaults to True.

    Returns:
        list[str]: The absolute path of the files in the directory, matching the provided extension.
    """

    return list(yield_files_in(directory, ext, recursive=recursive))


def yield_dirs_in(directory: str | Path, *, recursive: bool = True) -> Generator[str, None, None]:
    """
    Yields paths to all directories in the specified directory.
    Yielded paths are converted to absolute paths.

    Args:
        directory (str | Path): The directory to search.
        recursive (bool, optional): Whether to search recursively. Defaults to True.

    Yields:
        Generator[str, None, None]: The paths of the directories that are found during travelsal.
    """
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
    """
    Returns all directories in the specified directory.
    Returned paths are converted to absolute paths.


    Args:
        directory (str | Path): The directory to search.
        recursive (bool, optional): Whether to search recursively. Defaults to True.

    Returns:
        list[str]: The paths of the directories that are found during travelsal.
    """
    return list(yield_dirs_in(directory, recursive=recursive))


def __assert_path_exists(path: Pathlike) -> None:
    if not os.path.exists(pathlike_to_str(path)):
        raise FileNotFoundError(f"No such file or directory: '{path}'")


def assert_paths_exist(*args: Pathlike | Iterable[Pathlike]) -> None:
    """Asserts that the specified paths exist.

    Args:
        *args : one or more strings representing the paths to check. Can also include an Iterable of paths.

    Raises:
        FileNotFoundError : if one of the provided paths does not exist.
    """
    for path in args:
        if isinstance(path, (str, bytes)):
            __assert_path_exists(path)
        elif isinstance(path, Iterable):
            for i in path:
                __assert_path_exists(i)


def exec_cmd(
    cmd: str | list[str],
    timeout: float = None,  # type:ignore
    shell=False,
    check=False,
    capture_output=True,
    text=True,
    env: dict = None,  # type:ignore
    cwd=None,
    stdin: IO = None,  # type:ignore
    stdout: IO = None,  # type:ignore
    stderr: IO = None,  # type:ignore
    input: str | bytes = None,  # type:ignore
    *args,
    **kwargs,
) -> subprocess.CompletedProcess:
    """
    Wrapper for subprocess.run with nicer default arguments.

    Args:
        cmd (str | list[str]): command to run. A list of strings or a single string.
        timeout (float, optional): the time after which the command is killed.
        shell (bool): whether or not to run the command in a shell.
        check (bool): whether or not to raise an exception on a non-zero exit code.
        capture_output (bool): whether or not to capture the output to stdout and stderr.
        text (bool): whether or not to return output as text or bytes.
        env (dict, optional]): environment variables to pass to the new process.
        cwd (str, optional): current working directory to run the command in.
        stdin (IO, optional): file object to read stdin from.
        stdout (IO, optional): file object to write stdout to.
        stderr (IO, optional): file object to write stderr to.
        input (str | bytes): input to send to the command.
        *args : additional arguments to pass to subprocess.run.
        **kwargs : additional keyword arguments to pass to subprocess.run.

    Returns:
        subprocess.CompletedProcess : the completed process.
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
    "make_dir",
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
    "os",
    "SEP",
    "HOME",
    "abspath",
    "basename",
    "dirname",
    "joinpath",
    "splitpath",
]
