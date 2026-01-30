from __future__ import annotations

import fnmatch
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
import time
from collections.abc import Callable, Generator, Iterable
from datetime import datetime
from os import PathLike
from pathlib import Path
from queue import Queue
from typing import IO, Any, Literal

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from urllib.request import pathname2url

import toml
import yaml

from stdl import st

stat = os.stat
link = os.link
getcwd = os.getcwd

SEP = os.sep
HOME = os.path.expanduser("~")
abspath = os.path.abspath
basename = os.path.basename
dirname = os.path.dirname
joinpath = os.path.join
fspath = os.fspath
splitpath = os.path.split
isdir = os.path.isdir
isfile = os.path.isfile
islink = os.path.islink
exists = os.path.exists

chdir = os.chdir
chmod = os.chmod
remove = os.remove
rename = os.rename

copy = shutil.copy2
move = shutil.move
chown = shutil.chown


def pickle_load(filepath: str | PathLike) -> Any:
    """Loads a pickled file."""
    with open(filepath, "rb") as f:
        return pickle.load(f)


def pickle_dump(data: Any, filepath: str | PathLike) -> None:
    """Dumps an object to the specified filepath."""
    with open(filepath, "wb") as f:
        pickle.dump(data, f)


def json_load(
    path: str | PathLike, encoding: str = "utf-8"
) -> dict[Any, Any] | list[dict[Any, Any]]:
    """
    Load a JSON file from the given path.

    Args:
        path (str | PathLike): The path of the JSON file to load.
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".

    Returns:
        dict | list[dict]: The JSON data loaded from the file.
    """
    with open(os.fspath(path), encoding=encoding) as f:
        return json.load(f)


def json_append(
    data: dict[Any, Any] | list[dict[Any, Any]],
    filepath: str | PathLike,
    encoding: str = "utf-8",
    default: Callable[[Any], str] = str,
    indent: int = 4,
) -> None:
    """
    Append data to a JSON file.

    Args:
        data (dict | list[dict]): The data to be appended
        filepath (str | PathLike): The path of the JSON file
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".
        default : A function that gets called for objects that can't otherwise be serialized.
                  See json.dump() documentation for more information.
        indent (int, optional): The number of spaces to use for indentation. Defaults to 4.
    """
    file = File(filepath)
    path = os.fspath(filepath)
    if not file.exists or file.size == 0:
        json_dump([data], filepath, encoding=encoding, indent=indent, default=default)
        return
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


def json_dump(
    data: Any,
    path: str | PathLike,
    encoding: str = "utf-8",
    default: Callable[[Any], str] = str,
    indent: int = 4,
) -> None:
    """
    Dumps data to a JSON file.

    Args:
        data: data to be dumped
        path (str | PathLike): path to the output file
        encoding (str): encoding of the output file. Default: 'utf-8'
        default: A function that gets called on objects that cannot be serialized. Default: str
        indent (int): number of spaces to use when indenting the output json. Default: 4
    """
    with open(os.fspath(path), "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, default=default)


def yaml_load(
    path: str | PathLike, encoding: str = "utf-8"
) -> dict[Any, Any] | list[dict[Any, Any]]:
    """
    Load a YAML file from the given path.

    Args:
        path (str | PathLike): The path of the YAML file to load.
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".

    Returns:
        dict | list[dict]: The YAML data loaded from the file.
    """
    with open(path, encoding=encoding) as f:
        return yaml.safe_load(f)


def yaml_dump(data: Any, path: str | PathLike, encoding: str = "utf-8") -> None:
    """
    Dumps data to a YAML file
    Args:
        data: data to be dumped
        path (Pathlike): path to the output file
        encoding (str): encoding of the output file. Default: 'utf-8'
    """
    with open(path, "w", encoding=encoding) as f:
        yaml.safe_dump(data, f)


def toml_load(path: str | PathLike, encoding: str = "utf-8") -> dict[str, Any]:
    with open(path, encoding=encoding) as f:
        return toml.load(f)


def toml_dump(data: dict[str, Any], path: str | PathLike, encoding: str = "utf-8") -> None:
    with open(path, "w", encoding=encoding) as f:
        toml.dump(data, f)


def get_dir_size(directory: str | PathLike, *, readable: bool = False) -> str | int:
    """
    Moves files to a specified directory

    Args:
        directory (str, Path): target directory
        readable (bool, optional): Return the size in human-readable format
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


def move_files(
    files: list[str | PathLike], directory: str | PathLike, *, mkdir: bool = False
) -> None:
    """
    Moves files to a specified directory

    Args:
        files (list[str | PathLike]): List of files to be moved
        directory (str | PathLike): target directory
        mkdir (bool): whether to create the directory if it doesn't exist. Default: False

    Raises:
        FileNotFoundError : if the target directory does not exist and mkdir is False.
    """
    directory = os.fspath(directory)
    if exists(directory):
        if mkdir:
            os.makedirs(directory, exist_ok=True)
        else:
            raise FileNotFoundError(f"{directory} is not a directory")
    for file in files:
        os.rename(os.fspath(file), f"{directory}{SEP}{os.path.basename(file)}")


def rand_filename(prefix: str = "file", ext: str = "", include_datetime: bool = False) -> str:
    """
    Generates a random filename with the given prefix and extension.
    Optionally includes current date and time in the filename.

    Args:
        prefix (str, optional): Filename prefix.
        ext (str, optional): Filename extension.
        include_datetime (bool, optional): Whether to include date and time.

    Returns:
        str: The generated random filename.
    """
    if ext and not ext.startswith("."):
        ext = f".{ext}"
    num = str(random.randrange(1000000000, 9999999999)).zfill(10)
    if include_datetime:
        creation_time = datetime.now().strftime("%Y-%m-%d.%H-%M-%S-%f")[:-3]
        filename = f"{prefix}.{num}.{creation_time}{ext}"
    else:
        filename = f"{prefix}.{num}{ext}"
    return safe_filename(filename)


def bytes_readable(size_bytes: int) -> str:
    """
    Convert bytes to a human-readable string.

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


def readable_size_to_bytes(size: str, kb_size: Literal[1000, 1024] = 1024) -> int:
    """
    Convert human-readable string to bytes.

    Args:
        size (str): The number of bytes in human-readable format
        kb_size (int, optional): The byte size of a kilobyte (1000 or 1024). Defaults to 1024.

    Returns:
        int: The number of bytes
    """
    if kb_size not in (1000, 1024):
        raise ValueError(f"Invalid kb_size: {kb_size}. Must be 1000 or 1024.")

    size = size.upper().replace(" ", "")
    if size.isdigit():
        return int(size)

    match = re.match(r"^(\d+(\.\d+)?)(B|KB|MB|GB|TB)$", size)
    if not match:
        raise ValueError(f"Invalid size format: {size}")

    number, unit = float(match.group(1)), match.group(3)

    units = {"B": 1, "KB": kb_size, "MB": kb_size**2, "GB": kb_size**3, "TB": kb_size**4}

    if unit not in units:
        raise ValueError(f"Invalid unit: {unit}")

    return int(number * units[unit])


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
    """Check if the current platform is Windows Subsystem for Linux (WSL)."""
    return sys.platform == "linux" and "microsoft" in platform.platform()


def mkdir(path: str | PathLike, mode: int = 511, exist_ok: bool = True) -> None:
    """
    Creates a directory.

    Args:
        path (str | Path): The path of the directory to create.
        mode (int, optional): The mode to set for the directory. Defaults to 511 (octal 0777).
        exist_ok (bool, optional): Whether to raise an exception if the directory already exists. Defaults to True.
    """
    os.makedirs(os.fspath(path), exist_ok=exist_ok, mode=mode)


def mkdirs(dest: str | PathLike, names: list[str]) -> None:
    """
    Creates directories inside a destination directory.

    Args:
        dest (str | Path): The destination directory.
        names (list[str]): A list of directory names to be created in the destination directory.
    """
    if not exists(dest):
        mkdir(dest)
    for i in names:
        if not exists(i):
            path = f"{dest}{SEP}{i}"
            mkdir(path)


def yield_files_in(
    directory: str | PathLike,
    ext: str | tuple[str, ...] | None = None,
    *,
    recursive: bool = True,
    abs: bool = True,
) -> Generator[str, None, None]:
    """
    Yields the paths of files in a directory.

    This function searches for files in a directory and yields their paths.
    If the `ext` parameter is provided, only files with that extension are yielded. The `ext` parameter is case-insensitive.
    If the `recursive` parameter is set to `True`, the function will search for files in subdirectories recursively.

    Args:
        directory (str | Path): The directory to search.
        ext (str | tuple[str, ...], optional): If provided, only yield files with provided extensions.
        recursive (bool, optional): Whether to search recursively.
        abs (bool, optional): Whether to convert paths to absolute paths.

    Yields:
        Generator[str, None, None]: The absolute paths of the files in the directory, matching the provided extension.
    """
    if not recursive:
        for entry in os.scandir(directory):
            if not entry.is_file():
                continue
            path = entry.path
            if abs:
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
                    yield os.path.abspath(entry.path) if abs else entry.path
        return

    while not queue.empty():
        next_dir = queue.get()
        for entry in os.scandir(next_dir):
            if entry.is_dir():
                queue.put(entry.path)
            elif entry.is_file():
                if entry.path.lower().endswith(ext):
                    yield os.path.abspath(entry.path) if abs else entry.path


def get_files_in(
    directory: str | PathLike,
    ext: str | tuple[str, ...] | None = None,
    *,
    recursive: bool = True,
    abs: bool = True,
) -> list[str]:
    """
    Returns the paths of files in a directory.

    This function searches for files in a directory and yields their paths.
    If the `ext` parameter is provided, only files with that extension are returned. The `ext` parameter is case-insensitive.
    If the `recursive` parameter is set to `True`, the function will search for files in subdirectories recursively.

    Args:
        directory (str | Path): The directory to search.
        ext (str | tuple[str, ...], optional): If provided, only yield files with provided extensions. Defaults to None.
        recursive (bool, optional): Whether to search recursively. Defaults to True.
        abs (bool, optional): Whether to convert paths to absolute paths.

    Returns:
        list[str]: The absolute path of the files in the directory, matching the provided extension.
    """
    return list(yield_files_in(directory, ext, recursive=recursive, abs=abs))


def yield_dirs_in(
    directory: str | PathLike, *, recursive: bool = True, abs: bool = True
) -> Generator[str, None, None]:
    """
    Yields paths to all directories in the specified directory.
    Yielded paths are converted to absolute paths.

    Args:
        directory (str | Path): The directory to search.
        recursive (bool, optional): Whether to search recursively.
        abs (bool, optional): Whether to convert paths to absolute paths.


    Yields:
        Generator[str, None, None]: The paths of the directories that are found during travelsal.
    """
    queue = Queue()
    queue.put(directory)
    while not queue.empty():
        next_dir = queue.get()
        for entry in os.scandir(next_dir):
            if entry.is_dir():
                if recursive:
                    queue.put(entry.path)
                yield os.path.abspath(entry.path) if abs else entry.path


def get_dirs_in(
    directory: str | PathLike, *, recursive: bool = True, abs: bool = True
) -> list[str]:
    """
    Returns all directories in the specified directory.
    Returned paths are converted to absolute paths.

    Args:
        directory (str | Path): The directory to search.
        recursive (bool, optional): Whether to search recursively.
        abs (bool, optional): Whether to convert paths to absolute paths.

    Returns:
        list[str]: The paths of the directories that are found during travelsal.
    """
    return list(yield_dirs_in(directory, recursive=recursive, abs=abs))


def ensure_paths_exist(*args: str | PathLike | Iterable[str | PathLike]) -> None:
    """
    Ensures that the specified paths exist.

    Args:
        *args : one or more strings representing the paths to check. Can also include an Iterable of paths.

    Raises:
        FileNotFoundError : if one of the provided paths does not exist.
    """

    def check_path(path: str | PathLike) -> None:
        if not os.path.exists(os.fspath(path)):
            raise FileNotFoundError(f"Path does not exist: '{path}'")

    for path in args:
        if isinstance(path, (str, bytes, PathLike)):
            check_path(path)
        elif isinstance(path, Iterable):
            for i in path:
                check_path(i)


def ensure_paths_dont_exist(*args: str | PathLike | Iterable[str | PathLike]) -> None:
    """
    Ensures that the specified paths don't exist.

    Args:
        *args : one or more strings representing the paths to check. Can also include an Iterable of paths.

    Raises:
        FileNotFoundError : if one of the provided paths exists.
    """

    def check_path(path: str | PathLike) -> None:
        if os.path.exists(os.fspath(path)):
            raise FileExistsError(f"Path already exists: '{path}'")

    for path in args:
        if isinstance(path, (str, bytes, PathLike)):
            check_path(path)
        elif isinstance(path, Iterable):
            for i in path:
                check_path(i)


def safe_filename(name: str) -> str:
    newname = name.replace('"', "'")
    newname = st.remove(newname, chars='<>:"/|?*\\“”;')
    return newname


def safe_filepath(path: str) -> str:
    return st.remove(path, chars='<>"|?*“”;')


class CompletedCommand(subprocess.CompletedProcess):
    def __init__(
        self,
        args: str | list[str],
        returncode: int,
        time_taken: float,
        stdout: Any | None = None,
        stderr: Any | None = None,
    ) -> None:
        super().__init__(args, returncode, stdout, stderr)
        self.time_taken = time_taken

    def __repr__(self) -> str:
        args = [
            f"args={self.args!r}",
            f"returncode={self.returncode!r}",
            f"time_taken={self.time_taken}s",
        ]
        if self.stdout is not None:
            args.append(f"stdout={self.stdout!r}")
        if self.stderr is not None:
            args.append(f"stderr={self.stderr!r}")
        return "{}({})".format(type(self).__name__, ", ".join(args))

    @property
    def stdout_lines(self) -> list[str]:
        """Returns the stdout as a list of lines."""
        if self.stdout is None:
            return []
        return self.stdout.splitlines()

    @property
    def stderr_lines(self) -> list[str]:
        """Returns the stderr as a list of lines."""
        if self.stderr is None:
            return []
        return self.stderr.splitlines()

    def dict(self) -> dict[str, Any]:
        return {
            "args": self.args,
            "returncode": self.returncode,
            "time_taken": self.time_taken,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def exec_cmd(
    cmd: list[str] | str,
    timeout: float | None = None,  # type:ignore
    shell: bool = False,
    capture_output: bool = True,
    check: bool = False,
    cwd: str | None = None,  # type:ignore
    stdin: IO | None = None,  # type:ignore
    stdout: IO | None = None,  # type:ignore
    stderr: IO | None = None,  # type:ignore
    input: str | None | bytes = None,  # type:ignore
    env: dict[str, str] | None = None,  # type:ignore
    text: bool = True,
    *args: Any,
    **kwargs: Any,
) -> CompletedCommand:
    """
    Wrapper for subprocess.run with nicer default arguments.

    Args:
        cmd (str | list[str]): command to run. A list of strings or a single string.
        timeout (float, optional): the time after which the command is killed.
        shell (bool, optional): whether or not to run the command in a shell.
        capture_output (bool, optional): whether or not to capture the output to stdout and stderr.
        check (bool, optional): whether or not to raise an exception on a non-zero exit code.
        cwd (str, optional): current working directory to run the command in.
        stdin (IO, optional): file object to read stdin from.
        stdout (IO, optional): file object to write stdout to.
        stderr (IO, optional): file object to write stderr to.
        input (str | bytes): input to send to the command.
        env (dict, optional): environment variables to pass to the new process.
        text (bool): whether or not to return output as text or bytes.
        *args : additional arguments to pass to subprocess.run.
        **kwargs : additional keyword arguments to pass to subprocess.run.

    Returns:
        subprocess.CompletedProcess : the completed process.
    """
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    start_time = time.time()

    result = subprocess.run(
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
        **kwargs,
    )

    return CompletedCommand(
        result.args,
        result.returncode,
        time.time() - start_time,
        result.stdout,
        result.stderr,
    )


def read_piped() -> str:
    """Reads piped input from stdin."""
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read().strip()


def start_file(path: str | PathLike) -> None:
    """
    Open the file with your OS's default application.

    This function determines the current operating system and uses the appropriate command
    to open the specified file with the default application. It supports Windows, macOS,
    and Linux, including Windows Subsystem for Linux (WSL).
    """
    path = os.fspath(path)
    if is_wsl():
        exec_cmd(f"cmd.exe /C start '{path}'", check=True)
    elif sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        exec_cmd(f"open {path}", check=True)
    elif sys.platform == "linux":
        exec_cmd(f"xdg-open '{path}'", check=True)
    else:
        raise NotImplementedError(f"Unsupported platform: {sys.platform}")


class PathBase(PathLike):
    def __init__(
        self,
        path: str | PathLike,
        *,
        abs: bool = False,
    ) -> None:
        """
        Initialize a PathBase object.

        Args:
            path (str | PathLike): The path.
            abs (bool): Whether to use the absolute path.
        """
        self.path = os.fspath(path).replace("\\", SEP).replace("/", SEP)
        if abs:
            self.path = os.path.abspath(self.path)

    def __fspath__(self) -> str:
        return self.path

    def __str__(self) -> str:
        return self.path

    def resolve(self, strict: bool = False) -> PathBase:
        """
        Make the path absolute, resolving any symlinks.

        Args:
            strict: If True and path doesn't exist, raises FileNotFoundError. Defaults to False.

        Returns:
            PathBase: The object with resolved path.
        """
        self.path = os.path.realpath(self.path)
        if strict and not self.exists:
            raise FileNotFoundError(f"No such file: '{self.path}'")
        return self

    @property
    def nodes(self) -> list[str]:
        """The path as a list of nodes."""
        return self.abspath.split(SEP)

    @property
    def created(self) -> float:
        """The time when the path was created as a UNIX timestamp."""
        return os.path.getctime(self.path)

    @property
    def modified(self) -> float:
        """The time when the path was last modified as a UNIX timestamp."""
        return os.path.getmtime(self.path)

    @property
    def accessed(self) -> float:
        """The time when the path was last accessed as a UNIX timestamp."""
        return os.path.getatime(self.path)

    ctime = created
    mtime = modified
    atime = accessed

    @property
    def basename(self) -> str:
        """The base name of the path (without the parent directory)."""
        return os.path.basename(self.path)

    @property
    def abspath(self) -> str:
        """The absolute path."""
        return os.path.abspath(self.path)

    @property
    def parents(self) -> tuple[Directory, ...]:
        """All parent directories from immediate parent to root."""
        result: list[Directory] = []
        current = os.path.dirname(os.path.abspath(self.path))
        while current:
            result.append(Directory(current))
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return tuple(result)

    @property
    def is_absolute(self) -> bool:
        """Whether the path is absolute."""
        return os.path.isabs(self.path)

    @property
    def is_symlink(self) -> bool:
        """Whether the path is a symbolic link."""
        return os.path.islink(self.path)

    def rename(self, name: str) -> Self:
        """
        Rename the path.

        Args:
            name (str): The new name.
        """
        new_path = os.path.join(self.parent.path, name)
        os.rename(self.path, new_path)
        self.path = new_path
        return self

    def chmod(self, mode: int) -> Self:
        """
        Change the path's permissions.

        Args:
            mode (int): The new permissions mode.
        """
        os.chmod(self.path, mode)
        return self

    def chown(self, user: str, group: str) -> Self:
        """
        Change the path's owner and group.

        Args:
            user (str): The new owner.
            group (str): The new group.
        """
        shutil.chown(self.path, user, group)
        return self

    def should_exist(self) -> Self:
        """Raise FileNotFoundError if the path does not exist."""
        if not self.exists:
            raise FileNotFoundError(f"No such path: '{self.path}'")
        return self

    def should_not_exist(self) -> Self:
        """Raise FileExistsError if the path exists."""
        if self.exists:
            raise FileExistsError(f"Path already exists: '{self.path}'")
        return self

    def to_path(self) -> Path:
        """
        Convert to pathlib.Path.

        Returns:
            Path: The pathlib.Path object.
        """
        return Path(self.path)

    def to_str(self) -> str:
        """
        Convert to string.

        Returns:
            str: The path as a string.
        """
        return str(self)

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        """
        Return the stat info for this path.

        Args:
            follow_symlinks: If True, follow symlinks. If False, return info about the link itself.

        Returns:
            os.stat_result: The stat information.
        """
        return os.stat(self.path, follow_symlinks=follow_symlinks)

    def relative_to(self, other: str | PathBase) -> str:
        """
        Make this path relative to another path.

        Args:
            other: The base path to make this path relative to.

        Returns:
            str: The relative path.

        Raises:
            ValueError: If this path is not relative to the other path.
        """
        if isinstance(other, PathBase):
            other = other.path
        other = os.path.abspath(other)
        self_abs = os.path.abspath(self.path)
        if not self_abs.startswith(other.rstrip(SEP) + SEP) and self_abs != other:
            raise ValueError(f"'{self.path}' is not relative to '{other}'")
        return os.path.relpath(self_abs, other)

    def expanduser(self) -> PathBase:
        """
        Expand ~ and ~user constructs in the path.

        Returns:
            PathBase: The object with the expanded path.
        """
        self.path = os.path.expanduser(self.path)
        return self

    def as_posix(self) -> str:
        """Return the path with forward slashes."""
        return self.path.replace("\\", "/")

    def as_uri(self) -> str:
        """
        Return the path as a file URI.

        Returns:
            str: The file URI (e.g., 'file:///path/to/file').

        Raises:
            ValueError: If the path is not absolute.
        """
        if not self.is_absolute:
            raise ValueError("relative path can't be expressed as a file URI")
        return "file://" + pathname2url(os.path.abspath(self.path))

    def match(self, pattern: str) -> bool:
        """
        Check if the path matches the given glob pattern.

        Args:
            pattern: A glob pattern to match against.

        Returns:
            bool: True if the path matches the pattern.
        """
        return fnmatch.fnmatch(self.basename, pattern)

    def with_name(self, name: str) -> PathBase:
        """Return a new path with the name changed."""
        parent = os.path.dirname(self.path)
        if parent:
            return self.__class__(f"{parent}{SEP}{name}")
        return self.__class__(name)

    @property
    def exists(self) -> bool:
        """Check if the path exists."""
        raise NotImplementedError

    @property
    def parent(self) -> Directory:
        """The parent directory."""
        raise NotImplementedError

    @property
    def size(self) -> int:
        raise NotImplementedError

    @property
    def size_readable(self) -> str:
        raise NotImplementedError

    def remove(self) -> Self:
        raise NotImplementedError

    def delete(self) -> Self:
        return self.remove()

    def create(self) -> Self:
        raise NotImplementedError

    def clear(self) -> Self:
        raise NotImplementedError

    def move_to(self, directory: str | Directory | PathLike, *, overwrite: bool = True) -> PathBase:
        """
        Move the path to a new directory.

        Args:
            directory: The destination directory
            overwrite: Whether to overwrite files if they already exist. Defaults to True.

        Returns:
            The updated PathBase object
        """
        raise NotImplementedError

    def copy_to(
        self,
        directory: str | Directory | PathLike,
        *,
        overwrite: bool = True,
        mkdir: bool = False,
    ) -> PathBase:
        """
        Copy the path to a new directory.

        Args:
            directory: The destination directory
            overwrite: Whether to overwrite files if they already exist. Defaults to True.
            mkdir: Whether to create the destination directory if it doesn't exist. Defaults to False.

        Returns:
            The updated PathBase object
        """
        raise NotImplementedError

    if sys.platform != "win32":

        def get_xattr(self, name: str, group: str = "user") -> str:
            """
            Retrieve the value of an extended attribute.

            Args:
                name: The name of the extended attribute.
                group: The group of the extended attribute. Defaults to "user".

            Returns:
                The value of the extended attribute.
            """
            return os.getxattr(self.path, f"{group}.{name}").decode()

        def set_xattr(self, value: str | bytes, name: str, group: str = "user") -> PathBase:
            """
            Set an extended attribute.

            Args:
                value: The value of the extended attribute.
                name: The name of the extended attribute.
                group: The group of the extended attribute. Defaults to "user".
            """
            if isinstance(value, str):
                value = value.encode()
            os.setxattr(self.path, f"{group}.{name}", value)
            return self

        def remove_xattr(self, name: str, group: str = "user") -> PathBase:
            """
            Remove an extended attribute.

            Args:
                name: The name of the extended attribute.
                group: The group of the extended attribute. Defaults to "user".
            """
            os.removexattr(self.path, f"{group}.{name}")
            return self


class File(PathBase):
    def __init__(
        self,
        path: str | PathLike,
        encoding: str = "utf-8",
        *,
        abs: bool = False,
    ) -> None:
        """
        Initialize a File object.

        Args:
            path (str | PathLike): File path.
            encoding (str, optional): The file's encoding.
            abs (bool): Whether to use the absolute path.
        """
        super().__init__(path, abs=abs)
        self.encoding = encoding

    @property
    def exists(self) -> bool:
        """Whether the file exists."""
        return os.path.isfile(self.path)

    @property
    def parent(self) -> Directory:
        """The parent directory."""
        return Directory(os.path.dirname(self.path))

    @property
    def dirname(self) -> str:
        """The file's directory name."""
        return os.path.dirname(self.path)

    @property
    def ext(self) -> str:
        """
        The file's extension (without the dot).
        Returns empty string if the file has no extension.
        """
        if "." in self.basename:
            return self.basename.split(".")[-1]
        return ""

    @property
    def suffix(self) -> str:
        """The file extension WITH the dot (e.g., '.txt'). Empty string if no extension."""
        base = os.path.basename(self.path)
        if "." in base and not base.startswith("."):
            return "." + base.rsplit(".", 1)[-1]
        if base.startswith(".") and base.count(".") > 1:
            return "." + base.rsplit(".", 1)[-1]
        return ""

    @property
    def stem(self) -> str:
        """The file's stem (base name without extension)."""
        base = self.basename
        if "." not in base:
            return base
        return ".".join(base.split(".")[:-1])

    @property
    def size(self) -> int:
        """The file's size in bytes."""
        return os.path.getsize(self.path)

    @property
    def size_readable(self) -> str:
        """The file's size in a human-readable format if readable is set to True."""
        return bytes_readable(self.size)

    def create(self) -> File:
        """Create an empty file if it doesn't exist."""
        if self.exists:
            return self
        open(self.path, "a", encoding=self.encoding).close()
        return self

    def remove(self) -> File:
        """Remove the file."""
        if not self.exists:
            return self
        os.remove(self.path)
        return self

    def clear(self) -> File:
        """Clear the contents of a file if it exists."""
        if not self.exists:
            return self
        open(self.path, "w", encoding=self.encoding).close()
        return self

    def read(self, mode: Literal["r", "rb"] = "r") -> str | bytes:
        """
        Read the contents of a file.

        Args:
            mode: The mode to open the file in. Use 'r' for text, 'rb' for binary.

        Returns:
            str | bytes: The file contents as string (text mode) or bytes (binary mode).
        """
        if mode == "rb":
            with open(self.path, mode) as f:
                return f.read()
        with open(self.path, mode, encoding=self.encoding) as f:
            return f.read()

    def _write(self, data: str | bytes, mode: str, *, newline: bool = True) -> None:
        if "b" in mode:
            with open(self.path, mode) as f:
                f.write(data)
        else:
            with open(self.path, mode, encoding=self.encoding) as f:
                f.write(data)
                if newline:
                    f.write("\n")

    def _write_iter(self, data: Iterable[Any], mode: str, sep: str = "\n") -> None:
        with open(self.path, mode, encoding=self.encoding) as f:
            for entry in data:
                f.write(f"{entry}{sep}")

    def write(
        self,
        data: str | bytes,
        *,
        mode: Literal["w", "wb"] = "w",
        newline: bool = True,
    ) -> File:
        """
        Write data to a file, overwriting any existing data.

        Args:
            data: The data to write.
            mode: The mode to open the file in. Use 'w' for text, 'wb' for binary.
            newline: Whether to add a newline at the end. Ignored in binary mode.

        Returns:
            File: The File object for method chaining.
        """
        self._write(data, mode, newline=newline)
        return self

    def append(
        self,
        data: str | bytes,
        *,
        mode: Literal["a", "ab"] = "a",
        newline: bool = True,
    ) -> File:
        """
        Append data to a file.

        Args:
            data: The data to append.
            mode: The mode to open the file in. Use 'a' for text, 'ab' for binary.
            newline: Whether to add a newline at the end. Ignored in binary mode.

        Returns:
            File: The File object for method chaining.
        """
        self._write(data, mode, newline=newline)
        return self

    def open(self, mode: str = "r", encoding: str | None = None, **kwargs: Any) -> IO:
        """
        Open the file and return a file handle.

        Args:
            mode: The mode to open the file in.
            encoding: The encoding to use. Defaults to self.encoding for text modes.
            **kwargs: Additional arguments passed to the built-in open().

        Returns:
            IO: A file handle.
        """
        if "b" in mode:
            return open(self.path, mode, **kwargs)
        if encoding is None:
            encoding = self.encoding
        return open(self.path, mode, encoding=encoding, **kwargs)

    def write_iter(self, data: Iterable[Any], sep: str = "\n") -> None:
        """
        Write data from an iterable to a file, overwriting any existing data.

        Args:
            data (Iterable): The data to write.
            sep (str, optional): The separator to use between items.
        """
        self._write_iter(data, "w", sep=sep)

    def append_iter(self, data: Iterable[Any], sep: str = "\n") -> None:
        """
        Append data from an iterable to a file.

        Args:
            data (Iterable): The data to append.
            sep (str, optional): The separator to use between items.
        """
        self._write_iter(data, "a", sep=sep)

    def readlines(self) -> list[str]:
        """Equivalent to TextIOWrapper.readlines()"""
        with open(self.path, encoding=self.encoding) as f:
            return f.readlines()

    def splitlines(self) -> list[str]:
        """Equivalent to File.read().splitlines()"""
        return self.read(mode="r").splitlines()  # type:ignore

    def move_to(
        self,
        directory: str | Directory | PathLike,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> File:
        """
        Move the file to a new directory.

        Args:
            directory (str): The destination directory.
            mkdir (bool, optional): Whether to create the directory if it doesn't exist. Defaults to False.
            overwrite (bool, optional): Whether to overwrite the file if it already exists in the destination directory. Defaults to True.
        """
        directory = os.fspath(directory)
        if not os.path.isdir(directory):
            if mkdir:
                os.mkdir(directory)
            else:
                raise FileNotFoundError(f"No such directory: '{directory}'")

        move_path = f"{directory}{SEP}{self.basename}"
        if os.path.exists(move_path) and not overwrite:
            raise FileExistsError(move_path)
        os.rename(self.path, move_path)
        self.path = move_path
        return self

    def copy_to(
        self,
        directory: str | Directory | PathLike,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> File:
        """
        Copy the file to a new directory.

        Args:
            directory (str): The destination directory.
            mkdir (bool, optional): Whether to create the directory if it doesn't exist. Defaults to False.
            overwrite (bool, optional): Whether to overwrite the file if it already exists in the destination directory. Defaults to True.
        """
        directory = os.fspath(directory)
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

    def with_dir(self, directory: str) -> File:
        """
        Change the directory of the file object. This will not move the actual file to that directory.
        Use File.move_to for that.
        """
        self.path = f"{directory}{SEP}{self.basename}"
        return self

    def with_ext(self, ext: str) -> File:
        """
        Change the extension of the file and return the new File object

        Args:
            ext (str): The new extension of the file.

        Returns:
            File: The File object with the new extension.
        """
        if not ext.startswith("."):
            ext = f".{ext}"
        self.path = f"{self.dirname}{SEP}{self.stem}{ext}"
        return self

    def with_suffix(self, suffix: str) -> File:
        """Add a suffix to the file's name and return the new File object."""
        ext = self.ext
        if ext:
            ext = f".{ext}"
        filename = f"{self.stem}{suffix}{ext}"
        self.path = f"{self.dirname}{SEP}{filename}"
        return self

    def with_prefix(self, prefix: str) -> File:
        """Add a prefix to the file's name and return the new File object."""
        ext = self.ext
        if ext:
            ext = f".{ext}"
        filename = f"{prefix}{self.stem}{ext}"
        self.path = f"{self.dirname}{SEP}{filename}"
        return self

    def with_stem(self, stem: str) -> File:
        """Return a new File with the stem changed, keeping the suffix."""
        suffix = self.suffix
        return File(f"{self.dirname}{SEP}{stem}{suffix}", encoding=self.encoding)

    def rename(self, name: str) -> File:
        """Rename the file and return the new File object."""
        new_path = f"{self.dirname}{SEP}{name}"
        os.rename(self.path, new_path)
        self.path = new_path
        return self

    def link(self, target: str, follow_symlinks: bool = True) -> File:
        """Create a hard link to the file."""
        os.link(self.path, target, follow_symlinks=follow_symlinks)
        return self

    def symlink(self, target: str) -> File:
        """Create a symbolic link to the file."""
        os.symlink(self.path, target)
        return self

    @classmethod
    def rand(cls, prefix: str = "file", ext: str = "") -> File:
        """
        Create a new random file with a specified prefix and extension.

        Args:
            prefix (str, optional): The prefix for the file name.
            ext (str, optional): The extension for the file name.

        Returns:
            File: A new File object with a random name.
        """
        return File(rand_filename(prefix, ext))


class Directory(PathBase):
    def __init__(
        self,
        path: str | PathLike,
        *,
        abs: bool = False,
    ) -> None:
        """
        Initialize a Directory object.

        Args:
            path (str | PathLike): Directory path.
            abs (bool): Whether to use the absolute path.
        """
        super().__init__(path, abs=abs)

    def __truediv__(self, name: str) -> Directory:
        return self.directory(name)

    def __floordiv__(self, name: str) -> File:
        return self.file(name)

    @property
    def size(self) -> int:
        """Total size of the directory and all its contents in bytes."""
        return get_dir_size(self.path, readable=False)  # type:ignore

    @property
    def exists(self) -> bool:
        """Check if the directory exists."""
        return os.path.isdir(self.path)

    def create(self, mode: int = 0o777, exist_ok: bool = True) -> Directory:
        """Create directory (including parents)."""
        os.makedirs(self.path, mode=mode, exist_ok=exist_ok)
        return self

    @property
    def parent(self) -> Directory:
        """The parent directory."""
        return Directory(os.path.dirname(self.path))

    @classmethod
    def rand(cls, prefix: str = "dir") -> Directory:
        return Directory(joinpath(os.getcwd(), safe_filename(rand_filename(prefix))))

    def move_to(
        self,
        directory: str | PathLike | Directory,
        *,
        overwrite: bool = True,
    ) -> Directory:
        """
        Move this directory to become a child of the target location.

        Args:
            directory: The destination directory where this directory will be moved
            overwrite: Whether to overwrite if target path already exists. Defaults to True.

        Returns:
            The updated Directory object
        """
        directory = os.fspath(directory)
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Destination directory does not exist: {directory}")

        dest = f"{directory}{SEP}{self.basename}"
        shutil.move(self.path, dest)
        self.path = dest
        return self

    def copy_to(
        self,
        directory: str | PathLike | Directory,
        *,
        overwrite: bool = True,
        mkdir: bool = False,
    ) -> Directory:
        """
        Copy this directory to become a child of the target location.

        Args:
            directory: The destination directory where this directory will be copied
            overwrite: Whether to overwrite if target path already exists. Defaults to True.
            mkdir: Whether to create the destination directory if it doesn't exist. Defaults to False.

        Returns:
            The updated Directory object
        """
        directory = os.fspath(directory)
        if not os.path.exists(directory):
            if mkdir:
                os.makedirs(directory)
            else:
                raise FileNotFoundError(f"Destination directory does not exist: {directory}")

        dest = f"{directory}{SEP}{self.basename}"
        shutil.copytree(self.path, dest)
        self.path = dest
        return self

    def remove(self) -> Directory:
        """Remove the directory and all its contents."""
        if not self.exists:
            return self
        shutil.rmtree(self.path)
        return self

    def yield_files(
        self,
        ext: str | tuple[str, ...] | None = None,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
    ) -> Generator[File, None, None]:
        """
        Yield files in the directory.

        All filter parameters use AND logic - files must match all specified filters.

        Args:
            ext: If provided, only yield files with provided extensions.
            glob: Glob pattern as string or compiled regex from fnmatch.translate().
            regex: Regex pattern as string or compiled re.Pattern.
            recursive: Whether to search recursively.

        Yields:
            Generator[File, None, None]: The files in the directory.
        """
        glob_pattern = re.compile(fnmatch.translate(glob)) if isinstance(glob, str) else glob
        regex_pattern = re.compile(regex) if isinstance(regex, str) else regex
        for file_path in yield_files_in(self.path, ext=ext, recursive=recursive):
            basename = os.path.basename(file_path)
            if glob_pattern and not glob_pattern.match(basename):
                continue
            if regex_pattern and not regex_pattern.search(basename):
                continue
            yield File(file_path)

    def get_files(
        self,
        ext: str | tuple[str, ...] | None = None,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
    ) -> list[File]:
        """
        Get files in the directory.

        All filter parameters use AND logic - files must match all specified filters.

        Args:
            ext: If provided, only yield files with provided extensions.
            glob: Glob pattern as string or compiled regex from fnmatch.translate().
            regex: Regex pattern as string or compiled re.Pattern.
            recursive: Whether to search recursively.

        Returns:
            list[File]: The files in the directory.
        """
        return list(self.yield_files(ext=ext, glob=glob, regex=regex, recursive=recursive))

    def yield_subdirs(
        self,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
    ) -> Generator[Directory, None, None]:
        """
        Yield subdirectories in the directory.

        All filter parameters use AND logic - directories must match all specified filters.

        Args:
            glob: Glob pattern as string or compiled regex from fnmatch.translate().
            regex: Regex pattern as string or compiled re.Pattern.
            recursive: Whether to search recursively.

        Yields:
            Generator[Directory, None, None]: The subdirectories in the directory.
        """
        glob_pattern = re.compile(fnmatch.translate(glob)) if isinstance(glob, str) else glob
        regex_pattern = re.compile(regex) if isinstance(regex, str) else regex
        for dir_path in yield_dirs_in(self.path, recursive=recursive):
            basename = os.path.basename(dir_path)
            if glob_pattern and not glob_pattern.match(basename):
                continue
            if regex_pattern and not regex_pattern.search(basename):
                continue
            yield Directory(dir_path)

    def get_subdirs(
        self,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
    ) -> list[Directory]:
        """
        Get subdirectories in the directory.

        All filter parameters use AND logic - directories must match all specified filters.

        Args:
            glob: Glob pattern as string or compiled regex from fnmatch.translate().
            regex: Regex pattern as string or compiled re.Pattern.
            recursive: Whether to search recursively.

        Returns:
            list[Directory]: The subdirectories in the directory.
        """
        return list(self.yield_subdirs(glob=glob, regex=regex, recursive=recursive))

    def file(self, name: str) -> File:
        return File(joinpath(self.path, safe_filename(name)))

    def directory(self, name: str) -> Directory:
        return Directory(joinpath(self.path, safe_filename(name)))

    @classmethod
    def home(cls) -> Directory:
        return Directory(HOME)

    @classmethod
    def cwd(cls) -> Directory:
        return Directory(os.getcwd())


class EXT:
    AUDIO = (
        ".mp3",
        ".aac",
        ".ogg",
        ".flac",
        ".wav",
        ".aiff",
        ".dsd",
        ".pcm",
    )
    IMAGE = (
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
    VIDEO = (
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


__all__ = [
    "EXT",
    "File",
    "Directory",
    "PathLike",
    "mkdir",
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
    "mkdirs",
    "yield_files_in",
    "get_files_in",
    "yield_dirs_in",
    "get_dirs_in",
    "ensure_paths_exist",
    "exec_cmd",
    "SEP",
    "HOME",
    "abspath",
    "basename",
    "dirname",
    "joinpath",
    "splitpath",
    "start_file",
    "read_piped",
    "isdir",
    "isfile",
    "islink",
    "exists",
    "stat",
    "link",
    "getcwd",
    "chdir",
    "chmod",
    "remove",
    "rename",
    "copy",
    "move",
    "chown",
]
