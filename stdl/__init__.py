from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from stdl.fs import AsyncFileHandle, Directory, File

LazyExport: TypeAlias = "ModuleType | type[AsyncFileHandle[str] | Directory | File]"


def __getattr__(name: str) -> LazyExport:
    """Lazily resolve public package exports."""
    if name in {"AsyncFileHandle", "Directory", "File"}:
        from stdl import fs

        return getattr(fs, name)
    if name in {"color", "decorators", "dt", "fs", "import_lazy", "log", "lst", "net", "st"}:
        import importlib

        return importlib.import_module(f"stdl.{name}")

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AsyncFileHandle",
    "Directory",
    "File",
    "color",
    "decorators",
    "dt",
    "fs",
    "import_lazy",
    "log",
    "lst",
    "net",
    "st",
]
