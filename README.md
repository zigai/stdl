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
pip install 'stdl[async]'
```

### Using uv

```sh
uv add stdl
uv add 'stdl[async]'
```

### From source

```sh
pip install git+https://github.com/zigai/stdl.git
# or
uv add git+https://github.com/zigai/stdl.git
```

## License

[MIT License](https://github.com/zigai/stdl/blob/master/LICENSE)
