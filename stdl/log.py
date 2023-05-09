from os import get_terminal_size
from typing import Callable


def color_tag(text: str, c: str):
    return f"<{c}>{text}</{c}>"


class LoguruFormatter:
    time = color_tag("{time:YYYY-MM-DD HH:mm:ss.SSS}", "light-black")
    level = color_tag("{level: <8}", "level")
    msg = color_tag("{message:<24}", "level")
    name = color_tag("{name}", "light-blue")
    func = color_tag("{function}", "light-blue")
    lineno = color_tag("{line}", "light-blue")

    def format(self, record: dict) -> str:
        """
        Example:
        >>> import sys
        >>> from loguru import logger
        >>> logger.add(sys.stdout, level="DEBUG", format=loguru_formater)
        """
        extras = ""
        if len(record["extra"]):
            for key in record["extra"].keys():
                extras = extras + key + "=" + "{extra[" + key + "]}, "
            extras = extras[:-2]
        fmt = f"{self.time} [ {self.level} ] {self.name}:{self.func}:{self.lineno} - {self.msg} {extras}\n"
        return fmt


loguru_formater = LoguruFormatter().format


def get_logging_config(
    format: str | None = None,
    level: str = "INFO",
    filename: str | None = None,
    backup_count: int = 0,
    disable_existing: bool = False,
    console_handler: str = "logging.StreamHandler",
    file_handler: str = "logging.handlers.TimedRotatingFileHandler",
    style: str = "{",
):
    format = (
        format or "{asctime} [{levelname:<8s}] [{module}.{funcName}:{lineno}] {name} - {message}"
    )

    config = {
        "version": 1,
        "disable_existing_loggers": disable_existing,
        "formatters": {
            "standard": {
                "format": format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "style": style,
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
    length: int = None,  # type: ignore
    handler: Callable = print,
    *,
    newline=False,
) -> None:
    try:
        length = length or get_terminal_size().columns
    except OSError:  # OSError: [Errno 25] Inappropriate ioctl for device
        length = 80
    line = c * length
    if newline:
        line += "\n"
    handler(line)


__all__ = ["loguru_formater", "br", "get_logging_config", "LoguruFormatter"]
