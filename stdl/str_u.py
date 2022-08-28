import re
import textwrap

__CSI = '\033['


def ansi_code(n: int):
    return f"{__CSI}{n}m"


def __get_ansi_val(value, handler):
    if value == "" or value is None:
        return ""
    try:
        clr = handler[value]
        return clr
    except KeyError:
        return value


class __ColorANSI:
    # cancel SGR codes if we don't write to a terminal
    if not __import__("sys").stdout.isatty():
        for _ in dir():
            if isinstance(_, str) and _[0] != "_":
                locals()[_] = ""
    else:
        # set Windows console in VT mode
        if __import__("platform").system() == "Windows":
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
        for i in dir(cls):
            if i[0] != "_" and i not in ["dict", "print_all", "get_all"]:
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


class FG(__ColorANSI):
    BLACK = ansi_code(30)
    RED = ansi_code(31)
    GREEN = ansi_code(32)
    YELLOW = ansi_code(33)
    BLUE = ansi_code(34)
    MAGENTA = ansi_code(35)
    CYAN = ansi_code(36)
    WHITE = ansi_code(37)
    BRIGHT_BLACK = ansi_code(90)
    BRIGHT_RED = ansi_code(91)
    BRIGHT_GREEN = ansi_code(92)
    BRIGHT_YELLOW = ansi_code(93)
    BRIGHT_BLUE = ansi_code(94)
    BRIGHT_MAGENTA = ansi_code(95)
    BRIGHT_CYAN = ansi_code(96)
    BRIGHT_WHITE = ansi_code(97)
    BOLD = ansi_code(1)


class BG(__ColorANSI):
    BLACK = ansi_code(40)
    RED = ansi_code(41)
    GREEN = ansi_code(42)
    YELLOW = ansi_code(43)
    BLUE = ansi_code(44)
    MAGENTA = ansi_code(45)
    CYAN = ansi_code(46)
    WHITE = ansi_code(47)
    BRIGHT_BLACK = ansi_code(100)
    BRIGHT_RED = ansi_code(101)
    BRIGHT_GREEN = ansi_code(102)
    BRIGHT_YELLOW = ansi_code(103)
    BRIGHT_BLUE = ansi_code(104)
    BRIGHT_MAGENTA = ansi_code(105)
    BRIGHT_CYAN = ansi_code(106)
    BRIGHT_WHITE = ansi_code(107)


class ST(__ColorANSI):
    RESET = ansi_code(0)
    BOLD = ansi_code(1)
    DIM = ansi_code(2)
    ITALIC = ansi_code(3)
    UNDERLINE = ansi_code(4)
    BLINK = ansi_code(5)


def colored(text: str, color: str, background: str | None = None, style: str | None = None):
    color = __get_ansi_val(color, FG)  # type: ignore
    background = __get_ansi_val(background, BG)  # type: ignore
    style = __get_ansi_val(style, ST)  # type: ignore
    return f"{color}{background}{style}{text}{ST.RESET}"


def terminal_link(
    uri: str,
    label: str | None = None,
    color: str | None = None,
    background: str | None = None,
    style: str | None = None,
):
    """
    Hyperlinks are not supported in some terminals.
    Learn more at:
    https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    parameters = ''
    if label is None:
        label = uri
    link = f'\033]8;{parameters};{uri}\033\\{label}\033]8;;\033\\'
    link = colored(link, color, background, style)  # type: ignore
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
    filename_chars = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.[]-_()")
    return filter_str(s, chars=filename_chars, replace_with=replace_with)


def snake_case(s: str) -> str:
    return "_".join(
        re.sub(
            "([A-Z][a-z]+)",
            r" \1",
            re.sub("([A-Z]+)", r" \1", s.replace("-", " ")),
        ).split()).lower()


def camel_case(s: str) -> str:
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]


def to_lines(text: str, width: int, newline: str = "\n") -> str:
    string = ""
    wrapped = textwrap.wrap(text, width=width)
    for line in wrapped:
        string = f"{string}{line}{newline}"
    return string


def find_urls(s: str) -> list[str]:
    urls = re.findall('"((http|ftp)s?://.*?)"', s)
    urls = [i[0] for i in urls]
    return list(set(urls))


if __name__ == '__main__':
    FG.print_all()
    BG.print_all()
    ST.print_all()
