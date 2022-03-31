from re import sub
from textwrap import wrap


class ANSI_Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    LIGHT_GRAY = "\033[37m"
    DARK_GRAY = "\033[90m"
    LIGHT_RED = "\033[91m"
    LIGHT_GREEN = "\033[92m"
    LIGHT_YELLOW = "\033[93m"
    LIGHT_BLUE = "\033[94m"
    LIGHT_MAGENTA = "\033[95m"
    LIGHT_CYAN = "\033[96m"
    BLACK = "\033[30m"
    WHITE = "\033[97m"
    RESET = '\033[0m'


class StrFilter:
    LETTERS = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    LETTERS_SLOVENIAN = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZčšžČŠŽ")
    FILE_NAME = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:.[]-_()#!")
    REGULAR = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/\:;.,[]-_()#!?")
    ASCII = ''.join(chr(x) for x in range(128))
    NUMBERS = set("0123456789,.")
    DIGITS = set("0123456789")

    def filter_str(f: set, s: str):
        return "".join(filter(f.__contains__, s))

    def letters_only(s: str):
        return StrFilter.filter_str(StrFilter.LETTERS, s)

    def numbers_only(s: str):
        return StrFilter.filter_str(StrFilter.NUMBERS, s)

    def normal_chars(s: str):
        return StrFilter.filter_str(StrFilter.REGULAR, s)

    def file_name(s: str):
        return StrFilter.filter_str(StrFilter.FILE_NAME, s)

    def ascii(s: str):
        return StrFilter.filter_str(StrFilter.ASCII, s)


def str_colored(string: str, ansi_color):
    return f"{ansi_color}{string}{ANSI_Color.RESET}"


def snake_case(s: str) -> str:
    return "_".join(sub("([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", s.replace("-", " "))).split()).lower()


def camel_case(s: str) -> str:
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]


def strip_esc_chars(text: str):
    return text.strip("\n").strip("\t").strip("\r")


def to_lines(text: str, max_text_width: int, newline_char: str = "\n"):
    s = ""
    wrapped_text = wrap(text, width=max_text_width)
    for line in wrapped_text:
        s = s + line + newline_char
    return s