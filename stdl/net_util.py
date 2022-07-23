import os
from urllib.request import urlretrieve

from tqdm import tqdm


class ProgressBarTQDM(tqdm):

    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download(url: str, path: str, progressbar: bool = False, overwrite: bool = False):
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(path)
    if progressbar:
        with ProgressBarTQDM(unit="B", unit_scale=True, unit_divisor=1024) as t:
            r = urlretrieve(url, path, reporthook=t.update_to, data=None)
        t.total = t.n
    else:
        r = urlretrieve(url, path)
    return r
