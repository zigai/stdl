import os
import re
import textwrap
from platform import system
from sys import stdout

CSI_RESET = "\033["


def ansi_code(n: int) -> str:
    return f"{CSI_RESET}{n}m"


def _get_ansi_val(val: str | None, handler) -> str:
    if val == "" or val is None:
        return ""
    try:
        clr = handler[val]
        return clr
    except KeyError:
        return val


class ColorANSI:
    if not stdout.isatty():  # Cancel SGR codes if we don't write to a terminal
        for _ in dir():
            if isinstance(_, str) and _[0] != "_":
                locals()[_] = ""
    else:
        if system() == "Windows":  # Enable VT mode
            kernel32 = __import__("ctypes").windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            del kernel32

    @classmethod
    def __class_getitem__(cls, name: str) -> str:
        name = name.upper().replace(" ", "_")
        if name in dir(cls):
            return getattr(cls, name)
        raise KeyError(name)

    @classmethod
    @property
    def dict(cls) -> dict[str, str]:
        d = {}
        ignored = ["dict", "print_all", "get_all"]
        for i in dir(cls):
            if i[0] != "_" and i not in ignored:
                d[i] = cls.__class_getitem__(i)
        return d

    @classmethod
    def get_all(cls) -> list[str]:
        return [i for i in cls.dict.keys()]

    @classmethod
    def print_all(cls):
        for k, v in cls.dict.items():
            if k == "RESET":
                continue
            print(colored(k, v))


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
    "Style"
    RESET = ansi_code(0)
    BOLD = ansi_code(1)
    DIM = ansi_code(2)
    ITALIC = ansi_code(3)
    UNDERLINE = ansi_code(4)
    BLINK = ansi_code(5)


def colored(
    text: str,
    color: str | None = None,
    background: str | None = None,
    style: str | None = None,
):

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
    color = _get_ansi_val(color, FG)
    background = _get_ansi_val(background, BG)
    style = _get_ansi_val(style, ST)
    return f"{color}{background}{style}{text}{ST.RESET}"


def terminal_link(
    uri: str,
    label: str | None = None,
    color: str = FG.WHITE,
    background: str | None = None,
    style: str | None = None,
):
    """
    Returns a hyperlink that can be used in terminals.

    Hyperlinks are not supported in all terminals, for more information visit
    https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda

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
    link = f"\033]8;;{uri}\033\\{label}\033]8;;\033\\"
    link = colored(link, color, background, style)
    return link


def remove(s: str, chrs: str | set, replacement: str = "") -> str:
    """
    Remove or replace characters in a string.

    Args:
        s (str): Input string.
        chrs (str | set): Characters to remove
        replacement (str, optional): If provided, replace the characters with this value.

    """
    string = []
    chrs = set(chrs)
    for c in s:
        if not c in chrs:
            string.append(c)
        else:
            if replacement:
                string.append(replacement)
    return "".join(string)


def keep(s: str, chrs: str | set, replacement: str = "") -> str:
    """
    Keep provided characters in a string. Remove or replace others.

    Args:
        s (str): Input string
        chrs (str | set): Characters to keep
        replacement (str, optional): If provided, replace other characters with this value.

    """
    # return re.compile("[^" + "".join(set(chrs)) + "]").sub(replacement, s)
    string = []
    chrs = set(chrs)
    for c in s:
        if c in chrs:
            string.append(c)
        else:
            if replacement:
                string.append(replacement)
    return "".join(string)


ASCII = set("".join(chr(x) for x in range(128)))


class StringFilter:
    """
    A collection of functions that can be used to filter strings.
    """

    @classmethod
    def filename(cls, filename: str, replacement: str = "") -> str:
        """
        Removes or replaces characters that are not allowed to be in a filename.
        """
        return remove(filename, chrs='|?*<>:"\\', replacement=replacement)

    @classmethod
    def filepath(cls, filepath: str, replacement: str = "") -> str:
        """
        Removes or replaces characters that are not allowed to be in a filepath.
        """
        dn, fn = os.path.split(filepath)
        fn = StringFilter.filename(fn, replacement)
        dn = remove(dn, '|?*<>:"')
        return f"{dn}{os.sep}{fn}"

    @classmethod
    def ascii(cls, s: str, replacement: str = ""):
        """
        Removes or replaces non-ASCII characters from the string.
        """
        return keep(s, ASCII, replacement)


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
    "StringFilter",
    "snake_case",
    "camel_case",
    "kebab_case",
    "wrapped",
]
