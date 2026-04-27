import os
import stat
import sys
import tempfile
import time
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
    assert set(files_found) == {str(i) for i in files}


def test_yield_files_in_with_ext():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        filenames = ["file1.txt", "file2.txt", "file3.csv", "barecsv"]
        files = [temp_dir_path / i for i in filenames]
        [i.touch() for i in files]
        files_found = fs.get_files_in(temp_dir, ext="csv")
    assert set(files_found) == {str(files[2])}


def test_yield_files_in_with_tuple_ext():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        filenames = ["file1.txt", "file2.txt", "file3.csv", "file4.py", "barepy"]
        files = [temp_dir_path / i for i in filenames]
        [i.touch() for i in files]
        files_found = fs.get_files_in(temp_dir, ext=("py", "csv"))
    assert set(files_found) == {str(files[2]), str(files[3])}


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

    assert set(files_found) == {str(i) for i in files}


def test_bytes_readable():
    assert fs.bytes_readable(0) == "0B"
    assert fs.bytes_readable(512) == "512.0 B"
    assert fs.bytes_readable(1024) == "1.0 KB"
    assert fs.bytes_readable(1048576) == "1.0 MB"
    assert fs.bytes_readable(1073741824) == "1.0 GB"
    assert fs.bytes_readable(1500) == "1.46 KB"

    with pytest.raises(ValueError, match=r"-1"):
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

    with pytest.raises(ValueError, match=r"Invalid size format"):
        fs.readable_size_to_bytes("1XB")
    with pytest.raises(ValueError, match=r"Invalid size format"):
        fs.readable_size_to_bytes("-1KB")
    with pytest.raises(ValueError, match=r"Invalid kb_size"):
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

    def test_file_path_is_read_only(self, temp_file: File):
        """Path is read-only."""
        with pytest.raises(AttributeError):
            temp_file.path = "other.txt"


class TestPathValueSemantics:
    def test_file_equality_normalizes_lexical_path(self):
        """File equality uses normalized lexical paths."""
        assert fs.File("a") == fs.File(f".{os.sep}a")

    def test_directory_equality_normalizes_trailing_separator(self):
        """Directory equality ignores trailing separators."""
        assert fs.Directory("dir") == fs.Directory(f"dir{os.sep}")

    def test_file_and_directory_are_not_equal(self):
        """Concrete type is part of path equality."""
        assert fs.File("a") != fs.Directory("a")

    def test_equal_paths_have_equal_hashes(self):
        """Equal path objects hash the same."""
        paths = {fs.File("a"), fs.File(f".{os.sep}a")}
        assert len(paths) == 1

    def test_file_equality_ignores_encoding(self):
        """File equality and hashing ignore encoding."""
        utf8 = fs.File("a", encoding="utf-8")
        latin1 = fs.File("a", encoding="latin-1")
        assert utf8 == latin1
        assert hash(utf8) == hash(latin1)


class TestFilePathComponents:
    def test_file_basename(self, temp_file: File):
        """Basename returns filename only."""
        assert temp_file.basename == "test.txt"

    def test_file_dirname(self, temp_file: File):
        """Dirname returns directory path."""
        dirname = temp_file.dirname
        assert os.path.isdir(dirname)
        assert "test.txt" not in dirname

    def test_file_parent(self, temp_file: File):
        """Parent returns Directory object."""
        parent = temp_file.parent
        assert isinstance(parent, fs.Directory)
        assert parent.path == os.path.dirname(temp_file.path)

    def test_file_ext(self, temp_file: File):
        """Ext returns extension without dot."""
        assert temp_file.ext == "txt"

    def test_file_ext_no_extension(self, tmp_path: Path):
        """Ext returns empty string for no extension."""
        f = tmp_path / "noext"
        f.touch()
        file = fs.File(str(f))
        assert file.ext == ""

    def test_file_ext_dotfile(self, tmp_path: Path):
        """Dotfiles without another dot have no extension."""
        f = tmp_path / ".gitignore"
        f.touch()
        file = fs.File(str(f))
        assert file.ext == ""

    def test_file_suffix(self, temp_file: File):
        """Suffix returns extension with dot."""
        assert temp_file.suffix == ".txt"

    def test_file_suffix_no_extension(self, tmp_path: Path):
        """Suffix returns empty string for no extension."""
        f = tmp_path / "noext"
        f.touch()
        file = fs.File(str(f))
        assert file.suffix == ""

    def test_file_suffix_dotfile(self, tmp_path: Path):
        """Suffix handles dotfiles correctly."""
        f = tmp_path / ".gitignore"
        f.touch()
        file = fs.File(str(f))
        assert file.suffix == ""

    def test_file_stem(self, temp_file: File):
        """Stem returns name without extension."""
        assert temp_file.stem == "test"

    def test_file_stem_no_extension(self, tmp_path: Path):
        """Stem returns full name when no extension."""
        f = tmp_path / "noext"
        f.touch()
        file = fs.File(str(f))
        assert file.stem == "noext"

    def test_file_stem_multiple_dots(self, tmp_path: Path):
        """Stem handles file.tar.gz correctly."""
        f = tmp_path / "archive.tar.gz"
        f.touch()
        file = fs.File(str(f))
        assert file.stem == "archive.tar"
        assert file.ext == "gz"

    def test_file_stem_dotfile(self, tmp_path: Path):
        """Dotfiles without another dot use the whole basename as their stem."""
        f = tmp_path / ".env"
        f.touch()
        file = fs.File(str(f))
        assert file.stem == ".env"
        assert file.suffix == ""
        assert file.ext == ""

    def test_file_abspath(self, tmp_path: Path):
        """Abspath returns absolute path."""
        f = tmp_path / "test.txt"
        f.touch()
        file = fs.File(str(f))
        assert os.path.isabs(file.abspath)

    def test_file_nodes(self, temp_file: File):
        """Nodes returns path parts as list."""
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
        """Size returns correct byte count."""
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

    def test_file_touch_creates_missing_file(self, tmp_path: Path):
        """touch() creates a missing file."""
        f = fs.File(str(tmp_path / "new.txt"))
        result = f.touch()
        assert result is f
        assert f.exists

    def test_file_touch_updates_mtime(self, temp_file: File):
        """touch() updates timestamps for an existing file."""
        before = temp_file.stat().st_mtime_ns
        time.sleep(0.01)
        temp_file.touch()
        after = temp_file.stat().st_mtime_ns
        assert after > before

    def test_file_touch_mkdir(self, tmp_path: Path):
        """touch(mkdir=True) creates missing parent directories."""
        f = fs.File(str(tmp_path / "nested" / "new.txt"))
        f.touch(mkdir=True)
        assert f.exists

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
        r"""readlines() returns list of lines with \n."""
        f = tmp_path / "lines.txt"
        f.write_text("line1\nline2\nline3\n")
        file = fs.File(str(f))
        lines = file.readlines()
        assert lines == ["line1\n", "line2\n", "line3\n"]

    def test_file_splitlines(self, tmp_path: Path):
        r"""splitlines() returns list without \n."""
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
        result = f.write_iter(["a", "b", "c"])
        content = f.read()
        assert result is f
        assert "a\n" in content
        assert "b\n" in content
        assert "c\n" in content

    def test_file_write_iter_custom_sep(self, tmp_path: Path):
        """write_iter(sep=',') uses custom separator."""
        f = fs.File(str(tmp_path / "iter.txt"))
        result = f.write_iter(["a", "b", "c"], sep=",")
        content = f.read()
        assert result is f
        assert content == "a,b,c,"

    def test_file_append_iter(self, tmp_path: Path):
        """append_iter() appends list to file."""
        f = tmp_path / "iter.txt"
        f.write_text("first\n")
        file = fs.File(str(f))
        result = file.append_iter(["a", "b"])
        content = file.read()
        assert result is file
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
        """move_to() returns a new File for the destination."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        original_path = temp_file.path
        moved_file = temp_file.move_to(fs.Directory(str(dest_dir)))
        assert not os.path.exists(original_path)
        assert not temp_file.exists
        assert temp_file.path == original_path
        assert moved_file.exists
        assert moved_file.dirname == str(dest_dir)
        assert moved_file is not temp_file

    def test_file_move_to_mkdir(self, temp_file: File, tmp_path: Path):
        """move_to(mkdir=True) creates directory and returns new File."""
        dest_dir = tmp_path / "newdir"
        assert not dest_dir.exists()
        moved_file = temp_file.move_to(fs.Directory(str(dest_dir)), mkdir=True)
        assert dest_dir.exists()
        assert moved_file.exists
        assert not temp_file.exists

    def test_file_move_to_no_overwrite(self, temp_file: File, tmp_path: Path):
        """move_to(overwrite=False) raises FileExistsError."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        existing = dest_dir / "test.txt"
        existing.write_text("existing")

        with pytest.raises(FileExistsError):
            temp_file.move_to(fs.Directory(str(dest_dir)), overwrite=False)

    def test_file_move_to_nonexistent_dir(self, temp_file: File, tmp_path: Path):
        """move_to() raises FileNotFoundError."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError):
            temp_file.move_to(fs.Directory(str(nonexistent)))

    def test_file_move_to_leaves_source_path_unchanged(self, temp_file: File, tmp_path: Path):
        """move_to() leaves the source object unchanged and returns a new File."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        original_path = temp_file.path
        moved_file = temp_file.move_to(fs.Directory(str(dest_dir)))
        assert temp_file.path == original_path
        assert moved_file.path == str(dest_dir / "test.txt")

    def test_file_move_to_exact_file_target(self, temp_file: File, tmp_path: Path):
        """move_to(File(...)) uses the exact destination path."""
        target = fs.File(str(tmp_path / "dest" / "renamed.txt"))
        moved_file = temp_file.move_to(target, mkdir=True)
        assert moved_file.path == target.path
        assert moved_file.exists
        assert moved_file.basename == "renamed.txt"
        assert not temp_file.exists

    def test_file_copy_to(self, temp_file: File, tmp_path: Path):
        """copy_to() returns a new File for the copy."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        original_path = temp_file.path
        copied_file = temp_file.copy_to(fs.Directory(str(dest_dir)))
        assert os.path.exists(original_path)
        assert temp_file.exists
        assert copied_file.exists
        assert copied_file.dirname == str(dest_dir)
        assert copied_file is not temp_file

    def test_file_copy_to_mkdir(self, temp_file: File, tmp_path: Path):
        """copy_to(mkdir=True) creates directory and returns new File."""
        dest_dir = tmp_path / "newdir"
        assert not dest_dir.exists()
        copied_file = temp_file.copy_to(fs.Directory(str(dest_dir)), mkdir=True)
        assert dest_dir.exists()
        assert temp_file.exists
        assert copied_file.exists

    def test_file_copy_to_no_overwrite(self, temp_file: File, tmp_path: Path):
        """copy_to(overwrite=False) raises FileExistsError."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        existing = dest_dir / "test.txt"
        existing.write_text("existing")

        with pytest.raises(FileExistsError):
            temp_file.copy_to(fs.Directory(str(dest_dir)), overwrite=False)

    def test_file_copy_to_leaves_source_path_unchanged(self, temp_file: File, tmp_path: Path):
        """copy_to() keeps the source path and returns a new File."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        original_path = temp_file.path
        copied_file = temp_file.copy_to(fs.Directory(str(dest_dir)))
        assert temp_file.path == original_path
        assert copied_file.path == str(dest_dir / "test.txt")

    def test_file_copy_to_exact_file_target(self, temp_file: File, tmp_path: Path):
        """copy_to(File(...)) uses the exact destination path."""
        target = fs.File(str(tmp_path / "dest" / "copied.txt"))
        copied_file = temp_file.copy_to(target, mkdir=True)
        assert copied_file.path == target.path
        assert copied_file.exists
        assert copied_file.basename == "copied.txt"
        assert temp_file.exists

    def test_file_copy_to_file_target_rejects_existing_directory(
        self, temp_file: File, tmp_path: Path
    ):
        """copy_to(File(existing_dir)) does not recursively remove directories."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        (existing_dir / "keep.txt").write_text("keep")

        with pytest.raises(IsADirectoryError):
            temp_file.copy_to(fs.File(str(existing_dir)))

        assert existing_dir.is_dir()
        assert (existing_dir / "keep.txt").read_text() == "keep"

    def test_file_move_to_same_directory_is_noop(self, temp_file: File, tmp_path: Path):
        """move_to(existing parent) is a no-op when the destination is the same path."""
        moved_file = temp_file.move_to(fs.Directory(str(tmp_path)))
        assert moved_file is not temp_file
        assert moved_file.path == temp_file.path
        assert moved_file.exists
        assert temp_file.exists
        assert Path(temp_file.path).read_text() == "hello world"

    def test_file_copy_to_same_directory_is_noop(self, temp_file: File, tmp_path: Path):
        """copy_to(existing parent) is a no-op when the destination is the same path."""
        copied_file = temp_file.copy_to(fs.Directory(str(tmp_path)))
        assert copied_file is not temp_file
        assert copied_file.path == temp_file.path
        assert copied_file.exists
        assert temp_file.exists
        assert Path(temp_file.path).read_text() == "hello world"

    def test_file_move_to_requires_typed_target(self, temp_file: File, tmp_path: Path):
        """move_to() rejects raw string targets."""
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        with pytest.raises(TypeError):
            temp_file.move_to(str(dest_dir))


class TestFilePathManipulation:
    def test_file_with_dir(self, temp_file: File):
        """with_dir() returns a new File with a changed directory."""
        new_dir = "/new/directory"
        original_path = temp_file.path
        new_file = temp_file.with_dir(new_dir)
        assert temp_file.path == original_path
        assert new_file.dirname == new_dir.replace("/", os.sep)
        assert new_file.basename == "test.txt"
        assert new_file is not temp_file

    def test_file_with_ext(self, temp_file: File):
        """with_ext() returns a new File with a changed extension."""
        original_path = temp_file.path
        new_file = temp_file.with_ext("md")
        assert temp_file.path == original_path
        assert new_file.ext == "md"
        assert new_file.basename.endswith(".md")

    def test_file_with_ext_no_dot(self, temp_file: File):
        """with_ext('txt') adds dot automatically."""
        new_file = temp_file.with_ext("json")
        assert new_file.suffix == ".json"

    def test_file_with_ext_dotfile(self, tmp_path: Path):
        """with_ext() appends an extension to extensionless dotfiles."""
        file = fs.File(str(tmp_path / ".env"))
        new_file = file.with_ext("txt")
        assert new_file.basename == ".env.txt"

    def test_file_with_suffix(self, temp_file: File):
        """with_suffix() returns a new File with a suffixed name."""
        original_path = temp_file.path
        new_file = temp_file.with_suffix("_backup")
        assert temp_file.path == original_path
        assert "test_backup.txt" in new_file.path

    def test_file_with_suffix_dotfile(self, tmp_path: Path):
        """with_suffix() appends before the extension, preserving dotfile names."""
        file = fs.File(str(tmp_path / ".env"))
        new_file = file.with_suffix("_bak")
        assert new_file.basename == ".env_bak"

    def test_file_with_prefix(self, temp_file: File):
        """with_prefix() returns a new File with a prefixed name."""
        original_path = temp_file.path
        new_file = temp_file.with_prefix("new_")
        assert temp_file.path == original_path
        assert "new_test.txt" in new_file.path

    def test_file_with_name(self, temp_file: File):
        """with_name() returns new File with different name."""
        original_dir = temp_file.dirname
        new_file = temp_file.with_name("other.py")
        assert new_file.basename == "other.py"
        assert new_file.dirname == original_dir
        assert new_file is not temp_file

    def test_file_with_name_no_parent(self):
        """with_name() works with no parent directory."""
        f = fs.File("just_a_file.txt")
        new_f = f.with_name("renamed.py")
        assert new_f.path == "renamed.py"

    def test_file_with_stem(self, temp_file: File):
        """with_stem() returns new File with different stem."""
        new_file = temp_file.with_stem("different")
        assert new_file.stem == "different"
        assert new_file.suffix == ".txt"
        assert new_file is not temp_file

    def test_file_with_stem_no_extension(self, tmp_path: Path):
        """with_stem() works with files without extension."""
        f = tmp_path / "noext"
        f.touch()
        file = fs.File(str(f))
        new_file = file.with_stem("changed")
        assert new_file.basename == "changed"
        assert new_file.suffix == ""

    def test_file_clone_methods_preserve_encoding(self, tmp_path: Path):
        """Clone-returning methods preserve custom File encoding."""
        path = tmp_path / "encoded.txt"
        path.write_bytes("café".encode("latin-1"))
        file = fs.File(str(path), encoding="latin-1")
        renamed = file.with_name("other.txt")
        resolved = file.resolve()
        assert renamed.encoding == "latin-1"
        assert resolved.encoding == "latin-1"


class TestFileRename:
    def test_file_rename(self, temp_file: File):
        """rename() returns a new File for the renamed path."""
        original_path = temp_file.path
        renamed_file = temp_file.rename("renamed.txt")
        assert not os.path.exists(original_path)
        assert not temp_file.exists
        assert temp_file.path == original_path
        assert renamed_file.exists
        assert renamed_file.basename == "renamed.txt"

    def test_file_rename_returns_new_object(self, temp_file: File):
        """rename() returns a distinct File object."""
        renamed_file = temp_file.rename("renamed.txt")
        assert renamed_file is not temp_file
        assert renamed_file.basename == "renamed.txt"

    def test_file_rename_leaves_source_path_unchanged(self, temp_file: File):
        """rename() leaves the source object path unchanged."""
        original_path = temp_file.path
        result = temp_file.rename("renamed.txt")
        assert temp_file.path == original_path
        assert result.path.endswith("renamed.txt")


class TestFilePathTransformations:
    def test_file_resolve(self, tmp_path: Path):
        """resolve() returns a new absolute File."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            f = tmp_path / "test.txt"
            f.touch()
            file = fs.File("test.txt")
            resolved_file = file.resolve()
            assert file.path == "test.txt"
            assert os.path.isabs(resolved_file.path)
            assert resolved_file is not file
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
        with pytest.raises(ValueError, match=r"is not relative to"):
            temp_file.relative_to("/completely/different/path")

    def test_file_expanduser(self, tmp_path: Path):
        """expanduser() returns a new File with ~ expanded."""
        file = fs.File("~/test.txt")
        expanded_file = file.expanduser()
        assert file.path == os.path.join("~", "test.txt")
        assert "~" not in expanded_file.path
        assert os.path.expanduser("~") in expanded_file.path

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
        with pytest.raises(ValueError, match=r"file URI"):
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
    @pytest.mark.skipif(
        sys.platform == "win32", reason="follow_symlinks=True unavailable on Windows"
    )
    def test_file_link(self, temp_file: File, tmp_path: Path):
        """link() creates hard link."""
        target = str(tmp_path / "hardlink.txt")
        result = temp_file.link(target)
        assert os.path.exists(target)
        assert os.stat(target).st_ino == os.stat(temp_file.path).st_ino
        assert result is not temp_file
        assert result.path == target
        assert result.encoding == temp_file.encoding

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Windows symlinks return extended path format"
    )
    def test_file_symlink(self, temp_file: File, tmp_path: Path):
        """symlink() creates symbolic link."""
        target = str(tmp_path / "symlink.txt")
        result = temp_file.symlink(target)
        assert os.path.islink(target)
        assert os.readlink(target) == temp_file.path
        assert result is not temp_file
        assert result.path == target
        assert result.encoding == temp_file.encoding

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Windows symlinks return extended path format"
    )
    def test_file_symlink_relative_source_to_nested_target(self, tmp_path: Path):
        """symlink() keeps relative source paths valid for targets in another directory."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            Path("src.txt").write_text("content")
            Path("links").mkdir()

            result = fs.File("src.txt").symlink("links/link.txt")

            assert result.path == os.path.join("links", "link.txt")
            assert os.path.islink("links/link.txt")
            assert os.readlink("links/link.txt") == os.path.join("..", "src.txt")
            assert os.path.samefile("links/link.txt", "src.txt")
        finally:
            os.chdir(original_cwd)

    def test_file_samefile(self, temp_file: File, tmp_path: Path):
        """samefile() detects matching filesystem entries."""
        target = str(tmp_path / "hardlink.txt")
        temp_file.link(target)
        assert temp_file.samefile(target) is True

    def test_file_readlink(self, temp_file: File, tmp_path: Path):
        """readlink() returns the symlink target path."""
        target = str(tmp_path / "symlink.txt")
        temp_file.symlink(target)
        assert os.path.samefile(fs.File(target).readlink(), temp_file.path)


class TestFilePermissions:
    @pytest.mark.skipif(
        sys.platform == "win32", reason="Windows does not support Unix-style permissions"
    )
    def test_file_chmod(self, temp_file: File):
        """chmod() changes permissions."""
        temp_file.chmod(0o400)
        mode = os.stat(temp_file.path).st_mode
        assert mode & 0o777 == 0o400
        temp_file.chmod(0o644)

    @pytest.mark.skipif(
        not hasattr(os, "geteuid") or os.geteuid() != 0,
        reason="Requires root privileges on Unix",
    )
    def test_file_chown(self, temp_file: File):
        """chown() changes owner (skip if not root)."""
        import grp
        import pwd

        user = pwd.getpwuid(os.getuid()).pw_name
        group = grp.getgrgid(os.getgid()).gr_name
        temp_file.chown(user, group)

    @pytest.mark.skipif(sys.platform == "win32", reason="owner/group not supported on Windows")
    def test_file_owner_group(self, temp_file: File):
        """owner() and group() return filesystem identity names."""
        import grp
        import pwd

        assert temp_file.owner() == pwd.getpwuid(os.getuid()).pw_name
        assert temp_file.group() == grp.getgrgid(os.getgid()).gr_name


class TestFileParents:
    def test_file_parents(self, temp_file: File):
        """Parents returns tuple of Directory objects."""
        parents = temp_file.parents
        assert isinstance(parents, tuple)
        assert all(isinstance(p, fs.Directory) for p in parents)
        assert len(parents) > 0

    def test_file_parents_order(self, temp_file: File):
        """Parents in order from immediate to root."""
        parents = temp_file.parents
        assert parents[0].path == temp_file.dirname
        if sys.platform != "win32":
            assert parents[-1].path == "/"


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="Linux only - os.setxattr not available on macOS/Windows",
)
class TestFileXattr:
    """Tests for extended attribute operations (Linux only)."""

    def test_file_set_xattr(self, temp_file: File):
        """set_xattr() sets extended attribute."""
        try:
            result = temp_file.set_xattr("test_value", "test_attr")
            assert result is temp_file
            assert isinstance(result, fs.File)
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
            with pytest.raises(OSError, match=r".*"):
                temp_file.get_xattr("test_attr")
        except OSError as e:
            if e.errno == 95:  # EOPNOTSUPP
                pytest.skip("Extended attributes not supported on this filesystem")
            raise


@pytest.fixture
def temp_directory(tmp_path: Path) -> fs.Directory:
    """Create a temporary directory with some files."""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")
    (test_dir / "file3.py").write_text("print('hello')")
    return fs.Directory(str(test_dir))


@pytest.fixture
def nested_directory(tmp_path: Path) -> fs.Directory:
    """Create a nested directory structure."""
    root = tmp_path / "root"
    root.mkdir()
    (root / "file1.txt").write_text("root file")
    sub1 = root / "sub1"
    sub1.mkdir()
    (sub1 / "sub1_file.txt").write_text("sub1 content")
    sub2 = root / "sub2"
    sub2.mkdir()
    (sub2 / "sub2_file.py").write_text("print('sub2')")
    deep = sub1 / "deep"
    deep.mkdir()
    (deep / "deep_file.txt").write_text("deep content")
    return fs.Directory(str(root))


class TestDirectoryInit:
    def test_directory_init(self, tmp_path: Path):
        """Create Directory with string path."""
        path = str(tmp_path / "testdir")
        directory = fs.Directory(path)
        assert directory.path == path

    def test_directory_init_with_pathlike(self, tmp_path: Path):
        """Create Directory with PathLike object."""
        path = tmp_path / "testdir"
        directory = fs.Directory(path)
        assert directory.path == str(path)

    def test_directory_init_abs(self, tmp_path: Path):
        """Create Directory with abs=True."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            directory = fs.Directory("testdir", abs=True)
            assert os.path.isabs(directory.path)
            assert directory.path == os.path.abspath("testdir")
        finally:
            os.chdir(original_cwd)

    def test_directory_exists_true(self, temp_directory: fs.Directory):
        """Check exists returns True for existing directory."""
        assert temp_directory.exists is True

    def test_directory_exists_false(self, tmp_path: Path):
        """Check exists returns False for non-existent directory."""
        directory = fs.Directory(str(tmp_path / "nonexistent"))
        assert directory.exists is False

    def test_directory_path_property(self, temp_directory: fs.Directory):
        """Verify path returns correct string."""
        assert isinstance(temp_directory.path, str)
        assert temp_directory.path.endswith("testdir")

    def test_directory_fspath(self, temp_directory: fs.Directory):
        """Verify __fspath__ protocol."""
        assert os.fspath(temp_directory) == temp_directory.path

    def test_directory_str(self, temp_directory: fs.Directory):
        """Verify __str__ returns path."""
        assert str(temp_directory) == temp_directory.path

    def test_directory_path_is_read_only(self, temp_directory: fs.Directory):
        """Path is read-only."""
        with pytest.raises(AttributeError):
            temp_directory.path = "otherdir"


class TestDirectoryPathComponents:
    def test_directory_basename(self, temp_directory: fs.Directory):
        """Basename returns directory name only."""
        assert temp_directory.basename == "testdir"

    def test_directory_parent(self, temp_directory: fs.Directory):
        """Parent returns Directory object."""
        parent = temp_directory.parent
        assert isinstance(parent, fs.Directory)
        assert parent.path == os.path.dirname(temp_directory.path)

    def test_directory_abspath(self, tmp_path: Path):
        """Abspath returns absolute path."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        directory = fs.Directory(str(test_dir))
        assert os.path.isabs(directory.abspath)

    def test_directory_nodes(self, temp_directory: fs.Directory):
        """Nodes returns path parts as list."""
        nodes = temp_directory.nodes
        assert isinstance(nodes, list)
        assert "testdir" in nodes


class TestDirectoryPathBooleans:
    def test_directory_is_absolute_true(self, temp_directory: fs.Directory):
        """is_absolute returns True for absolute path."""
        assert temp_directory.is_absolute is True

    def test_directory_is_absolute_false(self, tmp_path: Path):
        """is_absolute returns False for relative path."""
        directory = fs.Directory("relative/path")
        assert directory.is_absolute is False

    def test_directory_is_symlink_true(self, tmp_path: Path):
        """is_symlink returns True for symlink."""
        target = tmp_path / "target"
        target.mkdir()
        link = tmp_path / "link"
        link.symlink_to(target)
        directory = fs.Directory(str(link))
        assert directory.is_symlink is True

    def test_directory_is_symlink_false(self, temp_directory: fs.Directory):
        """is_symlink returns False for regular directory."""
        assert temp_directory.is_symlink is False


class TestDirectoryMetadata:
    def test_directory_size(self, temp_directory: fs.Directory):
        """Size returns total size of directory."""
        size = temp_directory.size
        assert isinstance(size, int)
        assert size > 0

    def test_directory_size_empty(self, tmp_path: Path):
        """Size returns 0 for empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        directory = fs.Directory(str(empty_dir))
        assert directory.size == 0

    def test_directory_size_readable(self, temp_directory: fs.Directory):
        """size_readable returns human-readable directory size."""
        readable = temp_directory.size_readable
        assert isinstance(readable, str)
        assert "B" in readable

    def test_directory_ctime(self, temp_directory: fs.Directory):
        """ctime/created returns creation timestamp."""
        ctime = temp_directory.ctime
        assert isinstance(ctime, float)
        assert ctime > 0
        assert temp_directory.created == ctime

    def test_directory_mtime(self, temp_directory: fs.Directory):
        """mtime/modified returns modification timestamp."""
        mtime = temp_directory.mtime
        assert isinstance(mtime, float)
        assert mtime > 0
        assert temp_directory.modified == mtime

    def test_directory_atime(self, temp_directory: fs.Directory):
        """atime/accessed returns access timestamp."""
        atime = temp_directory.atime
        assert isinstance(atime, float)
        assert atime > 0
        assert temp_directory.accessed == atime

    def test_directory_stat(self, temp_directory: fs.Directory):
        """stat() returns os.stat_result."""
        result = temp_directory.stat()
        assert isinstance(result, os.stat_result)
        assert stat.S_ISDIR(result.st_mode)


class TestDirectoryCreationDeletion:
    def test_directory_create(self, tmp_path: Path):
        """create() creates new directory."""
        directory = fs.Directory(str(tmp_path / "newdir"))
        assert not directory.exists
        directory.create()
        assert directory.exists

    def test_directory_create_nested(self, tmp_path: Path):
        """create() creates nested directories."""
        directory = fs.Directory(str(tmp_path / "a" / "b" / "c"))
        assert not directory.exists
        directory.create()
        assert directory.exists

    def test_directory_create_existing(self, temp_directory: fs.Directory):
        """create() on existing directory does nothing."""
        temp_directory.create()
        assert temp_directory.exists

    def test_directory_create_returns_self(self, tmp_path: Path):
        """create() returns self for chaining."""
        directory = fs.Directory(str(tmp_path / "newdir"))
        result = directory.create()
        assert result is directory

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Windows does not support Unix-style permissions"
    )
    def test_directory_create_with_mode(self, tmp_path: Path):
        """create() respects mode parameter."""
        directory = fs.Directory(str(tmp_path / "modedir"))
        directory.create(mode=0o755)
        assert directory.exists
        mode = os.stat(directory.path).st_mode
        assert mode & 0o777 == 0o755

    def test_directory_remove(self, temp_directory: fs.Directory):
        """remove() deletes directory and contents."""
        assert temp_directory.exists
        temp_directory.remove()
        assert not temp_directory.exists

    def test_directory_remove_nonexistent(self, tmp_path: Path):
        """remove() on non-existent directory does nothing."""
        directory = fs.Directory(str(tmp_path / "nonexistent"))
        directory.remove()

    def test_directory_remove_returns_self(self, temp_directory: fs.Directory):
        """remove() returns self for chaining."""
        result = temp_directory.remove()
        assert result is temp_directory

    def test_directory_clear(self, temp_directory: fs.Directory):
        """clear() removes contents but keeps the directory."""
        temp_directory.clear()
        assert temp_directory.exists
        assert temp_directory.get_files(recursive=True) == []

    def test_directory_clear_nonexistent(self, tmp_path: Path):
        """clear() on a missing directory is a no-op."""
        directory = fs.Directory(str(tmp_path / "missing"))
        result = directory.clear()
        assert result is directory


class TestDirectoryOperators:
    def test_directory_truediv(self, temp_directory: fs.Directory):
        """/ operator returns sub-Directory."""
        sub = temp_directory / "subdir"
        assert isinstance(sub, fs.Directory)
        assert sub.path.endswith("subdir")
        assert temp_directory.path in sub.path

    def test_directory_floordiv(self, temp_directory: fs.Directory):
        """// operator returns File in directory."""
        file_obj = temp_directory // "myfile.txt"
        assert isinstance(file_obj, fs.File)
        assert file_obj.path.endswith("myfile.txt")
        assert temp_directory.path in file_obj.path


class TestDirectoryFileAccess:
    def test_directory_file(self, temp_directory: fs.Directory):
        """file() returns File object."""
        file_obj = temp_directory.file("test.txt")
        assert isinstance(file_obj, fs.File)
        assert file_obj.basename == "test.txt"
        assert temp_directory.path in file_obj.path

    def test_directory_directory(self, temp_directory: fs.Directory):
        """directory() returns Directory object."""
        sub_dir = temp_directory.directory("subdir")
        assert isinstance(sub_dir, fs.Directory)
        assert sub_dir.basename == "subdir"
        assert temp_directory.path in sub_dir.path


class TestDirectoryEntries:
    def test_directory_yield_entries(self, nested_directory: fs.Directory):
        """yield_entries() returns immediate mixed child entries."""
        entries = list(nested_directory.yield_entries())
        assert len(entries) == 3
        assert {entry.basename for entry in entries} == {"file1.txt", "sub1", "sub2"}
        assert any(isinstance(entry, fs.File) for entry in entries)
        assert any(isinstance(entry, fs.Directory) for entry in entries)

    def test_directory_get_entries(self, nested_directory: fs.Directory):
        """get_entries() materializes the immediate mixed child list."""
        entries = nested_directory.get_entries()
        assert isinstance(entries, list)
        assert len(entries) == 3


class TestDirectoryWalk:
    def test_directory_walk(self, nested_directory: fs.Directory):
        """walk() yields grouped top-down traversal tuples."""
        walked = list(nested_directory.walk())
        root_names = [root.basename for root, _, _ in walked]
        assert root_names[0] == "root"
        assert set(root_names[1:]) == {"sub1", "deep", "sub2"}

        walked_by_root = {root.basename: (subdirs, files) for root, subdirs, files in walked}
        root_subdirs, root_files = walked_by_root["root"]
        assert {entry.basename for entry in root_subdirs} == {"sub1", "sub2"}
        assert [entry.basename for entry in root_files] == ["file1.txt"]

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Windows symlinks return extended path format"
    )
    def test_directory_walk_does_not_follow_symlink_dirs(self, tmp_path: Path):
        """walk(follow_symlinks=False) includes symlink dirs but does not recurse into them."""
        root = tmp_path / "root"
        root.mkdir()
        real = root / "real"
        real.mkdir()
        (real / "inside.txt").write_text("content")
        link = root / "linked"
        link.symlink_to(real, target_is_directory=True)

        walked = list(fs.Directory(str(root)).walk())
        assert {entry.basename for entry in walked[0][1]} == {"real", "linked"}
        assert [current.basename for current, _, _ in walked] == ["root", "real"]


class TestDirectoryYieldFiles:
    def test_directory_yield_files(self, temp_directory: fs.Directory):
        """yield_files() yields File objects."""
        files = list(temp_directory.yield_files())
        assert len(files) == 3
        assert all(isinstance(file_obj, fs.File) for file_obj in files)

    def test_directory_yield_files_ext(self, temp_directory: fs.Directory):
        """yield_files(ext='txt') filters by extension."""
        files = list(temp_directory.yield_files(ext="txt"))
        assert len(files) == 2
        assert all(file_obj.ext == "txt" for file_obj in files)

    def test_directory_yield_files_tuple_ext(self, temp_directory: fs.Directory):
        """yield_files(ext=('txt', 'py')) filters by multiple extensions."""
        files = list(temp_directory.yield_files(ext=("txt", "py")))
        assert len(files) == 3

    def test_directory_yield_files_glob(self, temp_directory: fs.Directory):
        """yield_files(glob='file*.txt') filters by glob pattern."""
        files = list(temp_directory.yield_files(glob="file*.txt"))
        assert len(files) == 2
        assert all("file" in file_obj.basename and file_obj.ext == "txt" for file_obj in files)

    def test_directory_yield_files_regex(self, temp_directory: fs.Directory):
        r"""yield_files(regex=r'\d') filters by regex."""
        files = list(temp_directory.yield_files(regex=r"\d"))
        assert len(files) == 3

    def test_directory_yield_files_recursive(self, nested_directory: fs.Directory):
        """yield_files(recursive=True) finds nested files."""
        files = list(nested_directory.yield_files(recursive=True))
        assert len(files) == 4

    def test_directory_yield_files_non_recursive(self, nested_directory: fs.Directory):
        """yield_files(recursive=False) only top-level."""
        files = list(nested_directory.yield_files(recursive=False))
        assert len(files) == 1

    def test_directory_yield_files_combined_filters(self, nested_directory: fs.Directory):
        """yield_files with multiple filters uses AND logic."""
        files = list(nested_directory.yield_files(ext="txt", glob="*file*"))
        basenames = [file_obj.basename for file_obj in files]
        assert all("file" in name and name.endswith(".txt") for name in basenames)

    @pytest.mark.skipif(os.name == "nt", reason="symlink behavior is platform-specific")
    def test_directory_yield_files_avoids_symlink_cycles(self, tmp_path: Path):
        """yield_files() does not recurse forever through symlink directory cycles."""
        root = tmp_path / "root"
        child = root / "child"
        child.mkdir(parents=True)
        (child / "file.txt").write_text("x")
        (child / "back").symlink_to(root, target_is_directory=True)

        files = list(fs.Directory(str(root)).yield_files())

        assert [Path(file.path).relative_to(root) for file in files] == [Path("child/file.txt")]


class TestDirectoryGetFiles:
    def test_directory_get_files(self, temp_directory: fs.Directory):
        """get_files() returns list of File objects."""
        files = temp_directory.get_files()
        assert isinstance(files, list)
        assert len(files) == 3
        assert all(isinstance(file_obj, fs.File) for file_obj in files)

    def test_directory_get_files_ext(self, temp_directory: fs.Directory):
        """get_files(ext='py') filters by extension."""
        files = temp_directory.get_files(ext="py")
        assert len(files) == 1
        assert files[0].ext == "py"


class TestDirectoryYieldSubdirs:
    def test_directory_yield_subdirs(self, nested_directory: fs.Directory):
        """yield_subdirs() yields Directory objects."""
        subdirs = list(nested_directory.yield_subdirs())
        assert len(subdirs) == 3
        assert all(isinstance(sub_dir, fs.Directory) for sub_dir in subdirs)

    def test_directory_yield_subdirs_non_recursive(self, nested_directory: fs.Directory):
        """yield_subdirs(recursive=False) only immediate subdirs."""
        subdirs = list(nested_directory.yield_subdirs(recursive=False))
        assert len(subdirs) == 2

    def test_directory_yield_subdirs_glob(self, nested_directory: fs.Directory):
        """yield_subdirs(glob='sub*') filters by pattern."""
        subdirs = list(nested_directory.yield_subdirs(glob="sub*"))
        assert len(subdirs) == 2
        assert all(sub_dir.basename.startswith("sub") for sub_dir in subdirs)

    def test_directory_yield_subdirs_regex(self, nested_directory: fs.Directory):
        r"""yield_subdirs(regex=r'\d') filters by regex."""
        subdirs = list(nested_directory.yield_subdirs(regex=r"\d"))
        assert len(subdirs) == 2

    @pytest.mark.skipif(os.name == "nt", reason="symlink behavior is platform-specific")
    def test_directory_yield_subdirs_avoids_symlink_cycles(self, tmp_path: Path):
        """yield_subdirs() yields symlink dirs without recursing forever through cycles."""
        root = tmp_path / "root"
        child = root / "child"
        child.mkdir(parents=True)
        (child / "back").symlink_to(root, target_is_directory=True)

        subdirs = list(fs.Directory(str(root)).yield_subdirs())

        assert [Path(directory.path).relative_to(root) for directory in subdirs] == [
            Path("child"),
            Path("child/back"),
        ]


class TestDirectoryGetSubdirs:
    def test_directory_get_subdirs(self, nested_directory: fs.Directory):
        """get_subdirs() returns list of Directory objects."""
        subdirs = nested_directory.get_subdirs()
        assert isinstance(subdirs, list)
        assert len(subdirs) == 3
        assert all(isinstance(sub_dir, fs.Directory) for sub_dir in subdirs)

    def test_directory_get_subdirs_non_recursive(self, nested_directory: fs.Directory):
        """get_subdirs(recursive=False) only immediate subdirs."""
        subdirs = nested_directory.get_subdirs(recursive=False)
        assert len(subdirs) == 2


class TestDirectoryMoveCopy:
    def test_directory_move_to(self, temp_directory: fs.Directory, tmp_path: Path):
        """move_to() places the directory inside the target directory."""
        dest_path = tmp_path / "dest"
        dest_path.mkdir()
        dest = fs.Directory(str(dest_path))
        original_path = temp_directory.path
        moved_dir = temp_directory.move_to(dest)
        assert not os.path.exists(original_path)
        assert not temp_directory.exists
        assert temp_directory.path == original_path
        assert moved_dir.exists
        assert moved_dir.path == str(dest_path / temp_directory.basename)

    def test_directory_move_to_returns_new_object(
        self, temp_directory: fs.Directory, tmp_path: Path
    ):
        """move_to() returns a distinct Directory object."""
        dest_path = tmp_path / "dest"
        dest_path.mkdir()
        dest = fs.Directory(str(dest_path))
        moved_dir = temp_directory.move_to(dest)
        assert moved_dir is not temp_directory
        assert moved_dir.path == str(dest_path / temp_directory.basename)

    def test_directory_move_to_nonexistent(self, temp_directory: fs.Directory, tmp_path: Path):
        """move_to() raises FileNotFoundError when the target directory is missing."""
        nonexistent = fs.Directory(str(tmp_path / "missing-parent" / "dest"))
        with pytest.raises(FileNotFoundError):
            temp_directory.move_to(nonexistent)

    def test_directory_move_to_leaves_source_path_unchanged(
        self, temp_directory: fs.Directory, tmp_path: Path
    ):
        """move_to() leaves the source object path unchanged."""
        dest_path = tmp_path / "dest"
        dest_path.mkdir()
        dest = fs.Directory(str(dest_path))
        original_path = temp_directory.path
        result = temp_directory.move_to(dest)
        assert temp_directory.path == original_path
        assert result.path == str(dest_path / temp_directory.basename)

    def test_directory_copy_to(self, temp_directory: fs.Directory, tmp_path: Path):
        """copy_to() places the directory inside the target directory."""
        dest_path = tmp_path / "dest"
        dest_path.mkdir()
        dest = fs.Directory(str(dest_path))
        original_path = temp_directory.path
        copied_dir = temp_directory.copy_to(dest)
        assert os.path.exists(original_path)
        assert temp_directory.exists
        assert copied_dir.exists
        assert copied_dir.path == str(dest_path / temp_directory.basename)

    def test_directory_copy_to_mkdir(self, temp_directory: fs.Directory, tmp_path: Path):
        """copy_to(mkdir=True) creates the target directory before copying into it."""
        dest = fs.Directory(str(tmp_path / "newparent" / "dest"))
        assert not Path(dest.path).exists()
        copied_dir = temp_directory.copy_to(dest, mkdir=True)
        assert Path(dest.path).exists()
        assert temp_directory.exists
        assert copied_dir.exists
        assert copied_dir.path == str(Path(dest.path) / temp_directory.basename)

    def test_directory_copy_to_nonexistent(self, temp_directory: fs.Directory, tmp_path: Path):
        """copy_to() raises FileNotFoundError when the target directory is missing."""
        nonexistent = fs.Directory(str(tmp_path / "missing-parent" / "dest"))
        with pytest.raises(FileNotFoundError):
            temp_directory.copy_to(nonexistent)

    def test_directory_copy_to_leaves_source_path_unchanged(
        self, temp_directory: fs.Directory, tmp_path: Path
    ):
        """copy_to() keeps the source path and returns a new Directory."""
        dest_path = tmp_path / "dest"
        dest_path.mkdir()
        dest = fs.Directory(str(dest_path))
        original_path = temp_directory.path
        result = temp_directory.copy_to(dest)
        assert temp_directory.path == original_path
        assert result.path == str(dest_path / temp_directory.basename)

    def test_directory_move_to_same_parent_is_noop(
        self, temp_directory: fs.Directory, tmp_path: Path
    ):
        """move_to(existing parent) is a no-op when the destination is the same path."""
        moved_dir = temp_directory.move_to(fs.Directory(str(tmp_path)))
        assert moved_dir is not temp_directory
        assert moved_dir.path == temp_directory.path
        assert moved_dir.exists
        assert temp_directory.exists

    def test_directory_copy_to_same_parent_is_noop(
        self, temp_directory: fs.Directory, tmp_path: Path
    ):
        """copy_to(existing parent) is a no-op when the destination is the same path."""
        copied_dir = temp_directory.copy_to(fs.Directory(str(tmp_path)))
        assert copied_dir is not temp_directory
        assert copied_dir.path == temp_directory.path
        assert copied_dir.exists
        assert temp_directory.exists

    def test_directory_copy_to_preserves_subdirectory_basename(
        self, nested_directory: fs.Directory, tmp_path: Path
    ):
        """Mixed entry copies preserve directory basenames under the destination root."""
        dest_root = tmp_path / "dest"
        dest_root.mkdir()

        for entry in nested_directory.yield_entries():
            entry.copy_to(fs.Directory(str(dest_root)))

        assert (dest_root / "file1.txt").read_text() == "root file"
        assert (dest_root / "sub1" / "sub1_file.txt").read_text() == "sub1 content"
        assert (dest_root / "sub1" / "deep" / "deep_file.txt").read_text() == "deep content"
        assert (dest_root / "sub2" / "sub2_file.py").read_text() == "print('sub2')"

    def test_directory_move_to_requires_typed_target(
        self, temp_directory: fs.Directory, tmp_path: Path
    ):
        """move_to() rejects raw string targets."""
        dest = tmp_path / "dest"
        with pytest.raises(TypeError):
            temp_directory.move_to(str(dest))

    def test_directory_copy_to_into_itself_raises(self, temp_directory: fs.Directory):
        """copy_to() rejects destinations nested under the source directory."""
        with pytest.raises(ValueError, match="into itself"):
            temp_directory.copy_to(temp_directory.directory("nested"), mkdir=True)

    def test_directory_move_to_into_itself_raises(self, temp_directory: fs.Directory):
        """move_to() rejects destinations nested under the source directory."""
        with pytest.raises(ValueError, match="into itself"):
            temp_directory.move_to(temp_directory.directory("nested"), mkdir=True)

    @pytest.mark.skipif(os.name == "nt", reason="symlink behavior is platform-specific")
    def test_directory_copy_to_rejects_symlinked_source_child(self, tmp_path: Path):
        """copy_to() rejects destinations nested under the resolved source directory."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("data")
        link_to_source = tmp_path / "link-to-source"
        link_to_source.symlink_to(source, target_is_directory=True)

        with pytest.raises(ValueError, match="into itself"):
            fs.Directory(str(source)).copy_to(fs.Directory(str(link_to_source)))

        assert sorted(path.relative_to(source) for path in source.rglob("*")) == [Path("file.txt")]

    @pytest.mark.skipif(os.name == "nt", reason="symlink behavior is platform-specific")
    def test_directory_move_to_rejects_symlinked_source_child(self, tmp_path: Path):
        """move_to() rejects destinations nested under the resolved source directory."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("data")
        link_to_source = tmp_path / "link-to-source"
        link_to_source.symlink_to(source, target_is_directory=True)

        with pytest.raises(ValueError, match="into itself"):
            fs.Directory(str(source)).move_to(fs.Directory(str(link_to_source)))

        assert source.exists()
        assert link_to_source.exists()
        assert link_to_source.is_symlink()

    @pytest.mark.skipif(os.name == "nt", reason="symlink behavior is platform-specific")
    def test_directory_move_to_same_location_through_symlink_is_noop(self, tmp_path: Path):
        """move_to() treats a symlinked destination parent resolving to the same path as a no-op."""
        source = tmp_path / "source"
        source.mkdir()
        link_to_parent = tmp_path / "link-to-parent"
        link_to_parent.symlink_to(tmp_path, target_is_directory=True)

        moved = fs.Directory(str(source)).move_to(fs.Directory(str(link_to_parent)))

        assert moved.path == str(link_to_parent / "source")
        assert source.exists()
        assert link_to_parent.exists()


class TestDirectoryPathTransformations:
    def test_directory_resolve(self, tmp_path: Path):
        """resolve() returns a new absolute Directory."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            test_dir = tmp_path / "testdir"
            test_dir.mkdir()
            directory = fs.Directory("testdir")
            resolved_dir = directory.resolve()
            assert directory.path == "testdir"
            assert os.path.isabs(resolved_dir.path)
        finally:
            os.chdir(original_cwd)

    def test_directory_resolve_strict(self, tmp_path: Path):
        """resolve(strict=True) raises if not exists."""
        directory = fs.Directory(str(tmp_path / "nonexistent"))
        with pytest.raises(FileNotFoundError):
            directory.resolve(strict=True)

    def test_directory_relative_to(self, temp_directory: fs.Directory):
        """relative_to() returns relative path."""
        parent_dir = os.path.dirname(temp_directory.path)
        relative = temp_directory.relative_to(parent_dir)
        assert relative == "testdir"

    def test_directory_expanduser(self, tmp_path: Path):
        """expanduser() returns a new Directory with ~ expanded."""
        directory = fs.Directory("~/testdir")
        expanded_dir = directory.expanduser()
        assert directory.path == os.path.join("~", "testdir")
        assert "~" not in expanded_dir.path
        assert os.path.expanduser("~") in expanded_dir.path

    def test_directory_as_posix(self, temp_directory: fs.Directory):
        """as_posix() returns forward-slash path."""
        posix = temp_directory.as_posix()
        assert "\\" not in posix
        assert "/" in posix

    def test_directory_as_uri(self, temp_directory: fs.Directory):
        """as_uri() returns file:// URI."""
        uri = temp_directory.as_uri()
        assert uri.startswith("file://")

    def test_directory_match(self, temp_directory: fs.Directory):
        """match() matches glob pattern."""
        assert temp_directory.match("test*") is True
        assert temp_directory.match("*dir") is True

    def test_directory_match_no_match(self, temp_directory: fs.Directory):
        """match() returns False on no match."""
        assert temp_directory.match("other*") is False

    def test_directory_to_path(self, temp_directory: fs.Directory):
        """to_path() returns pathlib.Path."""
        path_obj = temp_directory.to_path()
        assert isinstance(path_obj, Path)
        assert str(path_obj) == temp_directory.path

    def test_directory_to_str(self, temp_directory: fs.Directory):
        """to_str() returns string."""
        string_path = temp_directory.to_str()
        assert isinstance(string_path, str)
        assert string_path == temp_directory.path

    def test_directory_with_name(self, temp_directory: fs.Directory):
        """with_name() returns new Directory with different name."""
        original_parent = os.path.dirname(temp_directory.path)
        new_dir = temp_directory.with_name("otherdir")
        assert new_dir.basename == "otherdir"
        assert os.path.dirname(new_dir.path) == original_parent
        assert new_dir is not temp_directory

    def test_directory_with_name_no_parent(self):
        """with_name() works with no parent directory."""
        d = fs.Directory("mydir")
        new_d = d.with_name("renamed")
        assert new_d.path == "renamed"


class TestDirectoryAssertions:
    def test_directory_should_exist(self, temp_directory: fs.Directory):
        """should_exist() passes for existing directory."""
        result = temp_directory.should_exist()
        assert result is temp_directory

    def test_directory_should_exist_raises(self, tmp_path: Path):
        """should_exist() raises FileNotFoundError."""
        directory = fs.Directory(str(tmp_path / "nonexistent"))
        with pytest.raises(FileNotFoundError):
            directory.should_exist()

    def test_directory_should_not_exist(self, tmp_path: Path):
        """should_not_exist() passes for missing directory."""
        directory = fs.Directory(str(tmp_path / "nonexistent"))
        result = directory.should_not_exist()
        assert result is directory

    def test_directory_should_not_exist_raises(self, temp_directory: fs.Directory):
        """should_not_exist() raises FileExistsError."""
        with pytest.raises(FileExistsError):
            temp_directory.should_not_exist()


class TestDirectoryRename:
    def test_directory_rename(self, temp_directory: fs.Directory):
        """rename() returns a new Directory for the renamed path."""
        original_path = temp_directory.path
        renamed_dir = temp_directory.rename("renamed")
        assert not os.path.exists(original_path)
        assert not temp_directory.exists
        assert temp_directory.path == original_path
        assert renamed_dir.exists
        assert renamed_dir.basename == "renamed"

    def test_directory_rename_returns_new_object(self, temp_directory: fs.Directory):
        """rename() returns a distinct Directory object."""
        renamed_dir = temp_directory.rename("renamed")
        assert renamed_dir is not temp_directory
        assert renamed_dir.basename == "renamed"

    def test_directory_rename_leaves_source_path_unchanged(self, temp_directory: fs.Directory):
        """rename() leaves the source object path unchanged."""
        original_path = temp_directory.path
        result = temp_directory.rename("renamed")
        assert temp_directory.path == original_path
        assert result.path.endswith("renamed")


class TestDirectoryPermissions:
    @pytest.mark.skipif(
        sys.platform == "win32", reason="Windows does not support Unix-style permissions"
    )
    def test_directory_chmod(self, temp_directory: fs.Directory):
        """chmod() changes permissions."""
        temp_directory.chmod(0o755)
        mode = os.stat(temp_directory.path).st_mode
        assert mode & 0o777 == 0o755
        temp_directory.chmod(0o777)


class TestDirectoryParents:
    def test_directory_parents(self, temp_directory: fs.Directory):
        """Parents returns tuple of Directory objects."""
        parents = temp_directory.parents
        assert isinstance(parents, tuple)
        assert all(isinstance(parent_dir, fs.Directory) for parent_dir in parents)
        assert len(parents) > 0

    def test_directory_parents_order(self, temp_directory: fs.Directory):
        """Parents in order from immediate to root."""
        parents = temp_directory.parents
        assert parents[0].path == os.path.dirname(temp_directory.path)
        if sys.platform != "win32":
            assert parents[-1].path == "/"


class TestDirectoryClassMethods:
    def test_directory_home(self):
        """Directory.home() returns home directory."""
        home = fs.Directory.home()
        assert isinstance(home, fs.Directory)
        assert home.exists
        assert home.path == os.path.expanduser("~")

    def test_directory_cwd(self):
        """Directory.cwd() returns current working directory."""
        cwd = fs.Directory.cwd()
        assert isinstance(cwd, fs.Directory)
        assert cwd.exists
        assert cwd.path == os.getcwd()

    def test_directory_rand(self):
        """Directory.rand() creates random directory name."""
        directory = fs.Directory.rand()
        assert isinstance(directory, fs.Directory)
        assert directory.basename.startswith("dir")

    def test_directory_rand_with_prefix(self):
        """Directory.rand(prefix='test') uses custom prefix."""
        directory = fs.Directory.rand(prefix="test")
        assert directory.basename.startswith("test")


@pytest.mark.skipif(
    sys.platform != "linux",
    reason="Linux only - os.setxattr not available on macOS/Windows",
)
class TestDirectoryXattr:
    """Tests for extended attribute operations on directories (Linux only)."""

    def test_directory_set_xattr(self, temp_directory: fs.Directory):
        """set_xattr() sets extended attribute."""
        try:
            result = temp_directory.set_xattr("test_value", "test_attr")
            assert result is temp_directory
            assert isinstance(result, fs.Directory)
        except OSError as e:
            if e.errno == 95:  # EOPNOTSUPP
                pytest.skip("Extended attributes not supported on this filesystem")
            raise

    def test_directory_get_xattr(self, temp_directory: fs.Directory):
        """get_xattr() retrieves extended attribute."""
        try:
            temp_directory.set_xattr("test_value", "test_attr")
            value = temp_directory.get_xattr("test_attr")
            assert value == "test_value"
        except OSError as e:
            if e.errno == 95:  # EOPNOTSUPP
                pytest.skip("Extended attributes not supported on this filesystem")
            raise

    def test_directory_remove_xattr(self, temp_directory: fs.Directory):
        """remove_xattr() removes extended attribute."""
        try:
            temp_directory.set_xattr("test_value", "test_attr")
            temp_directory.remove_xattr("test_attr")
            with pytest.raises(OSError, match=r".*"):
                temp_directory.get_xattr("test_attr")
        except OSError as e:
            if e.errno == 95:  # EOPNOTSUPP
                pytest.skip("Extended attributes not supported on this filesystem")
            raise
