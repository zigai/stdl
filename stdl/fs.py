from __future__ import annotations

import fnmatch
import importlib
import inspect
import json
import math
import os
import pickle
import platform
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import time
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
    Generator,
    Iterable,
    Iterator,
)
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from os import PathLike
from pathlib import Path
from queue import Queue
from types import TracebackType
from typing import (
    IO,
    Any,
    Generic,
    Literal,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)

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

P = ParamSpec("P")
HandleDataT = TypeVar("HandleDataT", str, bytes)
T = TypeVar("T")
ResultT = TypeVar("ResultT")

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
YamlValue: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    | list["YamlValue"]
    | tuple["YamlValue", ...]
    | dict["YamlValue", "YamlValue"]
)
OpenKwarg: TypeAlias = str | int | bool | None | Callable[[str, int], int]
DirectoryIdentity: TypeAlias = tuple[Literal["inode"], int, int] | tuple[Literal["path"], str]


class AsyncLock(Protocol):
    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...


class AsyncSemaphore(Protocol):
    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...


class CancelScope(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...


class TaskGroupCancelScope(Protocol):
    def cancel(self) -> None: ...


class AnyIOTaskGroup(Protocol):
    cancel_scope: TaskGroupCancelScope

    def start_soon(
        self,
        func: Callable[..., Awaitable[object]],
        *args: object,
        **kwargs: object,
    ) -> None: ...


class AnyIOTaskGroupContext(Protocol):
    async def __aenter__(self) -> AnyIOTaskGroup: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...


class AnyIOToThread(Protocol):
    async def run_sync(self, func: Callable[[], T], /) -> T: ...


class AsyncFileLike(Protocol[HandleDataT]):
    def read(self, size: int = -1) -> HandleDataT | Awaitable[HandleDataT]: ...

    def readline(self, size: int = -1) -> HandleDataT | Awaitable[HandleDataT]: ...

    def readlines(self, hint: int = -1) -> list[HandleDataT] | Awaitable[list[HandleDataT]]: ...

    def write(self, data: HandleDataT) -> int | Awaitable[int]: ...

    def writelines(self, lines: Iterable[HandleDataT]) -> None | Awaitable[None]: ...

    def flush(self) -> None | Awaitable[None]: ...

    def seek(self, offset: int, whence: int = 0) -> int | Awaitable[int]: ...

    def tell(self) -> int | Awaitable[int]: ...

    @overload
    def truncate(self) -> int | Awaitable[int]: ...

    @overload
    def truncate(self, size: int) -> int | Awaitable[int]: ...

    def close(self) -> None | Awaitable[None]: ...


class AnyIOModule(Protocol):
    to_thread: AnyIOToThread
    CancelScope: Callable[..., CancelScope]
    Lock: Callable[[], AsyncLock]
    Semaphore: Callable[[int], AsyncSemaphore]
    create_task_group: Callable[[], AnyIOTaskGroupContext]
    get_cancelled_exc_class: Callable[[], type[BaseException]]

    async def open_file(
        self,
        file: str | PathLike[str],
        mode: str = "r",
        encoding: str | None = None,
        **kwargs: OpenKwarg,
    ) -> AsyncFileLike[str] | AsyncFileLike[bytes]: ...


@dataclass
class LimitedMapState(Generic[T, ResultT]):
    items: list[T]
    results: list[ResultT | None]
    lock: AsyncLock
    next_index: int = 0
    first_error: Exception | None = None


_ANYIO: AnyIOModule | None = None
_ITERATION_SENTINEL = object()


def _load_anyio() -> AnyIOModule:
    global _ANYIO

    if _ANYIO is not None:
        return _ANYIO

    try:
        _ANYIO = cast(AnyIOModule, importlib.import_module("anyio"))
    except ImportError as exc:
        raise ImportError(
            "Async stdl.fs APIs require AnyIO. Install stdl with the async extra: "
            "`pip install 'stdl[async]'`."
        ) from exc

    return _ANYIO


async def run_fs_sync(func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> T:
    anyio = _load_anyio()
    return await anyio.to_thread.run_sync(partial(func, *args, **kwargs))


async def _run_fs_sync_shielded(func: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> T:
    anyio = _load_anyio()
    with anyio.CancelScope(shield=True):
        return await run_fs_sync(func, *args, **kwargs)


def _next_or_sentinel(iterator: Iterator[T]) -> T | object:
    return next(iterator, _ITERATION_SENTINEL)


async def iterate_fs(iterable_factory: Callable[[], Iterable[T]]) -> AsyncGenerator[T, None]:
    _load_anyio()
    iterator = iter(iterable_factory())

    try:
        while True:
            item = await run_fs_sync(_next_or_sentinel, iterator)
            if item is _ITERATION_SENTINEL:
                return
            yield cast(T, item)
    finally:
        close = getattr(iterator, "close", None)
        if close is not None:
            await _run_fs_sync_shielded(close)


async def _map_limited_async(
    items: Iterable[T],
    func: Callable[[T], Awaitable[ResultT]],
    *,
    concurrency: int = 8,
) -> list[ResultT]:
    if concurrency < 1:
        raise ValueError("concurrency must be >= 1")

    item_list = list(items)
    if not item_list:
        return []

    anyio = _load_anyio()
    state = LimitedMapState(
        items=item_list,
        results=[None] * len(item_list),
        lock=anyio.Lock(),
    )
    cancelled_exc_class = anyio.get_cancelled_exc_class()

    async with anyio.create_task_group() as task_group:
        for _ in range(min(concurrency, len(item_list))):
            task_group.start_soon(
                _run_limited_map_worker,
                state,
                func,
                cancelled_exc_class,
                task_group,
            )

    if state.first_error is not None:
        raise state.first_error

    return [cast(ResultT, result) for result in state.results]


async def _claim_limited_map_item(state: LimitedMapState[T, ResultT]) -> tuple[int, T] | None:
    async with state.lock:
        if state.first_error is not None or state.next_index >= len(state.items):
            return None
        index = state.next_index
        state.next_index += 1
        return index, state.items[index]


async def _record_limited_map_error(
    state: LimitedMapState[T, ResultT],
    task_group: AnyIOTaskGroup,
    exc: Exception,
) -> None:
    async with state.lock:
        if state.first_error is None:
            state.first_error = exc
            task_group.cancel_scope.cancel()


async def _run_limited_map_worker(
    state: LimitedMapState[T, ResultT],
    func: Callable[[T], Awaitable[ResultT]],
    cancelled_exc_class: type[BaseException],
    task_group: AnyIOTaskGroup,
) -> None:
    while True:
        next_item = await _claim_limited_map_item(state)
        if next_item is None:
            return
        index, item = next_item

        try:
            state.results[index] = await func(item)
        except cancelled_exc_class:
            raise
        except Exception as exc:  # noqa: BLE001 - normalize worker failures
            await _record_limited_map_error(state, task_group, exc)
            return


class AsyncFileHandle(Generic[HandleDataT]):
    def __init__(self, handle: AsyncFileLike[HandleDataT]) -> None:
        self._handle: AsyncFileLike[HandleDataT] = handle
        self._lock: AsyncLock | None = None

    def _get_lock(self) -> AsyncLock:
        if self._lock is None:
            self._lock = _load_anyio().Lock()
        return self._lock

    async def __aenter__(self) -> AsyncFileHandle[HandleDataT]:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        await self.close()
        return None

    def __aiter__(self) -> AsyncIterator[HandleDataT]:
        return self.iter_lines()

    async def _resolve_result(self, result: ResultT | Awaitable[ResultT]) -> ResultT:
        if inspect.isawaitable(result):
            return await cast(Awaitable[ResultT], result)
        return result

    async def read(self, size: int = -1) -> HandleDataT:
        async with self._get_lock():
            return await self._resolve_result(self._handle.read(size))

    async def readline(self, size: int = -1) -> HandleDataT:
        async with self._get_lock():
            if size == -1:
                return await self._resolve_result(self._handle.readline())
            return await self._resolve_result(self._handle.readline(size))

    async def readlines(self, hint: int = -1) -> list[HandleDataT]:
        async with self._get_lock():
            if hint == -1:
                return await self._resolve_result(self._handle.readlines())
            return await self._resolve_result(self._handle.readlines(hint))

    async def write(self, data: HandleDataT) -> int:
        async with self._get_lock():
            return await self._resolve_result(self._handle.write(data))

    async def writelines(self, lines: Iterable[HandleDataT]) -> None:
        async with self._get_lock():
            await self._resolve_result(self._handle.writelines(lines))

    async def flush(self) -> None:
        async with self._get_lock():
            await self._resolve_result(self._handle.flush())

    async def seek(self, offset: int, whence: int = 0) -> int:
        async with self._get_lock():
            return await self._resolve_result(self._handle.seek(offset, whence))

    async def tell(self) -> int:
        async with self._get_lock():
            return await self._resolve_result(self._handle.tell())

    async def truncate(self, size: int | None = None) -> int:
        truncate = self._handle.truncate
        if size is None:
            async with self._get_lock():
                return await self._resolve_result(truncate())
        async with self._get_lock():
            return await self._resolve_result(truncate(size))

    async def close(self) -> None:
        anyio = _load_anyio()
        async with self._get_lock():
            with anyio.CancelScope(shield=True):
                await self._resolve_result(self._handle.close())

    async def iter_lines(self) -> AsyncGenerator[HandleDataT, None]:
        while True:
            line = await self.readline()
            if line in ("", b""):
                break
            yield line

    async def iter_chunks(self, size: int = 1024 * 1024) -> AsyncGenerator[HandleDataT, None]:
        while True:
            chunk = await self.read(size)
            if chunk in ("", b""):
                break
            yield chunk


def _iter_file_paths(
    directory: str | PathLike[str], *, recursive: bool
) -> Generator[str, None, None]:
    if not recursive:
        with os.scandir(directory) as entries:
            for entry in sorted(entries, key=lambda entry: os.fspath(entry.name)):
                if entry.is_file():
                    yield entry.path
        return

    visited = {_dir_identity(os.fspath(directory))}
    queue: Queue[str | PathLike[str]] = Queue()
    queue.put(directory)
    while not queue.empty():
        next_dir = queue.get()
        with os.scandir(next_dir) as entries:
            for entry in sorted(entries, key=lambda entry: os.fspath(entry.name)):
                if entry.is_dir():
                    entry_identity = _entry_dir_identity(entry)
                    if entry_identity in visited:
                        continue
                    visited.add(entry_identity)
                    queue.put(entry.path)
                elif entry.is_file():
                    yield entry.path


def _normalized_ext(ext: str | tuple[str, ...] | None) -> str | tuple[str, ...] | None:
    if ext is None:
        return None
    if isinstance(ext, str):
        return _normalize_single_ext(ext)
    return tuple(_normalize_single_ext(extension) for extension in ext)


def _normalize_single_ext(ext: str) -> str:
    normalized = ext.lower()
    if normalized and not normalized.startswith("."):
        return f".{normalized}"
    return normalized


def _remove_existing_path(path: str) -> None:
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def _comparison_path(path: str | PathLike) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(path))))


def _real_comparison_path(path: str | PathLike) -> str:
    return os.path.normcase(os.path.realpath(os.fspath(path)))


def _is_same_filesystem_path(path: str | PathLike, other: str | PathLike) -> bool:
    return _comparison_path(path) == _comparison_path(other) or (
        _real_comparison_path(path) == _real_comparison_path(other)
    )


def _ensure_directory_target_is_not_inside_source(source_path: str, destination_path: str) -> None:
    source = _comparison_path(source_path)
    destination = _comparison_path(destination_path)
    real_source = _real_comparison_path(source_path)
    real_destination = _real_comparison_path(destination_path)
    if (destination != source and destination.startswith(source + SEP)) or (
        real_destination != real_source and real_destination.startswith(real_source + SEP)
    ):
        raise ValueError("Cannot copy or move a directory into itself")


def _ensure_expected_destination_type(
    path: str, expected_type: Literal["file", "directory"]
) -> None:
    if expected_type == "file" and os.path.isdir(path) and not os.path.islink(path):
        raise IsADirectoryError(path)
    if expected_type == "directory" and not os.path.isdir(path):
        raise NotADirectoryError(path)


def _directory_identity_from_stat(path: str, stat_result: os.stat_result) -> DirectoryIdentity:
    if stat_result.st_ino:
        return "inode", stat_result.st_dev, stat_result.st_ino
    return "path", _real_comparison_path(path)


def _dir_identity(path: str) -> DirectoryIdentity:
    stat_result = os.stat(path, follow_symlinks=True)
    return _directory_identity_from_stat(path, stat_result)


def _entry_dir_identity(entry: os.DirEntry[str]) -> DirectoryIdentity:
    return _directory_identity_from_stat(entry.path, entry.stat(follow_symlinks=True))


def _symlink_source_path(source_path: str, target_path: str) -> str:
    if os.path.isabs(source_path):
        return source_path

    target_dir = os.path.dirname(os.path.abspath(target_path))
    return os.path.relpath(os.path.abspath(source_path), target_dir)


def _prepare_destination_path(
    path: str,
    *,
    mkdir: bool,
    overwrite: bool,
    source_path: str | None = None,
    expected_type: Literal["file", "directory"] | None = None,
    remove_existing: bool = True,
) -> bool:
    if source_path is not None and _is_same_filesystem_path(source_path, path):
        return True

    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        if mkdir:
            os.makedirs(parent, exist_ok=True)
        else:
            raise FileNotFoundError(f"No such directory: '{parent}'")

    if os.path.exists(path):
        if expected_type is not None:
            _ensure_expected_destination_type(path, expected_type)
        if not overwrite:
            raise FileExistsError(path)
        if remove_existing:
            _remove_existing_path(path)

    return False


def _copy_file_to_destination(source_path: str, destination_path: str) -> None:
    temp_path = os.path.join(
        os.path.dirname(destination_path),
        f".{os.path.basename(destination_path)}.tmp-{secrets.token_hex(8)}",
    )
    try:
        shutil.copy2(source_path, temp_path)
        os.replace(temp_path, destination_path)
    except Exception:
        if os.path.exists(temp_path):
            _remove_existing_path(temp_path)
        raise


def _copy_directory_to_destination(
    source_path: str, destination_path: str, *, overwrite: bool
) -> None:
    temp_path = f"{destination_path}.tmp-{secrets.token_hex(8)}"
    try:
        shutil.copytree(source_path, temp_path)
        _replace_temp_path(temp_path, destination_path, overwrite=overwrite)
    except Exception:
        if os.path.exists(temp_path):
            _remove_existing_path(temp_path)
        raise


def _replace_temp_path(temp_path: str, destination_path: str, *, overwrite: bool) -> None:
    if os.path.exists(destination_path):
        if not overwrite:
            raise FileExistsError(destination_path)
        _remove_existing_path(destination_path)
    os.replace(temp_path, destination_path)


def pickle_load(filepath: str | PathLike) -> object:
    """Loads a pickled file."""
    with open(filepath, "rb") as f:
        return pickle.load(f)  # noqa: S301


async def pickle_load_async(filepath: str | PathLike) -> object:
    """Async version of pickle_load()."""
    return await run_fs_sync(pickle_load, filepath)


def pickle_dump(data: object, filepath: str | PathLike) -> None:
    """Dumps an object to the specified filepath."""
    with open(filepath, "wb") as f:
        pickle.dump(data, f)


async def pickle_dump_async(data: object, filepath: str | PathLike) -> None:
    """Async version of pickle_dump()."""
    await _run_fs_sync_shielded(pickle_dump, data, filepath)


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


async def json_load_async(
    path: str | PathLike, encoding: str = "utf-8"
) -> dict[Any, Any] | list[dict[Any, Any]]:
    """Async version of json_load()."""
    return await run_fs_sync(json_load, path, encoding)


def json_append(
    data: JsonValue,
    filepath: str | PathLike,
    encoding: str = "utf-8",
    default: Callable[[object], str] = str,
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


async def json_append_async(
    data: JsonValue,
    filepath: str | PathLike,
    encoding: str = "utf-8",
    default: Callable[[object], str] = str,
    indent: int = 4,
) -> None:
    """Async version of json_append()."""
    await _run_fs_sync_shielded(
        json_append, data, filepath, encoding=encoding, default=default, indent=indent
    )


def json_dump(
    data: JsonValue,
    path: str | PathLike,
    encoding: str = "utf-8",
    default: Callable[[object], str] = str,
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


async def json_dump_async(
    data: JsonValue,
    path: str | PathLike,
    encoding: str = "utf-8",
    default: Callable[[object], str] = str,
    indent: int = 4,
) -> None:
    """Async version of json_dump()."""
    await _run_fs_sync_shielded(
        json_dump, data, path, encoding=encoding, default=default, indent=indent
    )


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


async def yaml_load_async(
    path: str | PathLike, encoding: str = "utf-8"
) -> dict[Any, Any] | list[dict[Any, Any]]:
    """Async version of yaml_load()."""
    return await run_fs_sync(yaml_load, path, encoding)


def yaml_dump(data: YamlValue, path: str | PathLike, encoding: str = "utf-8") -> None:
    """
    Dumps data to a YAML file.

    Args:
        data: data to be dumped
        path (Pathlike): path to the output file
        encoding (str): encoding of the output file. Default: 'utf-8'
    """
    with open(path, "w", encoding=encoding) as f:
        yaml.safe_dump(data, f)


async def yaml_dump_async(data: YamlValue, path: str | PathLike, encoding: str = "utf-8") -> None:
    """Async version of yaml_dump()."""
    await _run_fs_sync_shielded(yaml_dump, data, path, encoding)


def toml_load(path: str | PathLike, encoding: str = "utf-8") -> dict[str, Any]:
    with open(path, encoding=encoding) as f:
        return toml.load(f)


async def toml_load_async(path: str | PathLike, encoding: str = "utf-8") -> dict[str, Any]:
    """Async version of toml_load()."""
    return await run_fs_sync(toml_load, path, encoding)


def toml_dump(data: dict[str, Any], path: str | PathLike, encoding: str = "utf-8") -> None:
    with open(path, "w", encoding=encoding) as f:
        toml.dump(data, f)


async def toml_dump_async(
    data: dict[str, Any], path: str | PathLike, encoding: str = "utf-8"
) -> None:
    """Async version of toml_dump()."""
    await _run_fs_sync_shielded(toml_dump, data, path, encoding)


@overload
def get_dir_size(directory: str | PathLike, *, readable: Literal[False] = False) -> int: ...


@overload
def get_dir_size(directory: str | PathLike, *, readable: Literal[True]) -> str: ...


def get_dir_size(directory: str | PathLike, *, readable: bool = False) -> str | int:
    """
    Calculates total size of a directory.

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
    Moves files to a specified directory.

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
    num = str(secrets.randbelow(9_000_000_000) + 1_000_000_000).zfill(10)
    if include_datetime:
        creation_time = (
            datetime.now(tz=timezone.utc).astimezone().strftime("%Y-%m-%d.%H-%M-%S-%f")[:-3]
        )
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
    i = math.floor(math.log(size_bytes, 1024))
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
    abs: bool = True,  # noqa: A002
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
    normalized_ext = _normalized_ext(ext)

    for file_path in _iter_file_paths(directory, recursive=recursive):
        if normalized_ext is not None and not file_path.lower().endswith(normalized_ext):
            continue
        yield os.path.abspath(file_path) if abs else file_path


def get_files_in(
    directory: str | PathLike,
    ext: str | tuple[str, ...] | None = None,
    *,
    recursive: bool = True,
    abs: bool = True,  # noqa: A002
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
    directory: str | PathLike,
    *,
    recursive: bool = True,
    abs: bool = True,  # noqa: A002
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
    visited = {_dir_identity(os.fspath(directory))}
    queue: Queue[str | PathLike[str]] = Queue()
    queue.put(directory)
    while not queue.empty():
        next_dir = queue.get()
        with os.scandir(next_dir) as entries:
            for entry in sorted(entries, key=lambda entry: os.fspath(entry.name)):
                if entry.is_dir():
                    entry_identity = _entry_dir_identity(entry)
                    if recursive and entry_identity not in visited:
                        visited.add(entry_identity)
                        queue.put(entry.path)
                    yield os.path.abspath(entry.path) if abs else entry.path


def get_dirs_in(
    directory: str | PathLike,
    *,
    recursive: bool = True,
    abs: bool = True,  # noqa: A002
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
        stdout: str | bytes | None = None,
        stderr: str | bytes | None = None,
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
    timeout: float | None = None,
    shell: bool = False,
    capture_output: bool = True,
    check: bool = False,
    cwd: str | None = None,
    stdin: IO | None = None,
    stdout: IO | None = None,
    stderr: IO | None = None,
    input: str | None | bytes = None,
    env: dict[str, str] | None = None,
    text: bool = True,
    *args: object,
    **kwargs: object,
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

    result = subprocess.run(  # noqa: S603
        cmd,
        *args,
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
        os.startfile(path)  # noqa: S606
    elif sys.platform == "darwin":
        exec_cmd(f"open {path}", check=True)
    elif sys.platform == "linux":
        exec_cmd(f"xdg-open '{path}'", check=True)
    else:
        raise NotImplementedError(f"Unsupported platform: {sys.platform}")


class PathBase(PathLike):
    """
    Base class for typed filesystem paths.

    Return-value policy:
    - methods that keep the same lexical path return `self`
    - methods that point at a different path return a new path object
    - methods that create a second path return the created path object
    """

    def __init__(
        self,
        path: str | PathLike,
        *,
        abs: bool = False,  # noqa: A002
    ) -> None:
        """
        Initialize a PathBase object.

        Args:
            path (str | PathLike): The path.
            abs (bool): Whether to use the absolute path.
        """
        self._path = os.fspath(path).replace("\\", SEP).replace("/", SEP)
        if abs:
            self._path = os.path.abspath(self._path)

    @property
    def path(self) -> str:
        """The stored path string."""
        return self._path

    def _clone_with_path(self, path: str | PathLike, *, abs: bool = False) -> Self:  # noqa: A002
        return self.__class__(path, abs=abs)

    def _comparison_path(self) -> str:
        return os.path.normcase(os.path.normpath(self.path))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PathBase):
            return NotImplemented
        return type(self) is type(other) and self._comparison_path() == other._comparison_path()

    def __hash__(self) -> int:
        return hash((type(self), self._comparison_path()))

    def __fspath__(self) -> str:
        return self.path

    def __str__(self) -> str:
        return self.path

    def resolve(self, strict: bool = False) -> Self:
        """
        Make the path absolute, resolving any symlinks.

        Args:
            strict: If True and path doesn't exist, raises FileNotFoundError. Defaults to False.

        Returns:
            The resolved path object.
        """
        resolved_path = os.path.realpath(self.path)
        if strict and not os.path.exists(resolved_path):
            raise FileNotFoundError(f"No such file: '{resolved_path}'")
        return self._clone_with_path(resolved_path)

    async def resolve_async(self, strict: bool = False) -> Self:
        """Async version of resolve()."""
        return await run_fs_sync(self.resolve, strict=strict)

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

    async def created_async(self) -> float:
        """Async version of created."""
        return await run_fs_sync(lambda: self.created)

    async def modified_async(self) -> float:
        """Async version of modified."""
        return await run_fs_sync(lambda: self.modified)

    async def accessed_async(self) -> float:
        """Async version of accessed."""
        return await run_fs_sync(lambda: self.accessed)

    async def ctime_async(self) -> float:
        """Async version of ctime."""
        return await self.created_async()

    async def mtime_async(self) -> float:
        """Async version of mtime."""
        return await self.modified_async()

    async def atime_async(self) -> float:
        """Async version of atime."""
        return await self.accessed_async()

    async def is_symlink_async(self) -> bool:
        """Async version of is_symlink."""
        return await run_fs_sync(lambda: self.is_symlink)

    def rename(self, name: str) -> Self:
        """
        Rename the path.

        Args:
            name (str): The new name.
        """
        new_path = os.path.join(self.parent.path, name)
        os.rename(self.path, new_path)
        return self._clone_with_path(new_path)

    async def rename_async(self, name: str) -> Self:
        """Async version of rename()."""
        return await _run_fs_sync_shielded(self.rename, name)

    def chmod(self, mode: int) -> Self:
        """
        Change the path's permissions.

        Args:
            mode (int): The new permissions mode.
        """
        os.chmod(self.path, mode)
        return self

    async def chmod_async(self, mode: int) -> Self:
        """Async version of chmod()."""
        return await _run_fs_sync_shielded(self.chmod, mode)

    def chown(self, user: str, group: str) -> Self:
        """
        Change the path's owner and group.

        Args:
            user (str): The new owner.
            group (str): The new group.
        """
        shutil.chown(self.path, user, group)
        return self

    async def chown_async(self, user: str, group: str) -> Self:
        """Async version of chown()."""
        return await _run_fs_sync_shielded(self.chown, user, group)

    def should_exist(self) -> Self:
        """Raise FileNotFoundError if the path does not exist."""
        if not self.exists:
            raise FileNotFoundError(f"No such path: '{self.path}'")
        return self

    async def should_exist_async(self) -> Self:
        """Async version of should_exist()."""
        return await run_fs_sync(self.should_exist)

    def should_not_exist(self) -> Self:
        """Raise FileExistsError if the path exists."""
        if self.exists:
            raise FileExistsError(f"Path already exists: '{self.path}'")
        return self

    async def should_not_exist_async(self) -> Self:
        """Async version of should_not_exist()."""
        return await run_fs_sync(self.should_not_exist)

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

    async def stat_async(self, *, follow_symlinks: bool = True) -> os.stat_result:
        """Async version of stat()."""
        return await run_fs_sync(self.stat, follow_symlinks=follow_symlinks)

    def samefile(self, other: str | PathLike | PathBase) -> bool:
        """Return True if both paths reference the same filesystem entry."""
        if isinstance(other, PathBase):
            other = other.path
        return os.path.samefile(self.path, os.fspath(other))

    async def samefile_async(self, other: str | PathLike | PathBase) -> bool:
        """Async version of samefile()."""
        return await run_fs_sync(self.samefile, other)

    def readlink(self) -> str:
        """Return the path that this symbolic link points to."""
        return os.readlink(self.path)

    async def readlink_async(self) -> str:
        """Async version of readlink()."""
        return await run_fs_sync(self.readlink)

    def owner(self) -> str:
        """Return the filesystem owner name."""
        if sys.platform == "win32":
            raise NotImplementedError("owner() is not supported on Windows")
        import pwd

        return pwd.getpwuid(self.stat().st_uid).pw_name

    async def owner_async(self) -> str:
        """Async version of owner()."""
        return await run_fs_sync(self.owner)

    def group(self) -> str:
        """Return the filesystem group name."""
        if sys.platform == "win32":
            raise NotImplementedError("group() is not supported on Windows")
        import grp

        return grp.getgrgid(self.stat().st_gid).gr_name

    async def group_async(self) -> str:
        """Async version of group()."""
        return await run_fs_sync(self.group)

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

    def expanduser(self) -> Self:
        """
        Expand ~ and ~user constructs in the path.

        Returns:
            The path object with the expanded path.
        """
        return self._clone_with_path(os.path.expanduser(self.path))

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

    def with_name(self, name: str) -> Self:
        """Return a new path with the name changed."""
        parent = os.path.dirname(self.path)
        if parent:
            return self._clone_with_path(os.path.join(parent, name))
        return self._clone_with_path(name)

    @property
    def exists(self) -> bool:
        """Check if the path exists."""
        raise NotImplementedError

    async def exists_async(self) -> bool:
        """Async version of exists."""
        return await run_fs_sync(lambda: self.exists)

    @property
    def parent(self) -> Directory:
        """The parent directory."""
        raise NotImplementedError

    @property
    def size(self) -> int:
        raise NotImplementedError

    async def size_async(self) -> int:
        """Async version of size."""
        return await run_fs_sync(lambda: self.size)

    @property
    def size_readable(self) -> str:
        raise NotImplementedError

    async def size_readable_async(self) -> str:
        """Async version of size_readable."""
        return await run_fs_sync(lambda: self.size_readable)

    def remove(self) -> Self:
        raise NotImplementedError

    async def remove_async(self) -> Self:
        """Async version of remove()."""
        return await _run_fs_sync_shielded(self.remove)

    def delete(self) -> Self:
        return self.remove()

    async def delete_async(self) -> Self:
        """Async version of delete()."""
        return await self.remove_async()

    def create(self) -> Self:
        raise NotImplementedError

    def clear(self) -> Self:
        raise NotImplementedError

    def move_to(self, target: PathBase, *, mkdir: bool = False, overwrite: bool = True) -> Self:
        """
        Move the path to a new target.

        Args:
            target: The destination path object.
            mkdir: Whether to create missing parent directories. Defaults to False.
            overwrite: Whether to overwrite files if they already exist. Defaults to True.

        Returns:
            A new path object pointing at the moved path.
        """
        raise NotImplementedError

    def copy_to(
        self,
        target: PathBase,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> Self:
        """
        Copy the path to a new target.

        Args:
            target: The destination path object.
            mkdir: Whether to create missing parent directories. Defaults to False.
            overwrite: Whether to overwrite files if they already exist. Defaults to True.

        Returns:
            A new path object pointing at the copied path.
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

        async def get_xattr_async(self, name: str, group: str = "user") -> str:
            """Async version of get_xattr()."""
            return await run_fs_sync(self.get_xattr, name, group)

        def set_xattr(self, value: str | bytes, name: str, group: str = "user") -> Self:
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

        async def set_xattr_async(self, value: str | bytes, name: str, group: str = "user") -> Self:
            """Async version of set_xattr()."""
            return await _run_fs_sync_shielded(self.set_xattr, value, name, group)

        def remove_xattr(self, name: str, group: str = "user") -> Self:
            """
            Remove an extended attribute.

            Args:
                name: The name of the extended attribute.
                group: The group of the extended attribute. Defaults to "user".
            """
            os.removexattr(self.path, f"{group}.{name}")
            return self

        async def remove_xattr_async(self, name: str, group: str = "user") -> Self:
            """Async version of remove_xattr()."""
            return await _run_fs_sync_shielded(self.remove_xattr, name, group)


class File(PathBase):
    def __init__(
        self,
        path: str | PathLike,
        encoding: str = "utf-8",
        *,
        abs: bool = False,  # noqa: A002
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

    def _clone_with_path(self, path: str | PathLike, *, abs: bool = False) -> File:  # noqa: A002
        return File(path, encoding=self.encoding, abs=abs)

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
        suffix = self.suffix
        return suffix[1:] if suffix else ""

    @property
    def suffix(self) -> str:
        """The file extension WITH the dot (e.g., '.txt'). Empty string if no extension."""
        return os.path.splitext(self.basename)[1]

    @property
    def stem(self) -> str:
        """The file's stem (base name without extension)."""
        return os.path.splitext(self.basename)[0]

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

    async def create_async(self) -> File:
        """Async version of create()."""
        return await _run_fs_sync_shielded(self.create)

    def touch(self, *, mkdir: bool = False) -> File:
        """Create the file if needed and update its timestamps."""
        parent = os.path.dirname(self.path)
        if parent and not os.path.isdir(parent):
            if mkdir:
                os.makedirs(parent, exist_ok=True)
            else:
                raise FileNotFoundError(f"No such directory: '{parent}'")
        with open(self.path, "a", encoding=self.encoding):
            pass
        os.utime(self.path, None)
        return self

    async def touch_async(self, *, mkdir: bool = False) -> File:
        """Async version of touch()."""
        return await _run_fs_sync_shielded(self.touch, mkdir=mkdir)

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

    async def clear_async(self) -> File:
        """Async version of clear()."""
        return await _run_fs_sync_shielded(self.clear)

    @overload
    def read(self, mode: Literal["r"] = "r") -> str: ...

    @overload
    def read(self, mode: Literal["rb"]) -> bytes: ...

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

    @overload
    async def read_async(self, mode: Literal["r"] = "r") -> str: ...

    @overload
    async def read_async(self, mode: Literal["rb"]) -> bytes: ...

    async def read_async(self, mode: Literal["r", "rb"] = "r") -> str | bytes:
        """Async version of read()."""
        return await run_fs_sync(self.read, mode)

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
            f.writelines(f"{entry}{sep}" for entry in data)

    @overload
    def write(
        self,
        data: str,
        *,
        mode: Literal["w"] = "w",
        newline: bool = True,
    ) -> File: ...

    @overload
    def write(
        self,
        data: bytes,
        *,
        mode: Literal["wb"],
        newline: bool = True,
    ) -> File: ...

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

    @overload
    async def write_async(
        self,
        data: str,
        *,
        mode: Literal["w"] = "w",
        newline: bool = True,
    ) -> File: ...

    @overload
    async def write_async(
        self,
        data: bytes,
        *,
        mode: Literal["wb"],
        newline: bool = True,
    ) -> File: ...

    async def write_async(
        self,
        data: str | bytes,
        *,
        mode: Literal["w", "wb"] = "w",
        newline: bool = True,
    ) -> File:
        """Async version of write()."""
        return await _run_fs_sync_shielded(self.write, data, mode=mode, newline=newline)

    @overload
    def append(
        self,
        data: str,
        *,
        mode: Literal["a"] = "a",
        newline: bool = True,
    ) -> File: ...

    @overload
    def append(
        self,
        data: bytes,
        *,
        mode: Literal["ab"],
        newline: bool = True,
    ) -> File: ...

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

    @overload
    async def append_async(
        self,
        data: str,
        *,
        mode: Literal["a"] = "a",
        newline: bool = True,
    ) -> File: ...

    @overload
    async def append_async(
        self,
        data: bytes,
        *,
        mode: Literal["ab"],
        newline: bool = True,
    ) -> File: ...

    async def append_async(
        self,
        data: str | bytes,
        *,
        mode: Literal["a", "ab"] = "a",
        newline: bool = True,
    ) -> File:
        """Async version of append()."""
        return await _run_fs_sync_shielded(self.append, data, mode=mode, newline=newline)

    @overload
    def open(
        self, mode: Literal["r"] = "r", encoding: str | None = None, **kwargs: OpenKwarg
    ) -> IO[str]: ...

    @overload
    def open(
        self, mode: Literal["rb"], encoding: None = None, **kwargs: OpenKwarg
    ) -> IO[bytes]: ...

    @overload
    def open(self, mode: str, encoding: str | None = None, **kwargs: OpenKwarg) -> IO[Any]: ...

    def open(self, mode: str = "r", encoding: str | None = None, **kwargs: OpenKwarg) -> IO[Any]:
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

    @overload
    async def open_async(
        self, mode: Literal["r"] = "r", encoding: str | None = None, **kwargs: OpenKwarg
    ) -> AsyncFileHandle[str]: ...

    @overload
    async def open_async(
        self, mode: Literal["rb"], encoding: None = None, **kwargs: OpenKwarg
    ) -> AsyncFileHandle[bytes]: ...

    @overload
    async def open_async(
        self, mode: str, encoding: str | None = None, **kwargs: OpenKwarg
    ) -> AsyncFileHandle[str] | AsyncFileHandle[bytes]: ...

    async def open_async(
        self, mode: str = "r", encoding: str | None = None, **kwargs: OpenKwarg
    ) -> AsyncFileHandle[str] | AsyncFileHandle[bytes]:
        """Async version of open()."""
        if "b" not in mode and encoding is None:
            encoding = self.encoding
        anyio = _load_anyio()
        with anyio.CancelScope(shield=True):
            handle = await anyio.open_file(self.path, mode, encoding=encoding, **kwargs)
        if "b" in mode:
            return AsyncFileHandle(cast(AsyncFileLike[bytes], handle))
        return AsyncFileHandle(cast(AsyncFileLike[str], handle))

    def write_iter(self, data: Iterable[Any], sep: str = "\n") -> File:
        """
        Write data from an iterable to a file, overwriting any existing data.

        Args:
            data (Iterable): The data to write.
            sep (str, optional): The separator to use between items.

        Returns:
            File: The File object for method chaining.
        """
        self._write_iter(data, "w", sep=sep)
        return self

    async def write_iter_async(self, data: Iterable[Any], sep: str = "\n") -> File:
        """Async version of write_iter()."""
        return await _run_fs_sync_shielded(self.write_iter, data, sep=sep)

    def append_iter(self, data: Iterable[Any], sep: str = "\n") -> File:
        """
        Append data from an iterable to a file.

        Args:
            data (Iterable): The data to append.
            sep (str, optional): The separator to use between items.

        Returns:
            File: The File object for method chaining.
        """
        self._write_iter(data, "a", sep=sep)
        return self

    async def append_iter_async(self, data: Iterable[Any], sep: str = "\n") -> File:
        """Async version of append_iter()."""
        return await _run_fs_sync_shielded(self.append_iter, data, sep=sep)

    def readlines(self) -> list[str]:
        """Equivalent to TextIOWrapper.readlines()."""
        with open(self.path, encoding=self.encoding) as f:
            return f.readlines()

    async def readlines_async(self) -> list[str]:
        """Async version of readlines()."""
        return await run_fs_sync(self.readlines)

    def splitlines(self) -> list[str]:
        """Equivalent to File.read().splitlines()."""
        data = self.read(mode="r")
        if isinstance(data, bytes):
            data = data.decode(self.encoding)
        return data.splitlines()

    async def splitlines_async(self) -> list[str]:
        """Async version of splitlines()."""
        return await run_fs_sync(self.splitlines)

    def move_to(
        self,
        target: File | Directory,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> File:
        """
        Move the file to a new target.

        Args:
            target: The destination `File` or `Directory`.
            mkdir: Whether to create missing parent directories. Defaults to False.
            overwrite: Whether to overwrite the destination if it already exists. Defaults to True.

        Returns:
            File: A new File object pointing at the moved path.
        """
        if isinstance(target, Directory):
            dest_path = os.path.join(target.path, self.basename)
        elif isinstance(target, File):
            dest_path = target.path
        else:
            raise TypeError("File.move_to() target must be a File or Directory")

        if _prepare_destination_path(
            dest_path,
            mkdir=mkdir,
            overwrite=overwrite,
            source_path=self.path,
            expected_type="file",
        ):
            return self._clone_with_path(dest_path)
        shutil.move(self.path, dest_path)
        return self._clone_with_path(dest_path)

    async def move_to_async(
        self,
        target: File | Directory,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> File:
        """Async version of move_to()."""
        return await _run_fs_sync_shielded(self.move_to, target, mkdir=mkdir, overwrite=overwrite)

    def copy_to(
        self,
        target: File | Directory,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> File:
        """
        Copy the file to a new target.

        Args:
            target: The destination `File` or `Directory`.
            mkdir: Whether to create missing parent directories. Defaults to False.
            overwrite: Whether to overwrite the destination if it already exists. Defaults to True.

        Returns:
            File: A new File object pointing at the copied path.
        """
        if isinstance(target, Directory):
            dest_path = os.path.join(target.path, self.basename)
        elif isinstance(target, File):
            dest_path = target.path
        else:
            raise TypeError("File.copy_to() target must be a File or Directory")

        if _prepare_destination_path(
            dest_path,
            mkdir=mkdir,
            overwrite=overwrite,
            source_path=self.path,
            expected_type="file",
            remove_existing=False,
        ):
            return self._clone_with_path(dest_path)
        _copy_file_to_destination(self.path, dest_path)
        return self._clone_with_path(dest_path)

    async def copy_to_async(
        self,
        target: File | Directory,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> File:
        """Async version of copy_to()."""
        return await _run_fs_sync_shielded(self.copy_to, target, mkdir=mkdir, overwrite=overwrite)

    def with_dir(self, directory: str) -> File:
        """
        Change the directory of the file object. This will not move the actual file to that directory.
        Use File.move_to for that.
        """
        return self._clone_with_path(os.path.join(directory, self.basename))

    def with_ext(self, ext: str) -> File:
        """
        Change the extension of the file and return the new File object.

        Args:
            ext (str): The new extension of the file.

        Returns:
            File: The File object with the new extension.
        """
        if not ext.startswith("."):
            ext = f".{ext}"
        return self._clone_with_path(os.path.join(self.dirname, f"{self.stem}{ext}"))

    def with_suffix(self, suffix: str) -> File:
        """Add a suffix to the file's name and return the new File object."""
        filename = f"{self.stem}{suffix}{self.suffix}"
        return self._clone_with_path(os.path.join(self.dirname, filename))

    def with_prefix(self, prefix: str) -> File:
        """Add a prefix to the file's name and return the new File object."""
        filename = f"{prefix}{self.stem}{self.suffix}"
        return self._clone_with_path(os.path.join(self.dirname, filename))

    def with_stem(self, stem: str) -> File:
        """Return a new File with the stem changed, keeping the suffix."""
        suffix = self.suffix
        return self._clone_with_path(os.path.join(self.dirname, f"{stem}{suffix}"))

    def rename(self, name: str) -> File:
        """Rename the file and return the new File object."""
        new_path = os.path.join(self.dirname, name)
        os.rename(self.path, new_path)
        return self._clone_with_path(new_path)

    def link(self, target: str, follow_symlinks: bool = True) -> File:
        """Create a hard link and return a File for the created link path."""
        try:
            os.link(self.path, target, follow_symlinks=follow_symlinks)
        except NotImplementedError:
            if not follow_symlinks:
                raise
            os.link(self.path, target)
        return self._clone_with_path(target)

    async def link_async(self, target: str, follow_symlinks: bool = True) -> File:
        """Async version of link()."""
        return await _run_fs_sync_shielded(self.link, target, follow_symlinks=follow_symlinks)

    def symlink(self, target: str) -> File:
        """Create a symbolic link and return a File for the created link path."""
        os.symlink(_symlink_source_path(self.path, target), target)
        return self._clone_with_path(target)

    async def symlink_async(self, target: str) -> File:
        """Async version of symlink()."""
        return await _run_fs_sync_shielded(self.symlink, target)

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
        abs: bool = False,  # noqa: A002
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
        return get_dir_size(self.path, readable=False)

    @property
    def size_readable(self) -> str:
        """Total size of the directory and all its contents in human-readable form."""
        return bytes_readable(self.size)

    @property
    def exists(self) -> bool:
        """Check if the directory exists."""
        return os.path.isdir(self.path)

    def create(self, mode: int = 0o777, exist_ok: bool = True) -> Directory:
        """Create directory (including parents)."""
        os.makedirs(self.path, mode=mode, exist_ok=exist_ok)
        return self

    async def create_async(self, mode: int = 0o777, exist_ok: bool = True) -> Directory:
        """Async version of create()."""
        return await _run_fs_sync_shielded(self.create, mode, exist_ok)

    def clear(self) -> Directory:
        """Remove all children while keeping the directory itself."""
        if not self.exists:
            return self
        with os.scandir(self.path) as entries:
            for entry in entries:
                _remove_existing_path(entry.path)
        return self

    async def clear_async(self) -> Directory:
        """Async version of clear()."""
        return await _run_fs_sync_shielded(self.clear)

    @property
    def parent(self) -> Directory:
        """The parent directory."""
        return Directory(os.path.dirname(self.path))

    @classmethod
    def rand(cls, prefix: str = "dir") -> Directory:
        return Directory(joinpath(os.getcwd(), safe_filename(rand_filename(prefix))))

    def move_to(
        self,
        target: Directory,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> Directory:
        """
        Move this directory into another directory, preserving its basename.

        Args:
            target: The destination parent directory.
            mkdir: Whether to create missing parent directories. Defaults to False.
            overwrite: Whether to overwrite if target path already exists. Defaults to True.

        Returns:
            Directory: A new Directory object pointing at the moved path.
        """
        if not isinstance(target, Directory):
            raise TypeError("Directory.move_to() target must be a Directory")

        dest = os.path.join(target.path, self.basename)
        _ensure_directory_target_is_not_inside_source(self.path, dest)
        if _prepare_destination_path(
            dest,
            mkdir=mkdir,
            overwrite=overwrite,
            source_path=self.path,
            expected_type="directory",
        ):
            return self._clone_with_path(dest)
        shutil.move(self.path, dest)
        return self._clone_with_path(dest)

    async def move_to_async(
        self,
        target: Directory,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> Directory:
        """Async version of move_to()."""
        return await _run_fs_sync_shielded(self.move_to, target, mkdir=mkdir, overwrite=overwrite)

    def copy_to(
        self,
        target: Directory,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> Directory:
        """
        Copy this directory into another directory, preserving its basename.

        Args:
            target: The destination parent directory.
            mkdir: Whether to create missing parent directories. Defaults to False.
            overwrite: Whether to overwrite if target path already exists. Defaults to True.

        Returns:
            Directory: A new Directory object pointing at the copied path.
        """
        if not isinstance(target, Directory):
            raise TypeError("Directory.copy_to() target must be a Directory")

        dest = os.path.join(target.path, self.basename)
        _ensure_directory_target_is_not_inside_source(self.path, dest)
        if _prepare_destination_path(
            dest,
            mkdir=mkdir,
            overwrite=overwrite,
            source_path=self.path,
            expected_type="directory",
            remove_existing=False,
        ):
            return self._clone_with_path(dest)
        _copy_directory_to_destination(self.path, dest, overwrite=overwrite)
        return self._clone_with_path(dest)

    async def copy_to_async(
        self,
        target: Directory,
        *,
        mkdir: bool = False,
        overwrite: bool = True,
    ) -> Directory:
        """Async version of copy_to()."""
        return await _run_fs_sync_shielded(self.copy_to, target, mkdir=mkdir, overwrite=overwrite)

    def remove(self) -> Directory:
        """Remove the directory and all its contents."""
        if not self.exists:
            return self
        shutil.rmtree(self.path)
        return self

    async def remove_async(self) -> Directory:
        """Async version of remove()."""
        return await _run_fs_sync_shielded(self.remove)

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

    async def yield_files_async(
        self,
        ext: str | tuple[str, ...] | None = None,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
    ) -> AsyncGenerator[File, None]:
        """Async version of yield_files()."""
        async for file in iterate_fs(
            lambda: self.yield_files(ext=ext, glob=glob, regex=regex, recursive=recursive)
        ):
            yield file

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

    async def get_files_async(
        self,
        ext: str | tuple[str, ...] | None = None,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
    ) -> list[File]:
        """Async version of get_files()."""
        return await run_fs_sync(
            self.get_files, ext=ext, glob=glob, regex=regex, recursive=recursive
        )

    @overload
    async def read_files_async(
        self,
        *,
        mode: Literal["r"] = "r",
        ext: str | tuple[str, ...] | None = None,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
        concurrency: int = 8,
    ) -> list[tuple[File, str]]: ...

    @overload
    async def read_files_async(
        self,
        *,
        mode: Literal["rb"],
        ext: str | tuple[str, ...] | None = None,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
        concurrency: int = 8,
    ) -> list[tuple[File, bytes]]: ...

    async def read_files_async(
        self,
        *,
        mode: Literal["r", "rb"] = "r",
        ext: str | tuple[str, ...] | None = None,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
        concurrency: int = 8,
    ) -> list[tuple[File, str]] | list[tuple[File, bytes]]:
        """
        Read matching files concurrently.

        Args:
            mode: The mode to read files in. Use "r" for text and "rb" for binary.
            ext: If provided, only read files with provided extensions.
            glob: Glob pattern as string or compiled regex from fnmatch.translate().
            regex: Regex pattern as string or compiled re.Pattern.
            recursive: Whether to search recursively.
            concurrency: Maximum number of concurrent read operations.

        Returns:
            list[tuple[File, str]] | list[tuple[File, bytes]]: Matching files and their contents.
        """
        files = await self.get_files_async(ext=ext, glob=glob, regex=regex, recursive=recursive)

        if mode == "rb":

            async def read_file_binary(file: File) -> tuple[File, bytes]:
                return file, await file.read_async(mode="rb")

            return await _map_limited_async(files, read_file_binary, concurrency=concurrency)

        async def read_file_text(file: File) -> tuple[File, str]:
            return file, await file.read_async(mode="r")

        return await _map_limited_async(files, read_file_text, concurrency=concurrency)

    async def remove_files_async(
        self,
        *,
        ext: str | tuple[str, ...] | None = None,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
        concurrency: int = 8,
    ) -> list[File]:
        """
        Remove matching files concurrently.

        Args:
            ext: If provided, only remove files with provided extensions.
            glob: Glob pattern as string or compiled regex from fnmatch.translate().
            regex: Regex pattern as string or compiled re.Pattern.
            recursive: Whether to search recursively.
            concurrency: Maximum number of concurrent remove operations.

        Returns:
            list[File]: The removed files in snapshot order.
        """
        files = await self.get_files_async(ext=ext, glob=glob, regex=regex, recursive=recursive)

        async def remove_file(file: File) -> File:
            await file.remove_async()
            return file

        return await _map_limited_async(files, remove_file, concurrency=concurrency)

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

    async def yield_subdirs_async(
        self,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
    ) -> AsyncGenerator[Directory, None]:
        """Async version of yield_subdirs()."""
        async for directory in iterate_fs(
            lambda: self.yield_subdirs(glob=glob, regex=regex, recursive=recursive)
        ):
            yield directory

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

    async def get_subdirs_async(
        self,
        glob: str | re.Pattern[str] | None = None,
        regex: str | re.Pattern[str] | None = None,
        recursive: bool = True,
    ) -> list[Directory]:
        """Async version of get_subdirs()."""
        return await run_fs_sync(self.get_subdirs, glob=glob, regex=regex, recursive=recursive)

    def yield_entries(self, *, abs: bool = False) -> Generator[File | Directory, None, None]:  # noqa: A002
        """Yield immediate child files and directories in a single pass."""
        with os.scandir(self.path) as entries:
            for entry in entries:
                entry_path = os.path.abspath(entry.path) if abs else entry.path
                if entry.is_dir():
                    yield Directory(entry_path)
                elif entry.is_file():
                    yield File(entry_path)

    async def yield_entries_async(
        self,
        *,
        abs: bool = False,  # noqa: A002
    ) -> AsyncGenerator[File | Directory, None]:
        """Async version of yield_entries()."""
        async for entry in iterate_fs(lambda: self.yield_entries(abs=abs)):
            yield entry

    def get_entries(self, *, abs: bool = False) -> list[File | Directory]:  # noqa: A002
        """Return immediate child files and directories."""
        return list(self.yield_entries(abs=abs))

    async def get_entries_async(
        self,
        *,
        abs: bool = False,  # noqa: A002
    ) -> list[File | Directory]:
        """Async version of get_entries()."""
        return await run_fs_sync(self.get_entries, abs=abs)

    def walk(
        self,
        *,
        follow_symlinks: bool = False,
        abs: bool = False,  # noqa: A002
    ) -> Generator[tuple[Directory, list[Directory], list[File]], None, None]:
        """
        Recursively walk the directory tree in top-down order.

        Yields:
            tuple[Directory, list[Directory], list[File]]: The current root, its child directories,
            and its child files.
        """
        yield from _walk_directory(self, follow_symlinks=follow_symlinks, abs=abs, visited=None)

    async def walk_async(
        self,
        *,
        follow_symlinks: bool = False,
        abs: bool = False,  # noqa: A002
    ) -> AsyncGenerator[tuple[Directory, list[Directory], list[File]], None]:
        """Async version of walk()."""
        async for entry in iterate_fs(lambda: self.walk(follow_symlinks=follow_symlinks, abs=abs)):
            yield entry

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


def _walk_directory(
    directory: Directory,
    *,
    follow_symlinks: bool,
    abs: bool,  # noqa: A002
    visited: set[tuple[int, int]] | None,
) -> Generator[tuple[Directory, list[Directory], list[File]], None, None]:
    if follow_symlinks:
        if visited is None:
            visited = {_dir_identity(directory.path)}
        else:
            current_identity = _dir_identity(directory.path)
            if current_identity in visited:
                return
            visited.add(current_identity)

    subdirs: list[Directory] = []
    files: list[File] = []
    for entry in directory.yield_entries(abs=abs):
        if isinstance(entry, Directory):
            subdirs.append(entry)
        else:
            files.append(entry)

    root = Directory(os.path.abspath(directory.path)) if abs else directory
    yield root, subdirs, files

    for subdir in subdirs:
        if subdir.is_symlink and not follow_symlinks:
            continue
        yield from _walk_directory(
            subdir,
            follow_symlinks=follow_symlinks,
            abs=abs,
            visited=visited,
        )


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
    "HOME",
    "SEP",
    "AsyncFileHandle",
    "Directory",
    "File",
    "PathLike",
    "abspath",
    "basename",
    "bytes_readable",
    "chdir",
    "chmod",
    "chown",
    "copy",
    "dirname",
    "ensure_paths_exist",
    "exec_cmd",
    "exists",
    "get_dir_size",
    "get_dirs_in",
    "get_files_in",
    "getcwd",
    "is_wsl",
    "isdir",
    "isfile",
    "islink",
    "joinpath",
    "json_append",
    "json_append_async",
    "json_dump",
    "json_dump_async",
    "json_load",
    "json_load_async",
    "link",
    "mkdir",
    "mkdirs",
    "move",
    "move_files",
    "pickle_dump",
    "pickle_dump_async",
    "pickle_load",
    "pickle_load_async",
    "rand_filename",
    "read_piped",
    "readable_size_to_bytes",
    "remove",
    "rename",
    "run_fs_sync",
    "splitpath",
    "start_file",
    "stat",
    "toml_dump",
    "toml_dump_async",
    "toml_load",
    "toml_load_async",
    "windows_has_drive",
    "yaml_dump",
    "yaml_dump_async",
    "yaml_load",
    "yaml_load_async",
    "yield_dirs_in",
    "yield_files_in",
]
