import re
import textwrap


class ColorANSI:
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


class FilterStr:
    LETTERS = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    LETTERS_SLOVENIAN = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZčšžČŠŽ")
    FILE_NAME = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.[]-_()")
    REGULAR_CHARACTERS = set(
        " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/\\:;.,[]-_()#!?'\"")
    ASCII = set(''.join(chr(x) for x in range(128)))
    NUMBERS = set("0123456789,.")
    DIGITS = set("0123456789")

    @staticmethod
    def filter_str(f: set, s: str):
        return "".join(filter(f.__contains__, s))

    @staticmethod
    def letters_only(s: str):
        return FilterStr.filter_str(FilterStr.LETTERS, s)

    @staticmethod
    def numbers_only(s: str):
        return FilterStr.filter_str(FilterStr.NUMBERS, s)

    @staticmethod
    def normal_chars(s: str):
        return FilterStr.filter_str(FilterStr.REGULAR_CHARACTERS, s)

    @staticmethod
    def file_name(s: str):
        return FilterStr.filter_str(FilterStr.FILE_NAME, s)

    @staticmethod
    def ascii(s: str):
        return FilterStr.filter_str(FilterStr.ASCII, s)


def str_with_color(string: str, ansi_color):
    return f"{ansi_color}{string}{ColorANSI.RESET}"


def snake_case(s: str) -> str:
    return "_".join(
        re.sub("([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1",
                                               s.replace("-", " "))).split()).lower()


def camel_case(s: str) -> str:
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return s[0].lower() + s[1:]


def strip_esc_chars(text: str):
    return text.strip("\n").strip("\t").strip("\r")


def to_lines(text: str, max_text_width: int, newline: str = "\n"):
    s = ""
    wrapped_text = textwrap.wrap(text, width=max_text_width)
    for line in wrapped_text:
        s = s + line + newline
    return s


def find_urls(s: str) -> list:
    urls = re.findall('"((http|ftp)s?://.*?)"', s)
    urls = [i[0] for i in urls]
    urls = list(set(urls))
    return urls
