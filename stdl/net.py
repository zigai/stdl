import os
from urllib.request import urlretrieve

from tqdm import tqdm


class ProgressBarTQDM(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download(url: str, path: str, *, progressbar: bool = False, overwrite: bool = False):
    """
    Download a file

    Args:
        url (str): File URL
        path (str): Save path
        progressbar (bool, optional): Display progress bar in console. Defaults to False.
        overwrite (bool, optional): Overwrite destination path if it already exists. Defaults to False.

    Raises:
        FileExistsError: if path already exists and overwrite is set to False
    """
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(path)
    if progressbar:
        with ProgressBarTQDM(unit="B", unit_scale=True, unit_divisor=1024) as t:
            r = urlretrieve(url, path, reporthook=t.update_to, data=None)
        t.total = t.n
    else:
        r = urlretrieve(url, path)
    return r


__all__ = ["download"]
