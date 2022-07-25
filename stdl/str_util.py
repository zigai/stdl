import re
import textwrap


def str_with_color(string: str, color: str) -> str:
    try:
        clr = Color[color]
    except KeyError:
        clr = color
    return f"{clr}{string}{Color.RESET}"


class Color:
    BLACK = "\033[30m"
    BLINK = "\033[5m"
    BLUE = "\033[34m"
    BOLD = "\033[1m"
    BROWN = "\033[0;33m"
    CROSSED = "\033[9m"
    CYAN = "\033[36m"
    DARK_GRAY = "\033[90m"
    FAINT = "\033[2m"
    GREEN = '\033[92m'
    ITALIC = "\033[3m"
    LIGHT_BLUE = "\033[94m"
    LIGHT_CYAN = "\033[96m"
    LIGHT_GRAY = "\033[37m"
    LIGHT_GREEN = "\033[92m"
    LIGHT_PURPLE = "\033[95m"
    LIGHT_RED = "\033[91m"
    LIGHT_WHITE = "\033[1;37m"
    LIGHT_YELLOW = "\033[93m"
    NEGATIVE = "\033[7m"
    PURPLE = "\033[0;35m"
    RED = '\033[91m'
    RESET = '\033[0m'
    UNDERLINE = "\033[4m"
    WHITE = "\033[97m"
    YELLOW = "\033[33m"

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
            if i[0] != "_" and i not in ["dict", "print_all"]:
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
            print(str_with_color(k, v))


class FilterStr:
    ENG_ALPHABET = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    FILENAME = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.[]-_()")
    ASCII = set(''.join(chr(x) for x in range(128)))
    NUMBERS = set("0123456789,.")
    DIGITS = set("0123456789")

    @classmethod
    def filter(cls, s: str, allowed_chars: set) -> str:
        return "".join(filter(allowed_chars.__contains__, s))

    @classmethod
    def filename(cls, s: str) -> str:
        return cls.filter(s, cls.FILENAME)

    @classmethod
    def ascii(cls, s: str) -> str:
        return cls.filter(s, cls.ASCII)

    @classmethod
    def numbers(cls, s: str) -> str:
        return cls.filter(s, cls.NUMBERS)

    @classmethod
    def digits(cls, s: str) -> str:
        return cls.filter(s, cls.DIGITS)

    @classmethod
    def eng_alphabet(cls, s: str) -> str:
        return cls.filter(s, cls.ENG_ALPHABET)


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


def to_lines(text: str, max_width: int, newline: str = "\n") -> str:
    s = ""
    wrapped = textwrap.wrap(text, width=max_width)
    for line in wrapped:
        s = f"{s}{line}{newline}"
    return s


def find_urls(s: str) -> list[str]:
    urls = re.findall('"((http|ftp)s?://.*?)"', s)
    urls = [i[0] for i in urls]
    return list(set(urls))


def terminal_link(uri: str, label: str = None, color: str = None):
    """
    Hyperlinks may not be supported in your terminal and can cause disfigured text to be printed.
    
    Learn more at:
    https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    """
    parameters = ''
    if label is None:
        label = uri
    link = f'\033]8;{parameters};{uri}\033\\{label}\033]8;;\033\\'
    if color is not None:
        link = str_with_color(link, color)
    return link
