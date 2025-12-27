# stdl

[![Tests](https://github.com/zigai/stdl/actions/workflows/test.yml/badge.svg)](https://github.com/zigai/stdl/actions/workflows/test.yml)
[![Documentation Status](https://readthedocs.org/projects/stdl/badge/?version=latest)](https://stdl.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/stdl.svg)](https://badge.fury.io/py/stdl)
![Supported versions](https://img.shields.io/badge/python-3.10+-blue.svg)
[![Downloads](https://static.pepy.tech/badge/stdl)](https://pepy.tech/project/stdl)
[![license](https://img.shields.io/github/license/zigai/stdl.svg)](https://github.com/zigai/stdl/blob/master/LICENSE)

`stdl` is a collection of Python utilities that complement the standard library.

## Features

- File and directory operations
- String manipulation
- ANSI color support for terminal output
- Date and time formatting
- List utils
- Lazy imports
- Logging configuration for `logging` and `loguru`
- [See docs](https://stdl.readthedocs.io/en/latest/?badge=latest)

## Installation

### Using pip

```sh
pip install stdl
```

### Using uv

```sh
uv add stdl
```

### From source

```sh
pip install git+https://github.com/zigai/stdl.git
# or
uv add git+https://github.com/zigai/stdl.git
```

## Examples

### Lazy imports

```python
from typing import TYPE_CHECKING
from stdl.import_lazy import import_lazy

if TYPE_CHECKING:
    from os.path import abspath, join
    import numpy as np
    import torch
else:
    import_lazy("os.path", ["join", "abspath"], verbose=True)
    import_lazy("numpy", alias="np", verbose=True)
    import_lazy("torch", verbose=True)

print(np.zeros(4))
# importing "numpy" took 0.060s
# [0. 0. 0. 0.]
print(torch)
# <LazyImport: torch>
print(torch.randn(8))
# importing "torch" took 1.118s
# tensor([0., 0., 0., 0., 0., 0., 0., 0.])
print(torch)
# <module 'torch' from .../torch/__init__.py'
```

## License

[MIT License](https://github.com/zigai/stdl/blob/master/LICENSE)
