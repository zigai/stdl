import os
import stat
import sys
import tempfile
from pathlib import Path

import pytest

from stdl import fs
from stdl.fs import File


@pytest.fixture
def temp_file(tmp_path: Path) -> File:
    """Create a temporary file with content."""
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    return fs.File(str(f))


@pytest.fixture
def temp_dir(tmp_path: Path) -> str:
    """Return temporary directory as string."""
    return str(tmp_path)


@pytest.fixture
def empty_file(tmp_path: Path) -> File:
    """Create an empty temporary file."""
    f = tmp_path / "empty.txt"
    f.touch()
    return fs.File(str(f))


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


class TestFileInit:
    def test_file_init(self, tmp_path: Path):
        """Create File with string path."""
        path = str(tmp_path / "test.txt")
        f = fs.File(path)
        assert f.path == path

    def test_file_init_with_pathlike(self, tmp_path: Path):
        """Create File with PathLike object."""
        path = tmp_path / "test.txt"
        f = fs.File(path)
        assert f.path == str(path)

    def test_file_init_abs(self, tmp_path: Path):
        """Create File with abs=True."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            f = fs.File("test.txt", abs=True)
            assert os.path.isabs(f.path)
            assert f.path == os.path.abspath("test.txt")
        finally:
            os.chdir(original_cwd)

    def test_file_init_encoding(self, tmp_path: Path):
        """Create File with custom encoding."""
        path = str(tmp_path / "test.txt")
        f = fs.File(path, encoding="latin-1")
        assert f.encoding == "latin-1"

    def test_file_exists_true(self, temp_file: File):
        """Check exists returns True for existing file."""
        assert temp_file.exists is True

    def test_file_exists_false(self, tmp_path: Path):
        """Check exists returns False for non-existent file."""
        f = fs.File(str(tmp_path / "nonexistent.txt"))
        assert f.exists is False

    def test_file_path_property(self, temp_file: File):
        """Verify path returns correct string."""
        assert isinstance(temp_file.path, str)
        assert temp_file.path.endswith("test.txt")

    def test_file_fspath(self, temp_file: File):
        """Verify __fspath__ protocol."""
        assert os.fspath(temp_file) == temp_file.path

    def test_file_str(self, temp_file: File):
        """Verify __str__ returns path."""
        assert str(temp_file) == temp_file.path


class TestFilePathComponents:
    def test_file_basename(self, temp_file: File):
        """basename returns filename only."""
        assert temp_file.basename == "test.txt"

    def test_file_dirname(self, temp_file: File):
        """dirname returns directory path."""
        dirname = temp_file.dirname
        assert os.path.isdir(dirname)
        assert "test.txt" not in dirname

    def test_file_parent(self, temp_file: File):
        """parent returns Directory object."""
        parent = temp_file.parent
        assert isinstance(parent, fs.Directory)
        assert parent.path == os.path.dirname(temp_file.path)

    def test_file_ext(self, temp_file: File):
        """ext returns extension without dot."""
        assert temp_file.ext == "txt"

    def test_file_ext_no_extension(self, tmp_path: Path):
        """ext returns empty string for no extension."""
        f = tmp_path / "noext"
        f.touch()
        file = fs.File(str(f))
        assert file.ext == ""

    def test_file_ext_dotfile(self, tmp_path: Path):
        """ext handles dotfiles correctly (e.g., .gitignore)."""
        f = tmp_path / ".gitignore"
        f.touch()
        file = fs.File(str(f))
        assert file.ext == "gitignore"

    def test_file_suffix(self, temp_file: File):
        """suffix returns extension with dot."""
        assert temp_file.suffix == ".txt"

    def test_file_suffix_no_extension(self, tmp_path: Path):
        """suffix returns empty string for no extension."""
        f = tmp_path / "noext"
        f.touch()
        file = fs.File(str(f))
        assert file.suffix == ""

    def test_file_suffix_dotfile(self, tmp_path: Path):
        """suffix handles dotfiles correctly."""
        f = tmp_path / ".gitignore"
        f.touch()
        file = fs.File(str(f))
        assert file.suffix == ""

    def test_file_stem(self, temp_file: File):
        """stem returns name without extension."""
        assert temp_file.stem == "test"

    def test_file_stem_no_extension(self, tmp_path: Path):
        """stem returns full name when no extension."""
        f = tmp_path / "noext"
        f.touch()
        file = fs.File(str(f))
        assert file.stem == "noext"

    def test_file_stem_multiple_dots(self, tmp_path: Path):
        """stem handles file.tar.gz correctly."""
        f = tmp_path / "archive.tar.gz"
        f.touch()
        file = fs.File(str(f))
        assert file.stem == "archive.tar"
        assert file.ext == "gz"

    def test_file_abspath(self, tmp_path: Path):
        """abspath returns absolute path."""
        f = tmp_path / "test.txt"
        f.touch()
        file = fs.File(str(f))
        assert os.path.isabs(file.abspath)

    def test_file_nodes(self, temp_file: File):
        """nodes returns path parts as list."""
        nodes = temp_file.nodes
        assert isinstance(nodes, list)
        assert "test.txt" in nodes


class TestFilePathBooleans:
    def test_file_is_absolute_true(self, temp_file: File):
        """is_absolute returns True for absolute path."""
        assert temp_file.is_absolute is True

    def test_file_is_absolute_false(self, tmp_path: Path):
        """is_absolute returns False for relative path."""
        f = fs.File("relative/path.txt")
        assert f.is_absolute is False

    def test_file_is_symlink_true(self, tmp_path: Path):
        """is_symlink returns True for symlink."""
        target = tmp_path / "target.txt"
        target.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        file = fs.File(str(link))
        assert file.is_symlink is True

    def test_file_is_symlink_false(self, temp_file: File):
        """is_symlink returns False for regular file."""
        assert temp_file.is_symlink is False


class TestFileMetadata:
    def test_file_size(self, temp_file: File):
        """size returns correct byte count."""
        assert temp_file.size == 11  # "hello world" = 11 bytes

    def test_file_size_readable(self, temp_file: File):
        """size_readable returns human-readable string."""
        readable = temp_file.size_readable
        assert isinstance(readable, str)
        assert "B" in readable

    def test_file_ctime(self, temp_file: File):
        """ctime/created returns creation timestamp."""
        ctime = temp_file.ctime
        assert isinstance(ctime, float)
        assert ctime > 0
        assert temp_file.created == ctime

    def test_file_mtime(self, temp_file: File):
        """mtime/modified returns modification timestamp."""
        mtime = temp_file.mtime
        assert isinstance(mtime, float)
        assert mtime > 0
        assert temp_file.modified == mtime

    def test_file_atime(self, temp_file: File):
        """atime/accessed returns access timestamp."""
        atime = temp_file.atime
        assert isinstance(atime, float)
        assert atime > 0
        assert temp_file.accessed == atime

    def test_file_stat(self, temp_file: File):
        """stat() returns os.stat_result."""
        result = temp_file.stat()
        assert isinstance(result, os.stat_result)
        assert result.st_size == 11

    def test_file_stat_follow_symlinks(self, tmp_path: Path):
        """stat(follow_symlinks=False) on symlink."""
        target = tmp_path / "target.txt"
        target.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        file = fs.File(str(link))
        stat_no_follow = file.stat(follow_symlinks=False)
        assert stat.S_ISLNK(stat_no_follow.st_mode)


class TestFileCreationDeletion:
    def test_file_create(self, tmp_path: Path):
        """create() creates new empty file."""
        f = fs.File(str(tmp_path / "new.txt"))
        assert not f.exists
        f.create()
        assert f.exists
        assert f.size == 0

    def test_file_create_existing(self, temp_file: File):
        """create() on existing file does nothing."""
        original_content = temp_file.read()
        temp_file.create()
        assert temp_file.read() == original_content

    def test_file_create_returns_self(self, tmp_path: Path):
        """create() returns self for chaining."""
        f = fs.File(str(tmp_path / "new.txt"))
        result = f.create()
        assert result is f

    def test_file_remove(self, temp_file: File):
        """remove() deletes file."""
        assert temp_file.exists
        temp_file.remove()
        assert not temp_file.exists

    def test_file_remove_nonexistent(self, tmp_path: Path):
        """remove() on non-existent file does nothing."""
        f = fs.File(str(tmp_path / "nonexistent.txt"))
        f.remove()

    def test_file_remove_returns_self(self, temp_file: File):
        """remove() returns self for chaining."""
        result = temp_file.remove()
        assert result is temp_file

    def test_file_clear(self, temp_file: File):
        """clear() empties file contents."""
        assert temp_file.size > 0
        temp_file.clear()
        assert temp_file.size == 0

    def test_file_clear_nonexistent(self, tmp_path: Path):
        """clear() on non-existent file does nothing."""
        f = fs.File(str(tmp_path / "nonexistent.txt"))
        f.clear()
        assert not f.exists


class TestFileTextReadWrite:
    def test_file_read(self, temp_file: File):
        """read() returns file contents as string."""
        content = temp_file.read()
        assert content == "hello world"
        assert isinstance(content, str)

    def test_file_read_encoding(self, tmp_path: Path):
        """read() respects file encoding."""
        f = tmp_path / "encoded.txt"
        f.write_bytes("café".encode("latin-1"))
        file = fs.File(str(f), encoding="latin-1")
        content = file.read()
        assert content == "café"

    def test_file_write(self, tmp_path: Path):
        """write() writes string to file."""
        f = fs.File(str(tmp_path / "write.txt"))
        f.write("test content")
        assert f.exists
        assert f.read() == "test content\n"

    def test_file_write_newline(self, tmp_path: Path):
        """write() adds newline by default."""
        f = fs.File(str(tmp_path / "write.txt"))
        f.write("line1")
        content = f.read()
        assert content.endswith("\n")

    def test_file_write_no_newline(self, tmp_path: Path):
        """write(newline=False) skips newline."""
        f = fs.File(str(tmp_path / "write.txt"))
        f.write("line1", newline=False)
        content = f.read()
        assert content == "line1"

    def test_file_write_returns_self(self, tmp_path: Path):
        """write() returns self for chaining."""
        f = fs.File(str(tmp_path / "write.txt"))
        result = f.write("test")
        assert result is f

    def test_file_append(self, temp_file: File):
        """append() adds to existing content."""
        original = temp_file.read()
        temp_file.append("appended")
        content = temp_file.read()
        assert content.startswith(original)
        assert "appended" in content

    def test_file_append_newline(self, temp_file: File):
        """append() adds newline by default."""
        temp_file.append("new line")
        content = temp_file.read()
        assert content.endswith("new line\n")

    def test_file_readlines(self, tmp_path: Path):
        """readlines() returns list of lines with \\n."""
        f = tmp_path / "lines.txt"
        f.write_text("line1\nline2\nline3\n")
        file = fs.File(str(f))
        lines = file.readlines()
        assert lines == ["line1\n", "line2\n", "line3\n"]

    def test_file_splitlines(self, tmp_path: Path):
        """splitlines() returns list without \\n."""
        f = tmp_path / "lines.txt"
        f.write_text("line1\nline2\nline3")
        file = fs.File(str(f))
        lines = file.splitlines()
        assert lines == ["line1", "line2", "line3"]


class TestFileBinaryReadWrite:
    def test_file_read_binary(self, tmp_path: Path):
        """read(mode='rb') returns bytes."""
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x01\x02\x03")
        file = fs.File(str(f))
        content = file.read(mode="rb")
        assert content == b"\x00\x01\x02\x03"
        assert isinstance(content, bytes)

    def test_file_write_binary(self, tmp_path: Path):
        """write(mode='wb') writes bytes."""
        f = fs.File(str(tmp_path / "binary.bin"))
        f.write(b"\x00\x01\x02\x03", mode="wb")
        assert f.exists
        content = f.read(mode="rb")
        assert content == b"\x00\x01\x02\x03"

    def test_file_append_binary(self, tmp_path: Path):
        """append(mode='ab') appends bytes."""
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x01")
        file = fs.File(str(f))
        file.append(b"\x02\x03", mode="ab")
        content = file.read(mode="rb")
        assert content == b"\x00\x01\x02\x03"


class TestFileIterableWrite:
    def test_file_write_iter(self, tmp_path: Path):
        """write_iter() writes list to file."""
        f = fs.File(str(tmp_path / "iter.txt"))
        f.write_iter(["a", "b", "c"])
        content = f.read()
        assert "a\n" in content
        assert "b\n" in content
        assert "c\n" in content

    def test_file_write_iter_custom_sep(self, tmp_path: Path):
        """write_iter(sep=',') uses custom separator."""
        f = fs.File(str(tmp_path / "iter.txt"))
        f.write_iter(["a", "b", "c"], sep=",")
        content = f.read()
        assert content == "a,b,c,"

    def test_file_append_iter(self, tmp_path: Path):
        """append_iter() appends list to file."""
        f = tmp_path / "iter.txt"
        f.write_text("first\n")
        file = fs.File(str(f))
        file.append_iter(["a", "b"])
        content = file.read()
        assert content.startswith("first\n")
        assert "a\n" in content
        assert "b\n" in content


class TestFileOpen:
    def test_file_open_read(self, temp_file: File):
        """open() returns readable file handle."""
        with temp_file.open() as f:
            content = f.read()
        assert content == "hello world"

    def test_file_open_write(self, tmp_path: Path):
        """open('w') returns writable file handle."""
        file = fs.File(str(tmp_path / "open.txt"))
        with file.open("w") as f:
            f.write("new content")
        assert file.read() == "new content"

    def test_file_open_binary(self, tmp_path: Path):
        """open('rb') returns binary file handle."""
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x01\x02")
        file = fs.File(str(f))
        with file.open("rb") as handle:
            content = handle.read()
        assert content == b"\x00\x01\x02"

    def test_file_open_context_manager(self, temp_file: File):
        """open() works with with statement."""
        with temp_file.open() as f:
            content = f.read()
        assert f.closed
        assert content == "hello world"

    def test_file_open_encoding(self, tmp_path: Path):
        """open() respects encoding parameter."""
        f = tmp_path / "encoded.txt"
        f.write_bytes("café".encode("latin-1"))
        file = fs.File(str(f))
        with file.open(encoding="latin-1") as handle:
            content = handle.read()
        assert content == "café"

    def test_file_open_uses_file_encoding(self, tmp_path: Path):
        """open() uses self.encoding by default."""
        f = tmp_path / "encoded.txt"
        f.write_bytes("café".encode("latin-1"))
        file = fs.File(str(f), encoding="latin-1")
        with file.open() as handle:
            content = handle.read()
        assert content == "café"


class TestFileMoveCopy:
    def test_file_move_to(self, temp_file: File, tmp_path: Path):
        """move_to() moves file to directory."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        original_path = temp_file.path
        temp_file.move_to(str(dest_dir))
        assert not os.path.exists(original_path)
        assert temp_file.exists
        assert temp_file.dirname == str(dest_dir)

    def test_file_move_to_mkdir(self, temp_file: File, tmp_path: Path):
        """move_to(mkdir=True) creates directory."""
        dest_dir = tmp_path / "newdir"
        assert not dest_dir.exists()
        temp_file.move_to(str(dest_dir), mkdir=True)
        assert dest_dir.exists()
        assert temp_file.exists

    def test_file_move_to_no_overwrite(self, temp_file: File, tmp_path: Path):
        """move_to(overwrite=False) raises FileExistsError."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        existing = dest_dir / "test.txt"
        existing.write_text("existing")

        with pytest.raises(FileExistsError):
            temp_file.move_to(str(dest_dir), overwrite=False)

    def test_file_move_to_nonexistent_dir(self, temp_file: File, tmp_path: Path):
        """move_to() raises FileNotFoundError."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError):
            temp_file.move_to(str(nonexistent))

    def test_file_move_to_updates_path(self, temp_file: File, tmp_path: Path):
        """move_to() updates self.path."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        temp_file.move_to(str(dest_dir))
        assert str(dest_dir) in temp_file.path

    def test_file_copy_to(self, temp_file: File, tmp_path: Path):
        """copy_to() copies file to directory."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        original_path = temp_file.path
        temp_file.copy_to(str(dest_dir))
        assert os.path.exists(original_path)
        assert temp_file.exists
        assert temp_file.dirname == str(dest_dir)

    def test_file_copy_to_mkdir(self, temp_file: File, tmp_path: Path):
        """copy_to(mkdir=True) creates directory."""
        dest_dir = tmp_path / "newdir"
        assert not dest_dir.exists()
        temp_file.copy_to(str(dest_dir), mkdir=True)
        assert dest_dir.exists()
        assert temp_file.exists

    def test_file_copy_to_no_overwrite(self, temp_file: File, tmp_path: Path):
        """copy_to(overwrite=False) raises FileExistsError."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        existing = dest_dir / "test.txt"
        existing.write_text("existing")

        with pytest.raises(FileExistsError):
            temp_file.copy_to(str(dest_dir), overwrite=False)

    def test_file_copy_to_updates_path(self, temp_file: File, tmp_path: Path):
        """copy_to() updates self.path to copy."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        temp_file.copy_to(str(dest_dir))
        assert str(dest_dir) in temp_file.path


class TestFilePathManipulation:
    def test_file_with_dir(self, temp_file: File):
        """with_dir() changes directory portion."""
        new_dir = "/new/directory"
        temp_file.with_dir(new_dir)
        assert temp_file.dirname == new_dir
        assert temp_file.basename == "test.txt"

    def test_file_with_ext(self, temp_file: File):
        """with_ext() changes extension."""
        temp_file.with_ext("md")
        assert temp_file.ext == "md"
        assert temp_file.basename.endswith(".md")

    def test_file_with_ext_no_dot(self, temp_file: File):
        """with_ext('txt') adds dot automatically."""
        temp_file.with_ext("json")
        assert temp_file.suffix == ".json"

    def test_file_with_suffix(self, temp_file: File):
        """with_suffix() adds suffix before extension."""
        temp_file.with_suffix("_backup")
        assert "test_backup.txt" in temp_file.path

    def test_file_with_prefix(self, temp_file: File):
        """with_prefix() adds prefix to filename."""
        temp_file.with_prefix("new_")
        assert "new_test.txt" in temp_file.path


class TestFileRename:
    def test_file_rename(self, temp_file: File):
        """rename() renames file on disk."""
        original_path = temp_file.path
        temp_file.rename("renamed.txt")
        assert not os.path.exists(original_path)
        assert temp_file.exists
        assert temp_file.basename == "renamed.txt"

    def test_file_rename_updates_path(self, temp_file: File):
        """rename() updates self.path."""
        temp_file.rename("renamed.txt")
        assert "renamed.txt" in temp_file.path

    def test_file_rename_returns_self(self, temp_file: File):
        """rename() returns self for chaining."""
        result = temp_file.rename("renamed.txt")
        assert result is temp_file


class TestFilePathTransformations:
    def test_file_resolve(self, tmp_path: Path):
        """resolve() makes path absolute."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            f = tmp_path / "test.txt"
            f.touch()
            file = fs.File("test.txt")
            file.resolve()
            assert os.path.isabs(file.path)
        finally:
            os.chdir(original_cwd)

    def test_file_resolve_strict(self, tmp_path: Path):
        """resolve(strict=True) raises if not exists."""
        file = fs.File(str(tmp_path / "nonexistent.txt"))
        with pytest.raises(FileNotFoundError):
            file.resolve(strict=True)

    def test_file_relative_to(self, temp_file: File):
        """relative_to() returns relative path."""
        parent_dir = os.path.dirname(temp_file.path)
        relative = temp_file.relative_to(parent_dir)
        assert relative == "test.txt"

    def test_file_relative_to_not_relative(self, temp_file: File):
        """relative_to() raises ValueError."""
        with pytest.raises(ValueError):
            temp_file.relative_to("/completely/different/path")

    def test_file_expanduser(self, tmp_path: Path):
        """expanduser() expands ~."""
        file = fs.File("~/test.txt")
        file.expanduser()
        assert "~" not in file.path
        assert os.path.expanduser("~") in file.path

    def test_file_as_posix(self, temp_file: File):
        """as_posix() returns forward-slash path."""
        posix = temp_file.as_posix()
        assert "\\" not in posix
        assert "/" in posix

    def test_file_as_uri(self, temp_file: File):
        """as_uri() returns file:// URI."""
        uri = temp_file.as_uri()
        assert uri.startswith("file://")

    def test_file_as_uri_relative(self, tmp_path: Path):
        """as_uri() raises on relative path."""
        file = fs.File("relative/path.txt")
        with pytest.raises(ValueError):
            file.as_uri()

    def test_file_match(self, temp_file: File):
        """match() matches glob pattern."""
        assert temp_file.match("*.txt") is True
        assert temp_file.match("test.*") is True

    def test_file_match_no_match(self, temp_file: File):
        """match() returns False on no match."""
        assert temp_file.match("*.py") is False
        assert temp_file.match("other.*") is False

    def test_file_to_path(self, temp_file: File):
        """to_path() returns pathlib.Path."""
        p = temp_file.to_path()
        assert isinstance(p, Path)
        assert str(p) == temp_file.path

    def test_file_to_str(self, temp_file: File):
        """to_str() returns string."""
        s = temp_file.to_str()
        assert isinstance(s, str)
        assert s == temp_file.path


class TestFileAssertions:
    def test_file_should_exist(self, temp_file: File):
        """should_exist() passes for existing file."""
        result = temp_file.should_exist()
        assert result is temp_file

    def test_file_should_exist_raises(self, tmp_path: Path):
        """should_exist() raises FileNotFoundError."""
        file = fs.File(str(tmp_path / "nonexistent.txt"))
        with pytest.raises(FileNotFoundError):
            file.should_exist()

    def test_file_should_not_exist(self, tmp_path: Path):
        """should_not_exist() passes for missing file."""
        file = fs.File(str(tmp_path / "nonexistent.txt"))
        result = file.should_not_exist()
        assert result is file

    def test_file_should_not_exist_raises(self, temp_file: File):
        """should_not_exist() raises FileExistsError."""
        with pytest.raises(FileExistsError):
            temp_file.should_not_exist()


class TestFileLinks:
    def test_file_link(self, temp_file: File, tmp_path: Path):
        """link() creates hard link."""
        target = str(tmp_path / "hardlink.txt")
        result = temp_file.link(target)
        assert os.path.exists(target)
        assert os.stat(target).st_ino == os.stat(temp_file.path).st_ino
        assert result is temp_file

    def test_file_symlink(self, temp_file: File, tmp_path: Path):
        """symlink() creates symbolic link."""
        target = str(tmp_path / "symlink.txt")
        result = temp_file.symlink(target)
        assert os.path.islink(target)
        assert os.readlink(target) == temp_file.path
        assert result is temp_file


class TestFilePermissions:
    def test_file_chmod(self, temp_file: File):
        """chmod() changes permissions."""
        temp_file.chmod(0o400)
        mode = os.stat(temp_file.path).st_mode
        assert mode & 0o777 == 0o400
        temp_file.chmod(0o644)

    @pytest.mark.skipif(os.geteuid() != 0, reason="Requires root privileges")
    def test_file_chown(self, temp_file: File):
        """chown() changes owner (skip if not root)."""
        import grp
        import pwd

        user = pwd.getpwuid(os.getuid()).pw_name
        group = grp.getgrgid(os.getgid()).gr_name
        temp_file.chown(user, group)


class TestFileParents:
    def test_file_parents(self, temp_file: File):
        """parents returns tuple of Directory objects."""
        parents = temp_file.parents
        assert isinstance(parents, tuple)
        assert all(isinstance(p, fs.Directory) for p in parents)
        assert len(parents) > 0

    def test_file_parents_order(self, temp_file: File):
        """parents in order from immediate to root."""
        parents = temp_file.parents
        assert parents[0].path == temp_file.dirname
        if sys.platform != "win32":
            assert parents[-1].path == "/"


@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
class TestFileXattr:
    """Tests for extended attribute operations (Unix only)."""

    def test_file_set_xattr(self, temp_file: File):
        """set_xattr() sets extended attribute."""
        try:
            temp_file.set_xattr("test_value", "test_attr")
        except OSError as e:
            if e.errno == 95:  # EOPNOTSUPP
                pytest.skip("Extended attributes not supported on this filesystem")
            raise

    def test_file_get_xattr(self, temp_file: File):
        """get_xattr() retrieves extended attribute."""
        try:
            temp_file.set_xattr("test_value", "test_attr")
            value = temp_file.get_xattr("test_attr")
            assert value == "test_value"
        except OSError as e:
            if e.errno == 95:  # EOPNOTSUPP
                pytest.skip("Extended attributes not supported on this filesystem")
            raise

    def test_file_remove_xattr(self, temp_file: File):
        """remove_xattr() removes extended attribute."""
        try:
            temp_file.set_xattr("test_value", "test_attr")
            temp_file.remove_xattr("test_attr")
            with pytest.raises(OSError):
                temp_file.get_xattr("test_attr")
        except OSError as e:
            if e.errno == 95:  # EOPNOTSUPP
                pytest.skip("Extended attributes not supported on this filesystem")
            raise
