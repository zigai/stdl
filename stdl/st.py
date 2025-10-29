import os
import re
import textwrap
from dataclasses import dataclass
from platform import system
from sys import stdout
from typing import Any, Literal

CSI_RESET = "\033["
NO_COLOR = bool(os.environ.get("NO_COLOR", False))


def ansi_code(n: int) -> str:
    return f"{CSI_RESET}{n}m"


class ColorANSI:
    # Cancel SGR codes if we don't write to a terminal
    if not stdout.isatty():
        for attr in dir():
            if isinstance(attr, str) and attr[0] != "_":
                locals()[attr] = ""
    else:
        # Enable VT mode on Windows
        if system() == "Windows":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            if handle:
                kernel32.SetConsoleMode(handle, 7)
            del kernel32
            del handle
            del ctypes

    @classmethod
    def __class_getitem__(cls, key: str) -> str:
        key = key.upper().replace(" ", "_")
        if key in dir(cls):
            return getattr(cls, key)
        raise KeyError(key)

    @classmethod
    def dict(cls) -> dict[str, str]:
        ignored = ["dict", "print_all", "get_names"]
        data = {}
        for attr in dir(cls):
            if attr[0] != "_" and attr not in ignored:
                data[attr] = cls[attr]
        return data

    @classmethod
    def get_names(cls) -> list[str]:
        return [i for i in cls.dict.keys()]

    @classmethod
    def print_all(cls) -> None:
        for k, v in cls.dict().items():
            if k == "RESET":
                continue
            print(colored(k, v))  # type:ignore


class FG(ColorANSI):
    """Foreground Color"""

    BLACK = ansi_code(30)
    RED = ansi_code(31)
    GREEN = ansi_code(32)
    YELLOW = ansi_code(33)
    BLUE = ansi_code(34)
    MAGENTA = ansi_code(35)
    CYAN = ansi_code(36)
    WHITE = ansi_code(37)
    GRAY = ansi_code(90)
    LIGHT_RED = ansi_code(91)
    LIGHT_GREEN = ansi_code(92)
    LIGHT_YELLOW = ansi_code(93)
    LIGHT_BLUE = ansi_code(94)
    LIGHT_MAGENTA = ansi_code(95)
    LIGHT_CYAN = ansi_code(96)
    LIGHT_WHITE = ansi_code(97)
    BOLD = ansi_code(1)


class BG(ColorANSI):
    """Background Color"""

    BLACK = ansi_code(40)
    RED = ansi_code(41)
    GREEN = ansi_code(42)
    YELLOW = ansi_code(43)
    BLUE = ansi_code(44)
    MAGENTA = ansi_code(45)
    CYAN = ansi_code(46)
    WHITE = ansi_code(47)
    GRAY = ansi_code(100)
    LIGHT_RED = ansi_code(101)
    LIGHT_GREEN = ansi_code(102)
    LIGHT_YELLOW = ansi_code(103)
    LIGHT_BLUE = ansi_code(104)
    LIGHT_MAGENTA = ansi_code(105)
    LIGHT_CYAN = ansi_code(106)
    LIGHT_WHITE = ansi_code(107)


class ST(ColorANSI):
    """Style"""

    RESET = ansi_code(0)
    BOLD = ansi_code(1)
    DIM = ansi_code(2)
    ITALIC = ansi_code(3)
    UNDERLINE = ansi_code(4)
    BLINK = ansi_code(5)


ForegroundColor = Literal[
    "black",
    "blue",
    "bold",
    "cyan",
    "gray",
    "green",
    "light_blue",
    "light_cyan",
    "light_green",
    "light_magenta",
    "light_red",
    "light_white",
    "light_yellow",
    "magenta",
    "red",
    "white",
    "yellow",
]


BackgroundColor = Literal[
    "black",
    "blue",
    "cyan",
    "gray",
    "green",
    "light_blue",
    "light_cyan",
    "light_green",
    "light_magenta",
    "light_red",
    "light_white",
    "light_yellow",
    "magenta",
    "red",
    "white",
    "yellow",
]

Style = Literal["blink", "bold", "dim", "italic", "reset", "underline"]


def _get_ansi_value(value: str | None, handler: Any) -> str:
    if not value:
        return ""
    try:
        return handler[value]
    except KeyError:
        return value


def colored(
    text: str,
    color: ForegroundColor | str | None = None,
    background: BackgroundColor | str | None = None,
    style: Style | str | None = None,
) -> str:
    """
    Returns the text with ansi color, background color and text style codes.

    Args:
        text (str): The text that should be colorized.
        color (str, optional): The color to use for the text.
        background (str, optional): The color to use for the background.
        style (str, optional): The style to use for the text.

    Returns:
        str: The colorized text.
    """
    if NO_COLOR or not stdout.isatty():
        return text
    color = _get_ansi_value(color, FG)  # type: ignore
    background = _get_ansi_value(background, BG)  # type: ignore
    style = _get_ansi_value(style, ST)  # type: ignore
    return f"{color}{background}{style}{text}{ST.RESET}"


@dataclass
class TextStyle:
    color: ForegroundColor | str | None = None
    background: BackgroundColor | str | None = None
    style: Style | str | None = None


def with_style(text: str, style: TextStyle) -> str:
    return colored(text, color=style.color, background=style.background, style=style.style)


def terminal_link(
    uri: str,
    label: str | None = None,
    color: ForegroundColor = "white",
    background: BackgroundColor | None = None,
    style: Style | None = None,
) -> str:
    """
    Returns a hyperlink that can be used in terminals.

    Note:
        Hyperlinks are not supported in all terminals.
        For more information visit
        <https://github.com/Alhadis/OSC8-Adoption/>
        and
        <https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda>

    Args:
        uri (str): The URI of the link.
        label (str, optional): The label of the link. Defaults to the URI.
        color (str, optional): The color of the link. Defaults to white.
        background (str, optional): The background color of the link.
        style (str, optional): The style of the link.

    Returns:
        str: The link as a string.
    """
    if label is None:
        label = uri

    if stdout.isatty():
        link = f"\033]8;;{uri}\033\\{label}\033]8;;\033\\"
    else:
        link = uri
    link = colored(link, color, background, style)
    return link


def remove(s: str, chars: str | set, replace_with: str = "") -> str:
    """
    Remove or replace characters in a string.

    Args:
        s (str): Input string.
        chars (str | set): Characters to remove
        replace_with (str, optional): If provided, replace the characters with this value.

    """
    string = []
    chars = set(chars)
    for c in s:
        if c not in chars:
            string.append(c)
        else:
            if replace_with:
                string.append(replace_with)
    return "".join(string)


def keep(s: str, chars: str | set, replace_with: str = "") -> str:
    """
    Keep provided characters in a string. Remove or replace others.

    Args:
        s (str): Input string
        chars (str | set): Characters to keep
        replace_with (str, optional): If provided, replace other characters with this value.

    """
    string = []
    chars = set(chars)
    for c in s:
        if c in chars:
            string.append(c)
        else:
            if replace_with:
                string.append(replace_with)
    return "".join(string)


ASCII = set("".join(chr(x) for x in range(128)))


class sf:
    """A collection of functions that can be used to filter strings."""

    @classmethod
    def filename(cls, filename: str, replace_with: str = "") -> str:
        """Removes or replaces characters that are not allowed to be in a filename."""
        return remove(filename, chars='|?*<>:"\\', replace_with=replace_with)

    @classmethod
    def filepath(cls, filepath: str, replace_with: str = "") -> str:
        """Removes or replaces characters that are not allowed to be in a filepath."""
        if not filepath:
            return ""
        dirname, filename = os.path.split(filepath)
        filename = sf.filename(filename, replace_with)
        dirname = remove(dirname, '|?*<>:"')
        return f"{dirname}{os.sep}{filename}"

    @classmethod
    def ascii(cls, s: str, replace_with: str = "") -> str:
        """Removes or replaces non-ASCII characters from the string."""
        return keep(s, ASCII, replace_with)


def snake_case(s: str) -> str:
    """Converts a given string to snake_case."""
    return "_".join(
        re.sub(
            "([A-Z][a-z]+)",
            r" \1",
            re.sub("([A-Z]+)", r" \1", s.replace("-", " ")),
        ).split()
    ).lower()


def camel_case(s: str) -> str:
    """Converts a given string to camelCase."""
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]


def kebab_case(s: str) -> str:
    """Converts a given string to kebab-case."""
    RE_WORDS = r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+"
    RE_SEP = r"(\s|_|-)+"
    return "-".join(
        re.sub(
            RE_SEP,
            " ",
            re.sub(
                RE_WORDS,
                lambda mo: " " + mo.group(0).lower(),
                s,
            ),
        ).split()
    )


def wrapped(text: str, width: int, newline: str = "\n") -> str:
    """Wraps the given text to a specified width and separates lines with the given newline character."""
    return newline.join(textwrap.wrap(text, width=width))


def ansi_len(s: str) -> int:
    """Returns the length of the string without the ANSI codes."""
    ascii_codes = re.findall(r"\x1b\[[0-9;]*[m]", s)
    codes_len = sum(len(code) for code in ascii_codes)
    return len(s) - codes_len


def ansi_ljust(s: str, width: int, fillchar: str = " ") -> str:
    """
    Ljust function that takes into account the length of the ANSI codes in the string.

    Args:
        s (str): The string to be left justified.
        width (int): The width of the string.
        fillchar (str, optional): The character to fill the string with. Defaults to " ".
    """
    ascii_codes = re.findall(r"\x1b\[[0-9;]*[m]", s)
    codes_len = sum(len(code) for code in ascii_codes)
    new_width = width + codes_len
    return s.ljust(new_width, fillchar)


def ansi_rjust(s: str, width: int, fillchar: str = " ") -> str:
    """
    Rjust function that takes into account the length of the ANSI codes in the string.

    Args:
        s (str): The string to be right justified.
        width (int): The width of the string.
        fillchar (str, optional): The character to fill the string with. Defaults to " ".
    """
    ascii_codes = re.findall(r"\x1b\[[0-9;]*[m]", s)
    codes_len = sum(len(code) for code in ascii_codes)
    new_width = width + codes_len
    return s.rjust(new_width, fillchar)


def ansi_strip(r: str) -> str:
    """Remove ANSI escape codes from a string."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", r)


if __name__ == "__main__":
    FG.print_all()
    BG.print_all()
    ST.print_all()


__all__ = [
    "FG",
    "BG",
    "ST",
    "colored",
    "terminal_link",
    "remove",
    "keep",
    "ASCII",
    "sf",
    "snake_case",
    "camel_case",
    "kebab_case",
    "wrapped",
    "ansi_len",
    "ansi_ljust",
    "ansi_rjust",
    "Style",
    "ForegroundColor",
    "BackgroundColor",
]
