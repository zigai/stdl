from __future__ import annotations

import os
import time
from pathlib import Path

import anyio
import pytest

from stdl import fs


def test_file_async_roundtrip(tmp_path: Path) -> None:
    async def scenario() -> None:
        file = fs.File(str(tmp_path / "async.txt"))

        assert await file.exists_async() is False

        await file.touch_async()
        assert await file.exists_async() is True

        await file.write_async("hello", newline=False)
        await file.append_async(" world", newline=False)

        assert await file.read_async() == "hello world"
        assert await file.size_async() == len("hello world")
        assert await file.size_readable_async() == fs.bytes_readable(len("hello world"))
        assert isinstance(await file.created_async(), float)
        assert isinstance(await file.modified_async(), float)
        assert isinstance(await file.accessed_async(), float)
        assert await file.is_symlink_async() is False
        assert await file.should_exist_async() == file

        stat_result = await file.stat_async()
        assert stat_result.st_size == len("hello world")

        await file.clear_async()
        assert await file.read_async() == ""

        await file.write_iter_async(["a", "b", "c"])
        assert await file.readlines_async() == ["a\n", "b\n", "c\n"]
        assert await file.splitlines_async() == ["a", "b", "c"]

    anyio.run(scenario)


def test_open_async_supports_context_manager_iteration_and_binary(tmp_path: Path) -> None:
    async def scenario() -> None:
        text_file = fs.File(str(tmp_path / "handle.txt"))

        async with await text_file.open_async("w") as handle:
            assert await handle.write("first\nsecond\n") == len("first\nsecond\n")
            await handle.flush()

        async with await text_file.open_async() as handle:
            assert await handle.tell() == 0
            assert await handle.readline() == "first\n"
            assert await handle.tell() == len("first\n")
            assert await handle.seek(0) == 0
            assert [line async for line in handle] == ["first\n", "second\n"]
            assert await handle.seek(0) == 0
            assert await handle.readlines() == ["first\n", "second\n"]

        async with await text_file.open_async("r+") as handle:
            assert await handle.seek(5) == 5
            assert await handle.truncate() == 5

        assert await text_file.read_async() == "first"

        binary_file = fs.File(str(tmp_path / "handle.bin"))
        async with await binary_file.open_async("wb") as handle:
            assert await handle.write(b"\x00\x01") == 2

        async with await binary_file.open_async("rb") as handle:
            assert await handle.read() == b"\x00\x01"

    anyio.run(scenario)


def test_open_async_supports_chunk_iteration(tmp_path: Path) -> None:
    async def scenario() -> None:
        file = fs.File(str(tmp_path / "chunks.txt"))
        await file.write_async("abcdefgh", newline=False)

        async with await file.open_async() as handle:
            chunks = [chunk async for chunk in handle.iter_chunks(3)]

        assert chunks == ["abc", "def", "gh"]

    anyio.run(scenario)


def test_open_async_serializes_concurrent_handle_operations(tmp_path: Path) -> None:
    async def scenario() -> None:
        file = fs.File(str(tmp_path / "concurrent.txt"))

        async with await file.open_async("a+") as handle, anyio.create_task_group() as task_group:
            for _ in range(20):
                task_group.start_soon(handle.write, "x")

        assert await file.read_async() == "x" * 20

    anyio.run(scenario)


def test_write_async_is_shielded_from_cancellation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_write = fs.File.write

    def slow_write(self: fs.File, data: str | bytes, **kwargs: object) -> fs.File:
        time.sleep(0.05)
        return original_write(self, data, **kwargs)

    monkeypatch.setattr(fs.File, "write", slow_write)

    async def scenario() -> None:
        file = fs.File(str(tmp_path / "shielded.txt"))

        with anyio.move_on_after(0.01) as scope:
            await file.write_async("shielded", newline=False)

        assert scope.cancel_called is True
        assert await file.read_async() == "shielded"

    anyio.run(scenario)


def test_file_async_copy_move_links_and_samefile(tmp_path: Path) -> None:
    async def scenario() -> None:
        source = fs.File(str(tmp_path / "source.txt"))
        await source.write_async("payload", newline=False)

        copied = await source.copy_to_async(fs.Directory(str(tmp_path / "copies")), mkdir=True)
        assert copied.path == str(tmp_path / "copies" / "source.txt")
        assert await copied.read_async() == "payload"
        assert await source.read_async() == "payload"

        moved = await source.move_to_async(
            fs.File(str(tmp_path / "moved" / "renamed.txt")), mkdir=True
        )
        assert moved.path == str(tmp_path / "moved" / "renamed.txt")
        assert await moved.read_async() == "payload"
        assert await source.exists_async() is False

        linked = await moved.link_async(str(tmp_path / "linked.txt"))
        assert linked.path == str(tmp_path / "linked.txt")
        assert await linked.samefile_async(moved)

        symlinked = await moved.symlink_async(str(tmp_path / "symlinked.txt"))
        assert await symlinked.is_symlink_async() is True
        assert await anyio.Path(await symlinked.readlink_async()).samefile(moved.path)

    anyio.run(scenario)


def test_directory_async_traversal_and_mutation(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "top.txt").write_text("top")
    (root / "nested").mkdir()
    (root / "nested" / "child.txt").write_text("child")
    (root / "nested" / "ignore.py").write_text("print('x')")

    async def scenario() -> None:
        directory = fs.Directory(str(root))

        files = [file async for file in directory.yield_files_async(ext="txt")]
        assert [file.basename for file in files] == ["top.txt", "child.txt"]

        subdirs = [subdir async for subdir in directory.yield_subdirs_async()]
        assert [subdir.basename for subdir in subdirs] == ["nested"]

        entries = [entry async for entry in directory.yield_entries_async()]
        assert {entry.basename for entry in entries} == {"nested", "top.txt"}

        walked = [item async for item in directory.walk_async()]
        assert [item[0].basename for item in walked] == ["root", "nested"]

        assert await directory.get_files_async(regex=r"\.txt$") == files
        assert await directory.get_subdirs_async(glob="nest*") == subdirs
        assert await directory.get_entries_async() == entries
        assert await directory.size_async() == directory.size
        assert await directory.exists_async() is True

        copied = await directory.copy_to_async(fs.Directory(str(tmp_path / "copies")), mkdir=True)
        assert copied.path == str(tmp_path / "copies" / "root")
        copied_files = [file async for file in copied.yield_files_async(ext="txt")]
        assert [file.basename for file in copied_files] == ["top.txt", "child.txt"]

        await copied.clear_async()
        assert await copied.get_entries_async() == []

        moved = await copied.move_to_async(fs.Directory(str(tmp_path / "moved")), mkdir=True)
        assert moved.path == str(tmp_path / "moved" / "root")
        assert await moved.exists_async() is True

        await moved.remove_async()
        assert await moved.exists_async() is False

    anyio.run(scenario)


def test_directory_async_iteration_can_exit_early(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    for index in range(3):
        (root / f"file-{index}.txt").write_text(str(index))

    async def scenario() -> None:
        directory = fs.Directory(str(root))

        async for file in directory.yield_files_async():
            assert file.basename.startswith("file-")
            break

        assert sorted(file.basename for file in await directory.get_files_async()) == [
            "file-0.txt",
            "file-1.txt",
            "file-2.txt",
        ]

    anyio.run(scenario)


def test_directory_async_entries_and_walk_support_absolute_paths(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "top.txt").write_text("top")
    (root / "nested").mkdir()

    async def scenario() -> None:
        directory = fs.Directory(str(root.relative_to(tmp_path)))
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            entries = [entry async for entry in directory.yield_entries_async(abs=True)]
            walked = [item async for item in directory.walk_async(abs=True)]
        finally:
            os.chdir(original_cwd)

        assert all(os.path.isabs(entry.path) for entry in entries)
        assert all(os.path.isabs(root_dir.path) for root_dir, _, _ in walked)

    anyio.run(scenario)


@pytest.mark.skipif(os.name == "nt", reason="symlink behavior is platform-specific")
def test_walk_follow_symlinks_avoids_cycles(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    child = root / "child"
    child.mkdir()
    (child / "file.txt").write_text("x")
    (child / "back").symlink_to(root, target_is_directory=True)

    walked = list(fs.Directory(str(root)).walk(follow_symlinks=True))

    assert [item[0].basename for item in walked] == ["root", "child"]


@pytest.mark.skipif(os.name == "nt", reason="owner/group/xattr behavior is platform-specific")
def test_async_metadata_and_xattrs(tmp_path: Path) -> None:
    async def scenario() -> None:
        file = fs.File(str(tmp_path / "meta.txt"))
        await file.write_async("meta", newline=False)

        assert isinstance(await file.owner_async(), str)
        assert isinstance(await file.group_async(), str)
        assert await file.ctime_async() == await file.created_async()
        assert await file.mtime_async() == await file.modified_async()
        assert await file.atime_async() == await file.accessed_async()

        await file.set_xattr_async("value", "key")
        assert await file.get_xattr_async("key") == "value"
        await file.remove_xattr_async("key")
        with pytest.raises(OSError, match=r"No data available|No such xattr"):
            await file.get_xattr_async("key")

    anyio.run(scenario)


def test_async_structured_file_helpers(tmp_path: Path) -> None:
    async def scenario() -> None:
        json_path = tmp_path / "data.json"
        yaml_path = tmp_path / "data.yaml"
        toml_path = tmp_path / "data.toml"
        pickle_path = tmp_path / "data.pkl"

        await fs.json_dump_async({"answer": 42}, json_path)
        assert await fs.json_load_async(json_path) == {"answer": 42}

        await fs.yaml_dump_async({"answer": 42}, yaml_path)
        assert await fs.yaml_load_async(yaml_path) == {"answer": 42}

        await fs.toml_dump_async({"answer": 42}, toml_path)
        assert await fs.toml_load_async(toml_path) == {"answer": 42}

        await fs.pickle_dump_async({"answer": 42}, pickle_path)
        assert await fs.pickle_load_async(pickle_path) == {"answer": 42}

    anyio.run(scenario)


def test_async_api_reports_missing_anyio(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import_module = fs.importlib.import_module

    def fake_import_module(name: str) -> object:
        if name == "anyio":
            raise ImportError("missing anyio")
        return real_import_module(name)

    monkeypatch.setattr(fs, "_ANYIO", None)
    monkeypatch.setattr(fs.importlib, "import_module", fake_import_module)

    with pytest.raises(ImportError, match=r"stdl\[async\]"):
        fs._load_anyio()
