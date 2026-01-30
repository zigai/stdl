import os
import warnings
from http.client import HTTPMessage
from urllib.request import urlopen, urlretrieve

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - optional dependency
    tqdm = None

from stdl.fs import bytes_readable, readable_size_to_bytes

if tqdm is not None:

    class ProgressBarTQDM(tqdm):
        def update_to(self, b: int = 1, bsize: int = 1, tsize: int | None = None) -> None:
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)
else:
    ProgressBarTQDM = None


class DownloadSizeExceededError(Exception):
    """
    Exception raised when a file download exceeds the maximum allowed size.

    Attributes:
        filesize (int): The actual file size in bytes.
        maxsize (int): The maximum allowed size in bytes.
    """

    def __init__(self, filesize: int, maxsize: int):
        self.filesize = filesize
        self.maxsize = maxsize

    def __str__(self) -> str:
        return f"File size {self.filesize} ({bytes_readable(self.filesize)}) exceeds maximum size limit of {self.maxsize} bytes ({bytes_readable(self.maxsize)})"


def download(
    url: str,
    path: str,
    *,
    maxsize: int | str | None = None,
    progressbar: bool = False,
    overwrite: bool = False,
) -> tuple[str, HTTPMessage]:
    """
    Download a file

    Args:
        url (str): File URL
        path (str): Save path
        maxsize (int | str | None, optional): Maximum file size in bytes or human readable format.
        progressbar (bool, optional): Display progress bar in console.
        overwrite (bool, optional): Overwrite destination path if it already exists.

    Raises:
        FileExistsError: if path already exists and overwrite is set to False
        DownloadSizeExceededError: if file size exceeds maxsize
    """
    if maxsize is not None:
        if isinstance(maxsize, str):
            maxsize = readable_size_to_bytes(maxsize)
        filesize = int(urlopen(url).headers.get("Content-Length", 0))
        if filesize > maxsize:
            raise DownloadSizeExceededError(filesize, maxsize)

    if os.path.exists(path) and not overwrite:
        raise FileExistsError(path)

    if progressbar and ProgressBarTQDM is not None:
        with ProgressBarTQDM(unit="B", unit_scale=True, unit_divisor=1024) as t:
            r = urlretrieve(url, path, reporthook=t.update_to, data=None)
        t.total = t.n
    else:
        if progressbar and ProgressBarTQDM is None:
            warnings.warn(
                "progressbar=True requested but tqdm is not installed; downloading without progress bar.",
                RuntimeWarning,
                stacklevel=2,
            )
        r = urlretrieve(url, path)
    return r


__all__ = ["download"]
