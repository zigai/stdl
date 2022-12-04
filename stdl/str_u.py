import re
import textwrap
from platform import system
from sys import stdout

CSI_RESET = "\033["


def ansi_code(n: int) -> str:
    return f"{CSI_RESET}{n}m"


def __get_ansi_val(val: str | None, handler) -> str:
    if val == "" or val is None:
        return ""
    try:
        clr = handler[val]
        return clr
    except KeyError:
        return val


class ColorANSI:

    # cancel SGR codes if we don't write to a terminal
    if not stdout.isatty():
        for _ in dir():
            if isinstance(_, str) and _[0] != "_":
                locals()[_] = ""
    else:
        # set Windows console in VT mode
        if system() == "Windows":
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


def colored(text: str, color: str, background: str | None = None, style: str | None = None):
    color = __get_ansi_val(color, FG)
    background = __get_ansi_val(background, BG)
    style = __get_ansi_val(style, ST)
    return f"{color}{background}{style}{text}{ST.RESET}"


def terminal_link(
    uri: str,
    label: str | None = None,
    color: str = FG.WHITE,
    background: str | None = None,
    style: str | None = None,
):
    """
    Hyperlinks are not supported in some terminals.
    Learn more at:
    https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    if label is None:
        label = uri
    link = f"\033]8;;{uri}\033\\{label}\033]8;;\033\\"
    link = colored(link, color, background, style)
    return link


def filter_str(s: str, chars: set, replace_with: str | None = None) -> str:
    string = ""
    for i in s:
        if i in chars:
            string = f"{string}{i}"
        else:
            if replace_with is not None:
                string = f"{string}{replace_with}"
    return string


def filter_filename(s: str, replace_with: str | None = None):
    ALLOWED_CHARS = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.[]-_()")
    return filter_str(s, chars=ALLOWED_CHARS, replace_with=replace_with)


def snake_case(s: str) -> str:
    # The following snippet is licensed under the CC-BY-4.0 License.
    # Its source can be found at: https://github.com/30-seconds/30-seconds-of-python

    return "_".join(
        re.sub(
            "([A-Z][a-z]+)",
            r" \1",
            re.sub("([A-Z]+)", r" \1", s.replace("-", " ")),
        ).split()
    ).lower()


def camel_case(s: str) -> str:
    # The following snippet is licensed under the CC-BY-4.0 License.
    # Its source can be found at: https://github.com/30-seconds/30-seconds-of-python

    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]


def kebab_case(s: str) -> str:
    # The following snippet is licensed under the CC-BY-4.0 License.
    # Its source can be found at: https://github.com/30-seconds/30-seconds-of-python

    re_words = r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+"
    re_sep = r"(\s|_|-)+"
    return "-".join(
        re.sub(
            re_sep,
            " ",
            re.sub(
                re_words,
                lambda mo: " " + mo.group(0).lower(),
                s,
            ),
        ).split()
    )


def wrapped(text: str, width: int, newline: str = "\n"):
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
    "filter_str",
    "filter_filename",
    "snake_case",
    "camel_case",
    "kebab_case",
    "wrapped",
]
