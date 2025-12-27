import inspect
import json
import sys
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def timer(
    r: int | None = 2,
    sink: Callable[[str], None] = sys.stdout.write,
    show_args: bool = False,
    serialize: bool = False,
    sep: str = " | ",
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    A decorator that displays the time taken for a function to execute.

    Args:
        r (int, optional): Number of decimal places to round the time to. Defaults to 2.
        sink (Callable, optional): A function that takes a string and does something with it. Defaults to print.
        show_args (bool, optional): Whether to show the arguments passed to the function. Defaults to False.
        serialize (bool, optional): Whether to serialize the output as JSON. Defaults to False.
        sep (str, optional): Separator between the function/method name and the arguments. Defaults to " | ".
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            time_start = time.perf_counter()
            result = func(*args, **kwargs)

            time_end = time.perf_counter()
            time_elapsed = time_end - time_start
            if r is not None:
                time_elapsed = round(time_elapsed, r)

            is_method = "self" in list(inspect.signature(func).parameters.keys())
            func_args = args[1:] if is_method else args
            name = func.__qualname__ if is_method else func.__name__
            message = f"'{name}' took {time_elapsed}s"

            if show_args:
                kwargs_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                all_args = ", ".join(map(str, func_args)) + (
                    ", " + kwargs_info if kwargs_info else ""
                )
                message += f"{sep}Args: {all_args}"

            if serialize:
                message_dict: dict[str, Any] = {
                    "name": name,
                    "time": time_elapsed,
                    "args": func_args,
                    "kwargs": kwargs,
                }
                if show_args:
                    message_dict["args"] = func_args
                    message_dict["kwargs"] = kwargs
                message = json.dumps(message_dict)

            sink(message)
            return result

        return wrapper

    return decorator


def retry(attempts: int, delay: float = 0) -> Callable[[Callable[P, T]], Callable[P, T]]:
    if attempts < 1:
        raise ValueError("Attempts must be greater than 0")

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt < attempts - 1:
                        time.sleep(delay)
                    else:
                        raise
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["timer", "retry"]
