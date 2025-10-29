import importlib
import sys
import time
from typing import Any


class LazyImport:
    """A lazy import that loads the actual object on first access."""

    def __init__(
        self,
        module_name: str,
        attr_name: str | None = None,
        verbose: bool = False,
    ):
        self.module_name = module_name
        self.attr_name = attr_name
        self.verbose = verbose

        self._cached_value: Any = None
        self._loaded = False

    def _load(self) -> Any:
        if not self._loaded:
            if self.verbose:
                start_time = time.time()

            module_already_loaded = self.module_name in sys.modules
            try:
                module = importlib.import_module(self.module_name)
            except ImportError as e:
                if self.attr_name:
                    raise ImportError(
                        f"Cannot import '{self.attr_name}' from '{self.module_name}': {e}"
                    )
                else:
                    raise ImportError(f"Cannot import module '{self.module_name}': {e}")

            if self.attr_name:
                try:
                    self._cached_value = getattr(module, self.attr_name)
                except AttributeError:
                    raise ImportError(
                        f"Module '{self.module_name}' has no attribute '{self.attr_name}'"
                    )
            else:
                self._cached_value = module

            if self.verbose and not module_already_loaded:
                end_time = time.time()
                import_time = end_time - start_time
                import_target = (
                    f"{self.module_name}.{self.attr_name}" if self.attr_name else self.module_name
                )

                print(
                    f'importing "{import_target}" took {import_time:.3f}s',
                    file=sys.stderr,
                )

            self._loaded = True

        return self._cached_value

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._load()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("module_name", "attr_name", "verbose", "_cached_value", "_loaded"):
            super().__setattr__(name, value)
        else:
            setattr(self._load(), name, value)

    def __repr__(self) -> str:
        if self._loaded:
            return repr(self._cached_value)
        return f"<LazyImport: {self.module_name}{('.' + self.attr_name) if self.attr_name else ''}>"


def import_lazy(
    module: str,
    names: list[str] | None = None,
    alias: str | None = None,
    verbose: bool = False,
) -> None:
    """
    Lazy import a module.

    Args:
        module (str): Module name to import
        names (list[str] | None): List of specific names to import from the module. If None, imports the module itself.
        alias (str | None): Alias to use for the imported module (only valid when names is None)
        verbose (bool): If True, print timing information when imports actually happen

    Example:
        ```python
        >>> import_lazy("module", ["name_1", "name_2"])  # from module import name_1, name_2
        >>> import_lazy("module")                      # import module
        >>> import_lazy("module", alias="mod")          # import module as mod
        >>> import_lazy("package.submodule", ["name_1"])   # from package.submodule import name_1
        ```
    """
    frame = sys._getframe(1)
    caller_globals = frame.f_globals

    if names is None:
        lazy_import = LazyImport(module, verbose=verbose)
        if alias:
            caller_globals[alias] = lazy_import
        else:
            caller_globals[module.split(".")[-1]] = lazy_import
    else:
        if alias:
            raise ValueError("Cannot use alias with named imports")
        for name in names:
            lazy_import = LazyImport(module, name, verbose=verbose)
            caller_globals[name] = lazy_import


__all__ = ["import_lazy", "LazyImport"]
