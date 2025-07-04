from __future__ import annotations

import typing as T
from abc import ABC, abstractmethod
from collections.abc import Sequence as SequenceType
from copy import deepcopy
from typing import Sequence


class ColorValueError(Exception):
    pass


class Color(ABC):
    """Base class for all color representations"""

    def str(self) -> str:
        return self.__repr__()

    @abstractmethod
    def validate(self) -> None:
        pass

    @abstractmethod
    def get_value_keys(self) -> list[str]:
        pass

    @abstractmethod
    def RGB(self) -> RGB:
        """Convert to RGB color space"""
        pass

    @abstractmethod
    def HEX(self) -> HEX:
        """Convert to HEX color space"""
        pass

    @abstractmethod
    def HSV(self) -> HSV:
        """Convert to HSV color space"""
        pass

    @abstractmethod
    def HSL(self) -> HSL:
        """Convert to HSL color space"""
        pass

    @abstractmethod
    def CMYK(self) -> CMYK:
        """Convert to CMYK color space"""
        pass

    @abstractmethod
    def ASSA(self) -> ASSA:
        """Convert to ASS color format"""
        pass

    def copy(self):
        return deepcopy(self)

    def dict(self) -> dict[str, int | float | str]:
        return {k: getattr(self, k) for k in self.get_value_keys()}


class RGB(Color):
    def __init__(self, r: int, g: int, b: int):
        super().__init__()
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)
        self.validate()

    def validate(self) -> None:
        if not all(isinstance(x, int) and 0 <= x <= 255 for x in self.tuple()):
            raise ColorValueError("RGB values must be between 0 and 255")

    def get_value_keys(self) -> list[str]:
        return ["r", "g", "b"]

    def __repr__(self) -> str:
        return f"rgb({self.r}, {self.g}, {self.b})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RGB):
            return NotImplemented
        return (self.r, self.g, self.b) == (other.r, other.g, other.b)

    def tuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def RGB(self) -> RGB:
        return self.copy()

    def HSV(self) -> HSV:
        r, g, b = self.r / 255, self.g / 255, self.b / 255
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        diff = cmax - cmin

        if cmax == cmin:
            h = 0
        elif cmax == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif cmax == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        s = 0 if cmax == 0 else diff / cmax
        v = cmax

        return HSV(h, s * 100, v * 100)

    def HSL(self) -> HSL:
        r, g, b = self.r / 255, self.g / 255, self.b / 255
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        diff = cmax - cmin

        l = (cmax + cmin) / 2

        if diff == 0:
            h = 0
            s = 0
        else:
            s = diff / (2 - cmax - cmin) if l > 0.5 else diff / (cmax + cmin)

            if cmax == r:
                h = (60 * ((g - b) / diff) + 360) % 360
            elif cmax == g:
                h = (60 * ((b - r) / diff) + 120) % 360
            else:
                h = (60 * ((r - g) / diff) + 240) % 360

        return HSL(h, s * 100, l * 100)

    def CMYK(self) -> CMYK:
        r, g, b = self.r / 255, self.g / 255, self.b / 255

        k = 1 - max(r, g, b)
        if k == 1:
            c = m = y = 0
        else:
            c = (1 - r - k) / (1 - k)
            m = (1 - g - k) / (1 - k)
            y = (1 - b - k) / (1 - k)

        return CMYK(c * 100, m * 100, y * 100, k * 100)

    def HEX(self) -> HEX:
        return HEX(f"#{self.r:02x}{self.g:02x}{self.b:02x}")

    def RGBA(self, alpha: float = 1.0) -> RGBA:
        return RGBA(self.r, self.g, self.b, alpha)

    def ASSA(self) -> ASSA:
        return ASSA.from_RGB(self)


class RGBA(Color):
    def __init__(self, r: int, g: int, b: int, a: float = 1.0):
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)
        self.a = float(a)
        self.validate()

    def __repr__(self) -> str:
        return f"rgba({self.r}, {self.g}, {self.b}, {self.a})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RGBA):
            return NotImplemented
        return (self.r, self.g, self.b, self.a) == (other.r, other.g, other.b, other.a)

    def validate(self) -> None:
        if not all(isinstance(x, (int, float)) and 0 <= x <= 255 for x in (self.r, self.g, self.b)):
            raise ColorValueError("RGB values must be 0-255")
        if not isinstance(self.a, (int, float)) or not 0 <= self.a <= 1:
            raise ColorValueError("Alpha value must be 0-1")

    def get_value_keys(self) -> list[str]:
        return ["r", "g", "b", "a"]

    def tuple(self) -> tuple[int, int, int, float]:
        return (self.r, self.g, self.b, self.a)

    def RGB(self) -> RGB:
        return RGB(self.r, self.g, self.b)

    def RGBA(self) -> RGBA:
        return self.copy()

    def HSV(self) -> HSV:
        return self.RGB().HSV()

    def HSL(self) -> HSL:
        return self.RGB().HSL()

    def CMYK(self) -> CMYK:
        return self.RGB().CMYK()

    def HEX(self) -> HEX:
        return self.RGB().HEX()

    def ASSA(self) -> ASSA:
        alpha = round((1 - self.a) * 255)
        return ASSA.from_RGB(self.RGB(), alpha=alpha)

    @classmethod
    def from_assa(cls, assa: ASSA) -> RGBA:
        rgb = assa.RGB()
        alpha = assa.alpha
        if alpha is None:
            return cls(rgb.r, rgb.g, rgb.b, 1.0)
        # ASSA alpha (FF=transparent) -> RGBA alpha (1=opaque)
        return cls(rgb.r, rgb.g, rgb.b, 1 - (alpha / 255))


class HEX(Color):
    def __init__(self, value: str):
        if value.startswith("#"):
            value = value[1:]
        self.value = f"#{value.lower()}"
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.value, str):
            raise ColorValueError("HEX value must be a string")
        hex_value = self.value.lstrip("#")
        if len(hex_value) != 6 or not all(c in "0123456789ABCDEFabcdef" for c in hex_value):
            raise ColorValueError(f"Invalid HEX color format ({hex_value})")

    def get_value_keys(self) -> list[str]:
        return ["value"]

    def __repr__(self) -> str:
        return f"hex('{self.value}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HEX):
            return NotImplemented
        return self.value.lower() == other.value.lower()

    def str(self) -> str:
        return self.value

    def RGB(self) -> RGB:
        hex_value = self.value.lstrip("#")
        return RGB(int(hex_value[0:2], 16), int(hex_value[2:4], 16), int(hex_value[4:6], 16))

    def HSV(self) -> HSV:
        return self.RGB().HSV()

    def HSL(self) -> HSL:
        return self.RGB().HSL()

    def CMYK(self) -> CMYK:
        return self.RGB().CMYK()

    def HEX(self) -> HEX:
        return self.copy()

    def ASSA(self) -> ASSA:
        return self.RGB().ASSA()

    def webcolor(self) -> webcolor:
        return webcolor.from_hex(self.value)


class HSV(Color):
    def __init__(self, h: float, s: float, v: float):
        self.h = float(h)
        self.s = float(s)
        self.v = float(v)
        self.validate()

    def validate(self) -> None:
        if not (0 <= self.h <= 360 and 0 <= self.s <= 100 and 0 <= self.v <= 100):
            raise ColorValueError("HSV values must be: H[0-360], S[0-100], V[0-100]")

    def get_value_keys(self) -> list[str]:
        return ["h", "s", "v"]

    def __repr__(self) -> str:
        return f"hsv({self.h}, {self.s}, {self.v})"

    def str(self) -> str:
        return f"hsv({self.h}°, {self.s}%, {self.v}%)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HSV):
            return NotImplemented
        return (self.h, self.s, self.v) == (other.h, other.s, other.v)

    def tuple(self) -> tuple[float, float, float]:
        return (self.h, self.s, self.v)

    def RGB(self) -> RGB:
        h, s, v = self.h, self.s / 100, self.v / 100
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x

        return RGB(round((r + m) * 255), round((g + m) * 255), round((b + m) * 255))

    def HSV(self) -> HSV:
        return self.copy()

    def HSL(self) -> HSL:
        return self.RGB().HSL()

    def CMYK(self) -> CMYK:
        return self.RGB().CMYK()

    def HEX(self) -> HEX:
        return self.RGB().HEX()

    def ASSA(self) -> ASSA:
        return self.RGB().ASSA()


class HSL(Color):
    def __init__(self, h: float, s: float, l: float):
        self.h = float(h)
        self.s = float(s)
        self.l = float(l)
        self.validate()

    def validate(self) -> None:
        if not (0 <= self.h <= 360 and 0 <= self.s <= 100 and 0 <= self.l <= 100):
            raise ColorValueError("HSL values must be: H[0-360], S[0-100], L[0-100]")

    def get_value_keys(self) -> list[str]:
        return ["h", "s", "l"]

    def __repr__(self) -> str:
        return f"hsl({self.h}, {self.s}, {self.l})"

    def str(self) -> str:
        return f"hsl({self.h}°, {self.s}%, {self.l}%)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HSL):
            return NotImplemented
        return (self.h, self.s, self.l) == (other.h, other.s, other.l)

    def tuple(self) -> tuple[float, float, float]:
        return (self.h, self.s, self.l)

    def RGB(self) -> RGB:
        h, s, l = self.h / 360, self.s / 100, self.l / 100

        if s == 0:
            r = g = b = l
        else:

            def hue_to_rgb(p: float, q: float, t: float) -> float:
                if t < 0:
                    t += 1
                if t > 1:
                    t -= 1
                if t < 1 / 6:
                    return p + (q - p) * 6 * t
                if t < 1 / 2:
                    return q
                if t < 2 / 3:
                    return p + (q - p) * (2 / 3 - t) * 6
                return p

            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q

            r = hue_to_rgb(p, q, h + 1 / 3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1 / 3)

        return RGB(round(r * 255), round(g * 255), round(b * 255))

    def HSV(self) -> HSV:
        return self.RGB().HSV()

    def HSL(self) -> HSL:
        return self.copy()

    def CMYK(self) -> CMYK:
        return self.RGB().CMYK()

    def HEX(self) -> HEX:
        return self.RGB().HEX()

    def ASSA(self) -> ASSA:
        return self.RGB().ASSA()


class CMYK(Color):
    def __init__(self, c: float, m: float, y: float, k: float):
        self.c = float(c)
        self.m = float(m)
        self.y = float(y)
        self.k = float(k)
        self.validate()

    def validate(self) -> None:
        if not all(0 <= x <= 100 for x in (self.c, self.m, self.y, self.k)):
            raise ColorValueError("CMYK values must be between 0 and 100")

    def get_value_keys(self) -> list[str]:
        return ["c", "m", "y", "k"]

    def __repr__(self) -> str:
        return f"cmyk({self.c}, {self.m}, {self.y}, {self.k})"

    def str(self) -> str:
        return f"cmyk({self.c}%, {self.m}%, {self.y}%, {self.k}%)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CMYK):
            return NotImplemented
        return (self.c, self.m, self.y, self.k) == (other.c, other.m, other.y, other.k)

    def tuple(self) -> tuple[float, float, float, float]:
        return (self.c, self.m, self.y, self.k)

    def RGB(self) -> RGB:
        c, m, y, k = self.c / 100, self.m / 100, self.y / 100, self.k / 100

        r = 255 * (1 - c) * (1 - k)
        g = 255 * (1 - m) * (1 - k)
        b = 255 * (1 - y) * (1 - k)

        return RGB(round(r), round(g), round(b))

    def HSV(self) -> HSV:
        return self.RGB().HSV()

    def HSL(self) -> HSL:
        return self.RGB().HSL()

    def CMYK(self) -> CMYK:
        return self.copy()

    def HEX(self) -> HEX:
        return self.RGB().HEX()

    def ASSA(self) -> ASSA:
        return self.RGB().ASSA()


class ASSA(Color):
    def __init__(self, value: str):
        """
        Initialize ASSA color with just hex numbers:
        - 'BBGGRR' for color
        - 'AABBGGRR' for color with alpha
        """

        clean_value = "".join(c for c in value.lower() if c in "0123456789abcdef")
        self.value = f"&H{clean_value}&"
        self.validate()

    def get_value_keys(self) -> list[str]:
        return ["value"]

    @property
    def clean_value(self) -> str:
        """Get the value without &H prefix and & suffix"""
        return self.value[2:-1]

    def __repr__(self) -> str:
        return f"assa('{self.clean_value}')"

    def __str__(self) -> str:
        return self.str()

    def str(self) -> str:
        """Return the full ASS format string"""
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASSA):
            return NotImplemented
        return self.clean_value == other.clean_value

    def validate(self) -> None:
        if not isinstance(self.value, str):
            raise ColorValueError("ASSA value must be a string")
        if len(self.clean_value) not in (6, 8):
            raise ColorValueError(
                "Color value must be either 6 (BBGGRR) or 8 (AABBGGRR) hex digits"
            )

        if not all(c in "0123456789abcdef" for c in self.clean_value):
            raise ColorValueError("Invalid hex digits in color value")

    @property
    def alpha(self) -> int | None:
        """Get alpha value if present (00=opaque, FF=transparent)"""
        clean = self.clean_value
        if len(clean) == 8:  # AABBGGRR format
            return int(clean[0:2], 16)
        return None

    def is_BBGGRR_format(self) -> bool:
        return len(self.clean_value) == 6

    def is_AABBGGRR_format(self) -> bool:
        return len(self.clean_value) == 8

    def RGB(self) -> RGB:
        clean = self.clean_value
        if self.is_BBGGRR_format():
            b = int(clean[0:2], 16)
            g = int(clean[2:4], 16)
            r = int(clean[4:6], 16)
        else:  # AABBGGRR
            b = int(clean[2:4], 16)
            g = int(clean[4:6], 16)
            r = int(clean[6:8], 16)
        return RGB(r, g, b)

    def HSV(self) -> HSV:
        return self.RGB().HSV()

    def HSL(self) -> HSL:
        return self.RGB().HSL()

    def CMYK(self) -> CMYK:
        return self.RGB().CMYK()

    def HEX(self) -> HEX:
        return self.RGB().HEX()

    def ASSA(self) -> ASSA:
        return self.copy()

    def embed_text(self, text: str) -> str:
        """Embed text with this color in ASS format"""
        return f"{{\\c{self.value}}}{text}{{\\c}}"

    @staticmethod
    def is_valid_format(value: str) -> bool:
        """Check if the cleaned value has valid length and hex digits"""
        clean_value = "".join(c for c in value.lower() if c in "0123456789abcdef")
        return len(clean_value) in (6, 8) and all(c in "0123456789abcdef" for c in clean_value)

    @classmethod
    def from_alpha(cls, alpha: int) -> ASSA:
        """Create transparency-only ASSA value"""
        if not 0 <= alpha <= 255:
            raise ColorValueError("Alpha value must be 0-255")
        return cls(f"{alpha:02x}000000")

    @classmethod
    def from_RGB(cls, rgb: RGB, alpha: int | None = None) -> ASSA:
        """Create ASSA color from RGB values with optional alpha"""
        if alpha is not None:
            if not 0 <= alpha <= 255:
                raise ColorValueError("Alpha value must be 0-255")
            value = f"{alpha:02x}{rgb.b:02x}{rgb.g:02x}{rgb.r:02x}"
        else:
            value = f"{rgb.b:02x}{rgb.g:02x}{rgb.r:02x}"
        return cls(value)

    @classmethod
    def from_RGBA(cls, rgba: RGBA) -> ASSA:
        """Create ASSA color from RGBA values"""
        return cls.from_RGB(rgba.RGB(), alpha=round((1 - rgba.a) * 255))


CSS_COLOR_NAME = T.Literal[
    "aliceblue",
    "antiquewhite",
    "aqua",
    "aquamarine",
    "azure",
    "beige",
    "bisque",
    "black",
    "blanchedalmond",
    "blue",
    "blueviolet",
    "brown",
    "burlywood",
    "cadetblue",
    "chartreuse",
    "chocolate",
    "coral",
    "cornflowerblue",
    "cornsilk",
    "crimson",
    "cyan",
    "darkblue",
    "darkcyan",
    "darkgoldenrod",
    "darkgray",
    "darkgrey",
    "darkgreen",
    "darkkhaki",
    "darkmagenta",
    "darkolivegreen",
    "darkorange",
    "darkorchid",
    "darkred",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "deeppink",
    "deepskyblue",
    "dimgray",
    "dimgrey",
    "dodgerblue",
    "firebrick",
    "floralwhite",
    "forestgreen",
    "fuchsia",
    "gainsboro",
    "ghostwhite",
    "gold",
    "goldenrod",
    "gray",
    "grey",
    "green",
    "greenyellow",
    "honeydew",
    "hotpink",
    "indianred",
    "indigo",
    "ivory",
    "khaki",
    "lavender",
    "lavenderblush",
    "lawngreen",
    "lemonchiffon",
    "lightblue",
    "lightcoral",
    "lightcyan",
    "lightgoldenrodyellow",
    "lightgray",
    "lightgrey",
    "lightgreen",
    "lightpink",
    "lightsalmon",
    "lightseagreen",
    "lightskyblue",
    "lightslategray",
    "lightslategrey",
    "lightsteelblue",
    "lightyellow",
    "lime",
    "limegreen",
    "linen",
    "magenta",
    "maroon",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "mediumspringgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "mistyrose",
    "moccasin",
    "navajowhite",
    "navy",
    "oldlace",
    "olive",
    "olivedrab",
    "orange",
    "orangered",
    "orchid",
    "palegoldenrod",
    "palegreen",
    "paleturquoise",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "pink",
    "plum",
    "powderblue",
    "purple",
    "rebeccapurple",
    "red",
    "rosybrown",
    "royalblue",
    "saddlebrown",
    "salmon",
    "sandybrown",
    "seagreen",
    "seashell",
    "sienna",
    "silver",
    "skyblue",
    "slateblue",
    "slategray",
    "slategrey",
    "snow",
    "springgreen",
    "steelblue",
    "tan",
    "teal",
    "thistle",
    "tomato",
    "turquoise",
    "violet",
    "wheat",
    "white",
    "whitesmoke",
    "yellow",
    "yellowgreen",
]

CSS_COLOR_TO_HEX = {
    "aliceblue": "#F0F8FF",
    "antiquewhite": "#FAEBD7",
    "aqua": "#00FFFF",
    "aquamarine": "#7FFFD4",
    "azure": "#F0FFFF",
    "beige": "#F5F5DC",
    "bisque": "#FFE4C4x",
    "black": "#000000",
    "blanchedalmond": "#FFEBCD",
    "blue": "#0000FF",
    "blueviolet": "#8A2BE2",
    "brown": "#A52A2A",
    "burlywood": "#DEB887",
    "cadetblue": "#5F9EA0",
    "chartreuse": "#7FFF00",
    "chocolate": "#D2691E",
    "coral": "#FF7F50",
    "cornflowerblue": "#6495ED",
    "cornsilk": "#FFF8DC",
    "crimson": "#DC143C",
    "cyan": "#00FFFF",
    "darkblue": "#00008B",
    "darkcyan": "#008B8B",
    "darkgoldenrod": "#B8860B",
    "darkgray": "#A9A9A9",
    "darkgrey": "#A9A9A9",
    "darkgreen": "#006400",
    "darkkhaki": "#BDB76B",
    "darkmagenta": "#8B008B",
    "darkolivegreen": "#556B2F",
    "darkorange": "#FF8C00",
    "darkorchid": "#9932CC",
    "darkred": "#8B0000",
    "darksalmon": "#E9967A",
    "darkseagreen": "#8FBC8F",
    "darkslateblue": "#483D8B",
    "darkslategray": "#2F4F4F",
    "darkslategrey": "#2F4F4F",
    "darkturquoise": "#00CED1",
    "darkviolet": "#9400D3",
    "deeppink": "#FF1493",
    "deepskyblue": "#00BFFF",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1E90FF",
    "firebrick": "#B22222",
    "floralwhite": "#FFFAF0",
    "forestgreen": "#228B22",
    "fuchsia": "#FF00FF",
    "gainsboro": "#DCDCDC",
    "ghostwhite": "#F8F8FF",
    "gold": "#FFD700",
    "goldenrod": "#DAA520",
    "gray": "#808080",
    "grey": "#808080",
    "green": "#008000",
    "greenyellow": "#ADFF2F",
    "honeydew": "#F0FFF0",
    "hotpink": "#FF69B4",
    "indianred": "#CD5C5C",
    "indigo": "#4B0082",
    "ivory": "#FFFFF0",
    "khaki": "#F0E68C",
    "lavender": "#E6E6FA",
    "lavenderblush": "#FFF0F5",
    "lawngreen": "#7CFC00",
    "lemonchiffon": "#FFFACD",
    "lightblue": "#ADD8E6",
    "lightcoral": "#F08080",
    "lightcyan": "#E0FFFF",
    "lightgoldenrodyellow": "#FAFAD2",
    "lightgray": "#D3D3D3",
    "lightgrey": "#D3D3D3",
    "lightgreen": "#90EE90",
    "lightpink": "#FFB6C1",
    "lightsalmon": "#FFA07A",
    "lightseagreen": "#20B2AA",
    "lightskyblue": "#87CEFA",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#B0C4DE",
    "lightyellow": "#FFFFE0",
    "lime": "#00FF00",
    "limegreen": "#32CD32",
    "linen": "#FAF0E6",
    "magenta": "#FF00FF",
    "maroon": "#800000",
    "mediumaquamarine": "#66CDAA",
    "mediumblue": "#0000CD",
    "mediumorchid": "#BA55D3",
    "mediumpurple": "#9370DB",
    "mediumseagreen": "#3CB371",
    "mediumslateblue": "#7B68EE",
    "mediumspringgreen": "#00FA9A",
    "mediumturquoise": "#48D1CC",
    "mediumvioletred": "#C71585",
    "midnightblue": "#191970",
    "mintcream": "#F5FFFA",
    "mistyrose": "#FFE4E1",
    "moccasin": "#FFE4B5",
    "navajowhite": "#FFDEAD",
    "navy": "#000080",
    "oldlace": "#FDF5E6",
    "olive": "#808000",
    "olivedrab": "#6B8E23",
    "orange": "#FFA500",
    "orangered": "#FF4500",
    "orchid": "#DA70D6",
    "palegoldenrod": "#EEE8AA",
    "palegreen": "#98FB98",
    "paleturquoise": "#AFEEEE",
    "palevioletred": "#DB7093",
    "papayawhip": "#FFEFD5",
    "peachpuff": "#FFDAB9",
    "peru": "#CD853F",
    "pink": "#FFC0CB",
    "plum": "#DDA0DD",
    "powderblue": "#B0E0E6",
    "purple": "#800080",
    "rebeccapurple": "#663399",
    "red": "#FF0000",
    "rosybrown": "#BC8F8F",
    "royalblue": "#4169E1",
    "saddlebrown": "#8B4513",
    "salmon": "#FA8072",
    "sandybrown": "#F4A460",
    "seagreen": "#2E8B57",
    "seashell": "#FFF5EE",
    "sienna": "#A0522D",
    "silver": "#C0C0C0",
    "skyblue": "#87CEEB",
    "slateblue": "#6A5ACD",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#FFFAFA",
    "springgreen": "#00FF7F",
    "steelblue": "#4682B4",
    "tan": "#D2B48C",
    "teal": "#008080",
    "thistle": "#D8BFD8",
    "tomato": "#FF6347",
    "turquoise": "#40E0D0",
    "violet": "#EE82EE",
    "wheat": "#F5DEB3",
    "white": "#FFFFFF",
    "whitesmoke": "#F5F5F5",
    "yellow": "#FFFF00",
    "yellowgreen": "#9ACD32",
}


class webcolor(Color):
    COLORS = CSS_COLOR_TO_HEX

    def __init__(self, name: CSS_COLOR_NAME):
        name = name.lower()  # type:ignore
        self.name = name
        self.validate()
        self.hex_value = HEX(self.COLORS[name])

    def validate(self) -> None:
        if self.name not in self.COLORS:
            raise ColorValueError(f"Unknown web color name '{self.name}'")

    def get_value_keys(self) -> list[str]:
        return ["name"]

    def __repr__(self) -> str:
        return f"webcolor('{self.name}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, webcolor):
            return NotImplemented
        return self.name == other.name

    def str(self) -> str:
        return self.name

    def RGB(self) -> RGB:
        return self.hex_value.RGB()

    def HSV(self) -> HSV:
        return self.hex_value.HSV()

    def HSL(self) -> HSL:
        return self.hex_value.HSL()

    def CMYK(self) -> CMYK:
        return self.hex_value.CMYK()

    def HEX(self) -> HEX:
        return self.hex_value

    def webcolor(self) -> webcolor:
        return self.copy()

    def ASSA(self) -> ASSA:
        return self.hex_value.ASSA()

    @classmethod
    def from_hex(cls, value: str) -> webcolor:
        value = value.lower()
        for name, color in cls.COLORS.items():
            if color.lower() == value:
                return cls(name)
        raise ColorValueError(f"No web color name matches hex value {value}")


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    if len(c) != 6:
        raise ValueError(color)
    r = int(c[0:2], 16)
    g = int(c[2:4], 16)
    b = int(c[4:6], 16)
    return (r, g, b)


def normalize_color(
    color: (
        str
        | CSS_COLOR_NAME
        | tuple[int, int, int]
        | tuple[int, int, int, float]
        | Sequence[int]
        | Sequence[float]
    ),
) -> RGB | RGBA | HEX | ASSA | webcolor:
    """Convert various color formats to a Color object."""
    if isinstance(color, SequenceType) and all(isinstance(x, (int, float)) for x in color):
        if len(color) == 3:
            return RGB(*color)
        elif len(color) == 4:
            return RGBA(*color)
        raise ColorValueError(f"Invalid sequence length: {len(color)}")
    elif isinstance(color, str):
        if color.startswith("#"):
            return HEX(color)
        elif color.startswith("&h") or color.startswith("&H"):
            return ASSA(color)
        else:
            return webcolor(color)
    raise ColorValueError(f"Unsupported color format: {color}")


__all__ = [
    "Color",
    "RGB",
    "RGBA",
    "HEX",
    "HSV",
    "HSL",
    "CMYK",
    "ASSA",
    "webcolor",
    "CSS_COLOR_TO_HEX",
    "CSS_COLOR_NAME",
    "ColorValueError",
    "normalize_color",
]
