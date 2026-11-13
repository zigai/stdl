# stdl

[![tests](https://img.shields.io/github/actions/workflow/status/zigai/stdl/test.yml?branch=master&label=tests&labelColor=30363d)](https://github.com/zigai/stdl/actions/workflows/test.yml)
[![docs](https://img.shields.io/readthedocs/stdl?label=docs&logo=readthedocs&logoColor=white&labelColor=30363d)](https://stdl.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/stdl?label=PyPI&color=blue&logo=pypi&logoColor=white&labelColor=30363d)](https://pypi.org/project/stdl/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white&labelColor=30363d)](pyproject.toml)
[![downloads](https://img.shields.io/pypi/dm/stdl?label=downloads&color=blue&labelColor=30363d)](https://pepy.tech/projects/stdl)
[![downloads](https://img.shields.io/pepy/dt/stdl?label=downloads&color=blue&labelColor=30363d)](https://pepy.tech/projects/stdl)
[![license](https://img.shields.io/github/license/zigai/stdl?label=license&labelColor=30363d)](LICENSE)

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
