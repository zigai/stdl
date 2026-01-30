from collections.abc import Callable
from shutil import get_terminal_size
from typing import Any, ClassVar

from stdl.st import ForegroundColor, colored

IGNORE_BREAKS = False


def color_tag(text: str, color: str) -> str:
    return f"<{color}>{text}</{color}>"


class LoguruFormatter:
    time = color_tag("{time:YYYY-MM-DD HH:mm:ss}", "green")
    level = color_tag("{level: <8}", "level")
    msg = color_tag("{message:<24}", "level")
    name = color_tag("{name}", "light-blue")
    func = color_tag("{function}", "light-blue")
    lineno = color_tag("{line}", "light-blue")
    extra_key_skips: ClassVar[list[str]] = ["title"]
    extra_key_name_color: ForegroundColor = "white"

    def format(self, record: dict[str, Any]) -> str:
        """
        Example:
            ```python
            >>> import sys
            >>> from loguru import logger
            >>> logger.remove()
            >>> logger.add(sys.stdout, level="DEBUG", format=loguru_formater)
            ```
        """
        extras = ""
        if len(record["extra"]):
            for key in record["extra"].keys():
                if key in self.extra_key_skips:
                    continue
                extras = (
                    extras
                    + colored(key, self.extra_key_name_color)
                    + "="
                    + "{extra["
                    + key
                    + "]}, "
                )
            extras = extras[:-2]

        if title := record["extra"].get("title"):
            return f"{self.time} | {self.level} | [ {title} ] {self.name}:{self.func}:{self.lineno} - {self.msg} {extras}\n"
        return f"{self.time} | {self.level} | {self.name}:{self.func}:{self.lineno} - {self.msg} {extras}\n"


class SimpleLoguruFormatter(LoguruFormatter):
    def format(self, record: dict[str, Any]) -> str:
        extras = ""
        if len(record["extra"]):
            for key in record["extra"].keys():
                if key in self.extra_key_skips:
                    continue
                extras = (
                    extras
                    + colored(key, self.extra_key_name_color)
                    + "="
                    + "{extra["
                    + key
                    + "]}, "
                )
            extras = extras[:-2]

        return f"{self.level} - {self.msg} {extras}\n"


loguru_formater = LoguruFormatter().format
simple_loguru_formater = SimpleLoguruFormatter().format


def get_logging_config(
    format: str | None = None,
    level: str = "INFO",
    filename: str | None = None,
    backup_count: int = 0,
    disable_existing: bool = False,
    console_handler: str = "logging.StreamHandler",
    file_handler: str = "logging.handlers.TimedRotatingFileHandler",
    format_style: str = "{",
) -> dict[str, Any]:
    format = (
        format
        or "{asctime} | {levelname:<8s} | [ {name} ] {module}.{funcName}:{lineno} - {message}"
    )

    config = {
        "version": 1,
        "disable_existing_loggers": disable_existing,
        "formatters": {
            "standard": {
                "format": format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "style": format_style,
            }
        },
        "handlers": {
            "console": {
                "class": console_handler,
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {"level": level, "handlers": ["console"]},
    }
    if filename:
        config["handlers"]["file"] = {
            "class": file_handler,
            "level": level,
            "formatter": "standard",
            "backupCount": backup_count,
            "filename": filename,
        }
        config["root"]["handlers"].append("file")

    return config


def br(
    c: str = "_",
    length: int | None = None,
    handler: Callable[[str], None] = print,
    *,
    newline: bool = False,
) -> None:
    """
    Print a horizontal line break across the terminal.

    Args:
        c (str): Character to repeat. Defaults to "_".
        length (int | None): Line length. Defaults to terminal width.
        handler (Callable[[str], None]): Function to output the line. Defaults to print.
        newline (bool): Whether to append a newline. Defaults to False.
    """
    if IGNORE_BREAKS:
        return
    length = length or get_terminal_size().columns
    line = c * length
    if newline:
        line += "\n"
    handler(line)


__all__ = ["loguru_formater", "br", "get_logging_config", "LoguruFormatter"]
