import re
import textwrap
from typing import List


# Code by https://github.com/rene-d
# https://gist.github.com/smcclennon/a42e2e3819a01d2429a430fb57d545c0
class ColorANSI:
    BLACK = "\033[30m"
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = "\033[34m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    WHITE = "\033[97m"
    BROWN = "\033[0;33m"
    PURPLE = "\033[0;35m"
    DARK_GRAY = "\033[90m"
    LIGHT_GRAY = "\033[37m"
    LIGHT_RED = "\033[91m"
    LIGHT_GREEN = "\033[92m"
    LIGHT_YELLOW = "\033[93m"
    LIGHT_BLUE = "\033[94m"
    LIGHT_PURPLE = "\033[95m"
    LIGHT_CYAN = "\033[96m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    RESET = '\033[0m'
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

    @staticmethod
    def print_all():
        for i in dir(ColorANSI):
            if i[0] != "_" and i != "RESET" and i != "print_all":
                print(str_with_color(i, getattr(ColorANSI, i)))


class FilterStr:
    ENG_LETTERS = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    FILE_NAME = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.[]-_()")
    ASCII = set(''.join(chr(x) for x in range(128)))
    NUMBERS = set("0123456789,.")
    DIGITS = set("0123456789")

    @staticmethod
    def filter(s: str, allowed_chars: set) -> str:
        return "".join(filter(allowed_chars.__contains__, s))

    @staticmethod
    def file_name(s: str) -> str:
        return FilterStr.filter(s, FilterStr.FILE_NAME)

    @staticmethod
    def ascii(s: str) -> str:
        return FilterStr.filter(s, FilterStr.ASCII)

    @staticmethod
    def numbers(s: str) -> str:
        return FilterStr.filter(s, FilterStr.NUMBERS)

    @staticmethod
    def digits(s: str) -> str:
        return FilterStr.filter(s, FilterStr.DIGITS)

    @staticmethod
    def letters_eng(s: str) -> str:
        return FilterStr.filter(s, FilterStr.ENG_LETTERS)


def str_with_color(string: str, ansi_color) -> str:
    return f"{ansi_color}{string}{ColorANSI.RESET}"


def snake_case(s: str) -> str:
    return "_".join(
        re.sub("([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1",
                                               s.replace("-", " "))).split()).lower()


def camel_case(s: str) -> str:
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]


def strip_esc_chars(text: str) -> str:
    return text.strip("\n").strip("\t").strip("\r")


def to_lines(text: str, max_text_width: int, newline: str = "\n") -> str:
    s = ""
    wrapped_text = textwrap.wrap(text, width=max_text_width)
    for line in wrapped_text:
        s = s + line + newline
    return s


def find_urls(s: str) -> List[str]:
    urls = re.findall('"((http|ftp)s?://.*?)"', s)
    urls = [i[0] for i in urls]
    urls = list(set(urls))
    return urls
