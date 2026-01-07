from __future__ import annotations

import builtins
import re
import typing as T
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from collections.abc import Sequence as SequenceType


class ColorValueError(Exception):
    pass


class Color(ABC):
    """Base class for all color representations"""

    __slots__ = ("_frozen",)

    def __init__(self) -> None:
        object.__setattr__(self, "_frozen", False)

    def _freeze(self) -> None:
        object.__setattr__(self, "_frozen", True)

    def to_str(self) -> builtins.str:
        return self.__repr__()

    @abstractmethod
    def validate(self) -> None:
        pass

    @abstractmethod
    def get_value_keys(self) -> list[builtins.str]:
        pass

    @abstractmethod
    def to_rgb(self) -> RGB:
        """Convert to RGB color space"""
        pass

    @abstractmethod
    def to_hex(self) -> HEX:
        """Convert to HEX color space"""
        pass

    @abstractmethod
    def to_hsv(self) -> HSV:
        """Convert to HSV color space"""
        pass

    @abstractmethod
    def to_hsl(self) -> HSL:
        """Convert to HSL color space"""
        pass

    @abstractmethod
    def to_cmyk(self) -> CMYK:
        """Convert to CMYK color space"""
        pass

    @abstractmethod
    def to_assa(self) -> ASSA:
        """Convert to ASS color format"""
        pass

    def copy(self) -> Color:
        return self

    def dict(self) -> dict[builtins.str, int | float | builtins.str]:
        return {k: getattr(self, k) for k in self.get_value_keys()}

    def __setattr__(self, name: builtins.str, value: T.Any) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} is immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: builtins.str) -> None:
        raise AttributeError(f"{self.__class__.__name__} is immutable")


class RGB(Color):
    __slots__ = ("red", "green", "blue")
    red: int
    green: int
    blue: int

    def __init__(self, red: int, green: int, blue: int):
        super().__init__()
        self.red = int(red)
        self.green = int(green)
        self.blue = int(blue)
        self.validate()
        self._freeze()

    def validate(self) -> None:
        if not all(isinstance(x, int) and 0 <= x <= 255 for x in self.tuple()):
            raise ColorValueError("RGB values must be between 0 and 255")

    def get_value_keys(self) -> list[str]:
        return ["red", "green", "blue"]

    def __repr__(self) -> str:
        return f"rgb({self.red}, {self.green}, {self.blue})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RGB):
            return NotImplemented
        return (self.red, self.green, self.blue) == (other.red, other.green, other.blue)

    def tuple(self) -> tuple[int, int, int]:
        return (self.red, self.green, self.blue)

    def to_rgb(self) -> RGB:
        return self

    def to_hsv(self) -> HSV:
        r, g, b = self.red / 255, self.green / 255, self.blue / 255
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        diff = cmax - cmin

        if cmax == cmin:
            h = 0.0
        elif cmax == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif cmax == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        s = 0 if cmax == 0 else diff / cmax
        v = cmax

        return HSV(h, s * 100, v * 100)

    def to_hsl(self) -> HSL:
        r, g, b = self.red / 255, self.green / 255, self.blue / 255
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        diff = cmax - cmin

        l = (cmax + cmin) / 2

        if diff == 0:
            h = 0.0
            s = 0.0
        else:
            s = diff / (2 - cmax - cmin) if l > 0.5 else diff / (cmax + cmin)

            if cmax == r:
                h = (60 * ((g - b) / diff) + 360) % 360
            elif cmax == g:
                h = (60 * ((b - r) / diff) + 120) % 360
            else:
                h = (60 * ((r - g) / diff) + 240) % 360

        return HSL(h, s * 100, l * 100)

    def to_cmyk(self) -> CMYK:
        r, g, b = self.red / 255, self.green / 255, self.blue / 255

        k = 1 - max(r, g, b)
        if k == 1:
            c = m = y = 0.0
        else:
            c = (1 - r - k) / (1 - k)
            m = (1 - g - k) / (1 - k)
            y = (1 - b - k) / (1 - k)

        return CMYK(c * 100, m * 100, y * 100, k * 100)

    def to_hex(self) -> HEX:
        return HEX(f"#{self.red:02x}{self.green:02x}{self.blue:02x}")

    def to_rgba(self, alpha: float = 1.0) -> RGBA:
        return RGBA(self.red, self.green, self.blue, alpha)

    def to_assa(self) -> ASSA:
        return ASSA.from_rgb(self)


class RGBA(Color):
    __slots__ = ("red", "green", "blue", "alpha")
    red: int
    green: int
    blue: int
    alpha: float

    def __init__(self, red: int, green: int, blue: int, alpha: float = 1.0):
        super().__init__()
        self.red = int(red)
        self.green = int(green)
        self.blue = int(blue)
        self.alpha = float(alpha)
        self.validate()
        self._freeze()

    def __repr__(self) -> str:
        return f"rgba({self.red}, {self.green}, {self.blue}, {self.alpha})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RGBA):
            return NotImplemented
        return (self.red, self.green, self.blue, self.alpha) == (
            other.red,
            other.green,
            other.blue,
            other.alpha,
        )

    def validate(self) -> None:
        if not all(
            isinstance(x, (int, float)) and 0 <= x <= 255 for x in (self.red, self.green, self.blue)
        ):
            raise ColorValueError("RGB values must be 0-255")
        if not isinstance(self.alpha, (int, float)) or not 0 <= self.alpha <= 1:
            raise ColorValueError("Alpha value must be 0-1")

    def get_value_keys(self) -> list[str]:
        return ["red", "green", "blue", "alpha"]

    def tuple(self) -> tuple[int, int, int, float]:
        return (self.red, self.green, self.blue, self.alpha)

    def to_rgb(self) -> RGB:
        return RGB(self.red, self.green, self.blue)

    def to_rgba(self) -> RGBA:
        return self

    def to_hsv(self) -> HSV:
        return self.to_rgb().to_hsv()

    def to_hsl(self) -> HSL:
        return self.to_rgb().to_hsl()

    def to_cmyk(self) -> CMYK:
        return self.to_rgb().to_cmyk()

    def to_hex(self) -> HEX:
        return self.to_rgb().to_hex()

    def to_assa(self) -> ASSA:
        return ASSA.from_rgba(self)

    @classmethod
    def from_assa(cls, assa: ASSA) -> RGBA:
        rgb = assa.to_rgb()
        alpha = assa.alpha
        if alpha is None:
            return cls(rgb.red, rgb.green, rgb.blue, 1.0)
        # ASSA alpha (FF=transparent) -> RGBA alpha (1=opaque)
        return cls(rgb.red, rgb.green, rgb.blue, 1 - (alpha / 255))


class HEX(Color):
    __slots__ = ("value",)
    value: str

    def __init__(self, value: str):
        super().__init__()
        if value.startswith("#"):
            value = value[1:]
        self.value = f"#{value.lower()}"
        self.validate()
        self._freeze()

    def validate(self) -> None:
        if not isinstance(self.value, str):
            raise ColorValueError("HEX value must be a string")
        hex_value = self.value.lstrip("#")
        if len(hex_value) != 6 or not all(c in "0123456789ABCDEFabcdef" for c in hex_value):
            raise ColorValueError(f"Invalid HEX color format ({hex_value})")

    def get_value_keys(self) -> list[str]:
        return ["value"]

    def __repr__(self) -> str:
        return f"hex({self.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HEX):
            return NotImplemented
        return self.value.lower() == other.value.lower()

    def to_str(self) -> builtins.str:
        return self.value

    def to_rgb(self) -> RGB:
        hex_value = self.value.lstrip("#")
        return RGB(int(hex_value[0:2], 16), int(hex_value[2:4], 16), int(hex_value[4:6], 16))

    def to_hsv(self) -> HSV:
        return self.to_rgb().to_hsv()

    def to_hsl(self) -> HSL:
        return self.to_rgb().to_hsl()

    def to_cmyk(self) -> CMYK:
        return self.to_rgb().to_cmyk()

    def to_hex(self) -> HEX:
        return self

    def to_assa(self) -> ASSA:
        return self.to_rgb().to_assa()

    def to_webcolor(self) -> webcolor:
        return webcolor.from_hex(self.value)


class HSV(Color):
    __slots__ = ("hue", "saturation", "value")
    hue: float
    saturation: float
    value: float

    def __init__(self, hue: float, saturation: float, value: float):
        super().__init__()
        self.hue = float(hue)
        self.saturation = float(saturation)
        self.value = float(value)
        self.validate()
        self._freeze()

    def validate(self) -> None:
        if not (0 <= self.hue <= 360 and 0 <= self.saturation <= 100 and 0 <= self.value <= 100):
            raise ColorValueError("HSV values must be: H[0-360], S[0-100], V[0-100]")

    def get_value_keys(self) -> list[str]:
        return ["hue", "saturation", "value"]

    def __repr__(self) -> str:
        return f"hsv({self.hue}, {self.saturation}, {self.value})"

    def to_str(self) -> builtins.str:
        return f"hsv({self.hue}°, {self.saturation}%, {self.value}%)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HSV):
            return NotImplemented
        return (self.hue, self.saturation, self.value) == (
            other.hue,
            other.saturation,
            other.value,
        )

    def tuple(self) -> tuple[float, float, float]:
        return (self.hue, self.saturation, self.value)

    def to_rgb(self) -> RGB:
        h, s, v = self.hue, self.saturation / 100, self.value / 100
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        if 0 <= h < 60:
            r, g, b = c, x, 0.0
        elif 60 <= h < 120:
            r, g, b = x, c, 0.0
        elif 120 <= h < 180:
            r, g, b = 0.0, c, x
        elif 180 <= h < 240:
            r, g, b = 0.0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0.0, c
        else:
            r, g, b = c, 0.0, x

        return RGB(round((r + m) * 255), round((g + m) * 255), round((b + m) * 255))

    def to_hsv(self) -> HSV:
        return self

    def to_hsl(self) -> HSL:
        return self.to_rgb().to_hsl()

    def to_cmyk(self) -> CMYK:
        return self.to_rgb().to_cmyk()

    def to_hex(self) -> HEX:
        return self.to_rgb().to_hex()

    def to_assa(self) -> ASSA:
        return self.to_rgb().to_assa()


class HSL(Color):
    __slots__ = ("hue", "saturation", "lightness")
    hue: float
    saturation: float
    lightness: float

    def __init__(self, hue: float, saturation: float, lightness: float):
        super().__init__()
        self.hue = float(hue)
        self.saturation = float(saturation)
        self.lightness = float(lightness)
        self.validate()
        self._freeze()

    def validate(self) -> None:
        if not (
            0 <= self.hue <= 360 and 0 <= self.saturation <= 100 and 0 <= self.lightness <= 100
        ):
            raise ColorValueError("HSL values must be: H[0-360], S[0-100], L[0-100]")

    def get_value_keys(self) -> list[str]:
        return ["hue", "saturation", "lightness"]

    def __repr__(self) -> str:
        return f"hsl({self.hue}, {self.saturation}, {self.lightness})"

    def to_str(self) -> builtins.str:
        return f"hsl({self.hue}°, {self.saturation}%, {self.lightness}%)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HSL):
            return NotImplemented
        return (self.hue, self.saturation, self.lightness) == (
            other.hue,
            other.saturation,
            other.lightness,
        )

    def tuple(self) -> tuple[float, float, float]:
        return (self.hue, self.saturation, self.lightness)

    def to_rgb(self) -> RGB:
        hue, saturation, lightness = self.hue / 360, self.saturation / 100, self.lightness / 100

        if saturation == 0:
            r = g = b = lightness
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

            q = (
                lightness * (1 + saturation)
                if lightness < 0.5
                else lightness + saturation - lightness * saturation
            )
            p = 2 * lightness - q

            r = hue_to_rgb(p, q, hue + 1 / 3)
            g = hue_to_rgb(p, q, hue)
            b = hue_to_rgb(p, q, hue - 1 / 3)

        return RGB(round(r * 255), round(g * 255), round(b * 255))

    def to_hsv(self) -> HSV:
        return self.to_rgb().to_hsv()

    def to_hsl(self) -> HSL:
        return self

    def to_cmyk(self) -> CMYK:
        return self.to_rgb().to_cmyk()

    def to_hex(self) -> HEX:
        return self.to_rgb().to_hex()

    def to_assa(self) -> ASSA:
        return self.to_rgb().to_assa()


class CMYK(Color):
    __slots__ = ("cyan", "magenta", "yellow", "key")
    cyan: float
    magenta: float
    yellow: float
    key: float

    def __init__(self, cyan: float, magenta: float, yellow: float, key: float):
        super().__init__()
        self.cyan = float(cyan)
        self.magenta = float(magenta)
        self.yellow = float(yellow)
        self.key = float(key)
        self.validate()
        self._freeze()

    def validate(self) -> None:
        if not all(0 <= x <= 100 for x in (self.cyan, self.magenta, self.yellow, self.key)):
            raise ColorValueError("CMYK values must be between 0 and 100")

    def get_value_keys(self) -> list[str]:
        return ["cyan", "magenta", "yellow", "key"]

    def __repr__(self) -> str:
        return f"cmyk({self.cyan}, {self.magenta}, {self.yellow}, {self.key})"

    def to_str(self) -> builtins.str:
        return f"cmyk({self.cyan}%, {self.magenta}%, {self.yellow}%, {self.key}%)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CMYK):
            return NotImplemented
        return (self.cyan, self.magenta, self.yellow, self.key) == (
            other.cyan,
            other.magenta,
            other.yellow,
            other.key,
        )

    def tuple(self) -> tuple[float, float, float, float]:
        return (self.cyan, self.magenta, self.yellow, self.key)

    def to_rgb(self) -> RGB:
        c, m, y, k = self.cyan / 100, self.magenta / 100, self.yellow / 100, self.key / 100

        r = 255 * (1 - c) * (1 - k)
        g = 255 * (1 - m) * (1 - k)
        b = 255 * (1 - y) * (1 - k)

        return RGB(round(r), round(g), round(b))

    def to_hsv(self) -> HSV:
        return self.to_rgb().to_hsv()

    def to_hsl(self) -> HSL:
        return self.to_rgb().to_hsl()

    def to_cmyk(self) -> CMYK:
        return self

    def to_hex(self) -> HEX:
        return self.to_rgb().to_hex()

    def to_assa(self) -> ASSA:
        return self.to_rgb().to_assa()


class ASSA(Color):
    __slots__ = ("value",)
    value: str

    def __init__(self, value: str):
        """
        Initialize ASSA color with just hex numbers:
        - 'BBGGRR' for color
        - 'AABBGGRR' for color with alpha
        """
        super().__init__()
        clean_value = "".join(c for c in value.lower() if c in "0123456789abcdef")
        self.value = f"&H{clean_value}&"
        self.validate()
        self._freeze()

    def get_value_keys(self) -> list[str]:
        return ["value"]

    @property
    def clean_value(self) -> str:
        value = self.value
        if (value.startswith("&H") or value.startswith("&h")) and value.endswith("&"):
            return value[2:-1].lower()
        return value.lower()

    def __repr__(self) -> str:
        return f"assa({self.clean_value})"

    def to_str(self) -> builtins.str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASSA):
            return NotImplemented
        return self.value == other.value

    def validate(self) -> None:
        if not self.is_valid_format(self.value):
            raise ColorValueError(
                "Color value must be either 6 (BBGGRR) or 8 (AABBGGRR) hexadecimal digits"
            )

    def is_BBGGRR_format(self) -> bool:
        return len(self.clean_value) == 6

    def is_AABBGGRR_format(self) -> bool:
        return len(self.clean_value) == 8

    def to_rgb(self) -> RGB:
        clean = self.clean_value
        if len(clean) == 6:
            blue_hex = clean[0:2]
            green_hex = clean[2:4]
            red_hex = clean[4:6]
        else:
            blue_hex = clean[2:4]
            green_hex = clean[4:6]
            red_hex = clean[6:8]
        return RGB(int(red_hex, 16), int(green_hex, 16), int(blue_hex, 16))

    @property
    def blue(self) -> int:
        clean = self.clean_value
        if len(clean) == 6:
            return int(clean[0:2], 16)
        else:
            return int(clean[2:4], 16)

    @property
    def green(self) -> int:
        clean = self.clean_value
        if len(clean) == 6:
            return int(clean[2:4], 16)
        else:
            return int(clean[4:6], 16)

    @property
    def red(self) -> int:
        clean = self.clean_value
        if len(clean) == 6:
            return int(clean[4:6], 16)
        else:
            return int(clean[6:8], 16)

    @property
    def alpha(self) -> int | None:
        clean = self.clean_value
        if len(clean) == 6:
            return None
        else:
            return int(clean[0:2], 16)

    def to_hsv(self) -> HSV:
        return self.to_rgb().to_hsv()

    def to_hsl(self) -> HSL:
        return self.to_rgb().to_hsl()

    def to_cmyk(self) -> CMYK:
        return self.to_rgb().to_cmyk()

    def to_hex(self) -> HEX:
        return self.to_rgb().to_hex()

    def to_assa(self) -> ASSA:
        return self

    def embed_text(self, text: str) -> str:
        """Embed text with this color in ASS format"""
        return f"{{\\c{self.value}}}{text}{{\\c}}"

    @staticmethod
    def is_valid_format(value: str) -> bool:
        clean_value = ASSA._clean_hex(value)
        return len(clean_value) in (6, 8)

    @classmethod
    def from_alpha(cls, alpha: int) -> ASSA:
        if not 0 <= alpha <= 255:
            raise ColorValueError("Alpha value must be 0-255")
        return cls(f"{alpha:02X}000000")

    @classmethod
    def from_rgb(cls, rgb: RGB, alpha: int | None = None) -> ASSA:
        if alpha is not None and not 0 <= alpha <= 255:
            raise ColorValueError("Alpha value must be 0-255")
        if alpha is None:
            return cls(f"{rgb.blue:02X}{rgb.green:02X}{rgb.red:02X}")
        else:
            return cls(f"{alpha:02X}{rgb.blue:02X}{rgb.green:02X}{rgb.red:02X}")

    @classmethod
    def from_rgba(cls, rgba: RGBA) -> ASSA:
        return cls.from_rgb(rgba.to_rgb(), alpha=round((1 - rgba.alpha) * 255))

    @classmethod
    def from_clean_value(cls, value: str) -> ASSA:
        clean = cls._clean_hex(value)
        if len(clean) not in (6, 8):
            raise ColorValueError(
                "Color value must be either 6 (BBGGRR) or 8 (AABBGGRR) hex digits"
            )
        return cls(clean)

    @classmethod
    def from_value(cls, value: str) -> ASSA:
        """Create an ASSA color from a string (with or without &H markers)."""
        clean_value = "".join(c for c in value.lower() if c in "0123456789abcdef")
        return cls(clean_value)

    @staticmethod
    def _clean_hex(value: str) -> str:
        return "".join(c for c in value.upper() if c in "0123456789ABCDEF")


CssColorName = T.Literal[
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
    "bisque": "#FFE4C4",
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
    __slots__ = ("name", "hex_value")
    name: str
    hex_value: HEX
    COLORS = CSS_COLOR_TO_HEX

    def __init__(self, name: CssColorName):
        super().__init__()
        name = name.lower()  # type:ignore
        self.name = name
        self.validate()
        self.hex_value = HEX(self.COLORS[name])
        self._freeze()

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

    def to_str(self) -> builtins.str:
        return self.name

    def to_rgb(self) -> RGB:
        return self.hex_value.to_rgb()

    def to_hsv(self) -> HSV:
        return self.hex_value.to_hsv()

    def to_hsl(self) -> HSL:
        return self.hex_value.to_hsl()

    def to_cmyk(self) -> CMYK:
        return self.hex_value.to_cmyk()

    def to_hex(self) -> HEX:
        return self.hex_value

    def to_webcolor(self) -> webcolor:
        return self

    def to_assa(self) -> ASSA:
        return self.hex_value.to_assa()

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
        | CssColorName
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
            return ASSA.from_value(color)
        else:
            return webcolor(color)
    raise ColorValueError(f"Unsupported color format: {color}")


try:
    from pydantic import GetCoreSchemaHandler as _GetCoreSchemaHandler
    from pydantic import GetJsonSchemaHandler as _GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue as _JsonSchemaValue
    from pydantic_core import core_schema as _core_schema
except Exception:  # pragma: no cover
    pass  # Pydantic not installed
else:

    def parse_rgb(value: str | Mapping[str, T.Any]) -> RGB:
        if isinstance(value, Mapping):
            data = dict(value)
            if {"red", "green", "blue"}.issubset(data):
                return RGB(data["red"], data["green"], data["blue"])
            if {"r", "g", "b"}.issubset(data):
                return RGB(data["r"], data["g"], data["b"])
            raise ValueError(f"Invalid RGB mapping: {value!r}")

        match = re.fullmatch(
            r"\s*rgb\(\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*\)\s*", value
        )
        if not match:
            raise ValueError(f"Invalid RGB repr: {value!r}")

        r, g, b = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return RGB(r, g, b)

    def parse_rgba(value: str | Mapping[str, T.Any]) -> RGBA:
        if isinstance(value, Mapping):
            data = dict(value)
            if {"red", "green", "blue", "alpha"}.issubset(data):
                return RGBA(data["red"], data["green"], data["blue"], data["alpha"])
            if {"r", "g", "b", "a"}.issubset(data):
                return RGBA(data["r"], data["g"], data["b"], data["a"])
            raise ValueError(f"Invalid RGBA mapping: {value!r}")

        match = re.fullmatch(
            r"\s*rgba\(\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*\)\s*",
            value,
        )
        if not match:
            raise ValueError(f"Invalid RGBA repr: {value!r}")

        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        a = float(match.group(4))
        return RGBA(r, g, b, a)

    def parse_hex(value: str | Mapping[str, T.Any]) -> HEX:
        if isinstance(value, Mapping):
            data = dict(value)
            if "value" in data:
                return HEX(data["value"])
            if "hex" in data:
                return HEX(data["hex"])
            raise ValueError(f"Invalid HEX mapping: {value!r}")

        match = re.fullmatch(r"\s*hex\(\s*(#?[0-9A-Fa-f]{6})\s*\)\s*", value)
        if not match:
            raise ValueError(f"Invalid HEX repr: {value!r}")
        v = match.group(1)
        if not v.startswith("#"):
            v = f"#{v}"

        return HEX(v)

    def parse_hsv(value: str | Mapping[str, T.Any]) -> HSV:
        if isinstance(value, Mapping):
            data = dict(value)
            if {"hue", "saturation", "value"}.issubset(data):
                return HSV(data["hue"], data["saturation"], data["value"])
            if {"h", "s", "v"}.issubset(data):
                return HSV(data["h"], data["s"], data["v"])
            raise ValueError(f"Invalid HSV mapping: {value!r}")

        match = re.fullmatch(
            r"\s*hsv\(\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*\)\s*",
            value,
        )
        if not match:
            raise ValueError(f"Invalid HSV repr: {value!r}")

        h, s, v = float(match.group(1)), float(match.group(2)), float(match.group(3))
        return HSV(h, s, v)

    def parse_hsl(value: str | Mapping[str, T.Any]) -> HSL:
        if isinstance(value, Mapping):
            data = dict(value)
            if {"hue", "saturation", "lightness"}.issubset(data):
                return HSL(data["hue"], data["saturation"], data["lightness"])
            if {"h", "s", "l"}.issubset(data):
                return HSL(data["h"], data["s"], data["l"])
            raise ValueError(f"Invalid HSL mapping: {value!r}")

        match = re.fullmatch(
            r"\s*hsl\(\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*\)\s*",
            value,
        )
        if not match:
            raise ValueError(f"Invalid HSL repr: {value!r}")

        h, s, l = float(match.group(1)), float(match.group(2)), float(match.group(3))
        return HSL(h, s, l)

    def parse_cmyk(value: str | Mapping[str, T.Any]) -> CMYK:
        if isinstance(value, Mapping):
            data = dict(value)
            if {"cyan", "magenta", "yellow", "key"}.issubset(data):
                return CMYK(data["cyan"], data["magenta"], data["yellow"], data["key"])
            if {"c", "m", "y", "k"}.issubset(data):
                return CMYK(data["c"], data["m"], data["y"], data["k"])
            raise ValueError(f"Invalid CMYK mapping: {value!r}")

        match = re.fullmatch(
            r"\s*cmyk\(\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*\)\s*",
            value,
        )
        if not match:
            raise ValueError(f"Invalid CMYK repr: {value!r}")

        c, m, y, k = (
            float(match.group(1)),
            float(match.group(2)),
            float(match.group(3)),
            float(match.group(4)),
        )
        return CMYK(c, m, y, k)

    def parse_assa(value: str | Mapping[str, T.Any]) -> ASSA:
        if isinstance(value, Mapping):
            data = dict(value)
            if "value" in data:
                return ASSA(data["value"])
            if "clean_value" in data:
                return ASSA(data["clean_value"])
            raise ValueError(f"Invalid ASSA mapping: {value!r}")

        match = re.fullmatch(r"\s*assa\(\s*([0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\s*\)\s*", value)
        if not match:
            raise ValueError(f"Invalid ASSA repr: {value!r}")

        return ASSA(match.group(1))

    def parse_webcolor(value: str | Mapping[str, T.Any]) -> webcolor:
        if isinstance(value, Mapping):
            data = dict(value)
            if "name" in data:
                return webcolor(data["name"])
            raise ValueError(f"Invalid webcolor mapping: {value!r}")

        match = re.fullmatch(r"\s*webcolor\(\s*(['\"])\s*([A-Za-z]+)\s*\1\s*\)\s*", value)
        if not match:
            raise ValueError(f"Invalid webcolor repr: {value!r}")

        return webcolor(match.group(2))

    def _string_schema(
        *,
        title: str,
        description: str | None = None,
        pattern: str | None = None,
        examples: list[str] | None = None,
    ) -> _JsonSchemaValue:
        schema: dict[str, T.Any] = {"type": "string", "title": title}
        if description:
            schema["description"] = description
        if pattern:
            schema["pattern"] = pattern
        if examples:
            schema["examples"] = examples
        return schema

    def _object_schema(
        *,
        title: str,
        description: str | None,
        properties: dict[str, T.Any],
        required: list[str],
    ) -> _JsonSchemaValue:
        return {
            "type": "object",
            "title": title,
            "description": description,
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    def _register_color(
        cls: type[Color],
        parser: T.Callable[[str | Mapping[str, T.Any]], Color],
        *,
        title: str,
        string_description: str,
        string_pattern: str,
        string_examples: list[str],
        object_description: str,
        object_properties: dict[str, T.Any],
        object_required: list[str],
    ) -> None:
        string_schema = _string_schema(
            title=title,
            description=string_description,
            pattern=string_pattern,
            examples=string_examples,
        )
        object_schema = _object_schema(
            title=title,
            description=object_description,
            properties=object_properties,
            required=object_required,
        )

        def _validator(v: T.Any) -> Color:
            if isinstance(v, cls):
                return v
            if isinstance(v, str):
                return parser(v)
            if isinstance(v, Mapping):
                return parser(v)
            raise ValueError(
                f"Expected {cls.__name__} instance, repr string, or mapping, got {type(v).__name__}"
            )

        def _serializer(v: T.Any, info: _core_schema.SerializationInfo) -> T.Any:
            if info.mode == "json":
                return repr(v)
            return v

        core_schema = _core_schema.no_info_plain_validator_function(
            _validator,
            serialization=_core_schema.plain_serializer_function_ser_schema(
                _serializer, info_arg=True
            ),
        )

        def _core_schema_factory(
            _cls: type[Color], _source: T.Any, _handler: _GetCoreSchemaHandler
        ) -> _core_schema.CoreSchema:
            return core_schema

        def _json_schema_factory(
            _cls: type[Color],
            _core_schema_obj: _core_schema.CoreSchema,
            handler: _GetJsonSchemaHandler,
        ) -> _JsonSchemaValue:
            return {
                "title": title,
                "anyOf": [
                    handler.resolve_ref_schema(string_schema),
                    handler.resolve_ref_schema(object_schema),
                ],
            }

        cls.__get_pydantic_core_schema__ = classmethod(_core_schema_factory)  # type: ignore[attr-defined]
        cls.__get_pydantic_json_schema__ = classmethod(_json_schema_factory)  # type: ignore[attr-defined]

    _register_color(
        RGB,
        parse_rgb,
        title="RGB",
        string_description="String representation rgb(r, g, b) with 0-255 integer channels",
        string_pattern=r"^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$",
        string_examples=["rgb(255, 0, 0)", "rgb(0, 0, 0)"],
        object_description="Object with integer channels 0-255",
        object_properties={
            "red": {"type": "integer", "minimum": 0, "maximum": 255},
            "green": {"type": "integer", "minimum": 0, "maximum": 255},
            "blue": {"type": "integer", "minimum": 0, "maximum": 255},
        },
        object_required=["red", "green", "blue"],
    )

    _register_color(
        RGBA,
        parse_rgba,
        title="RGBA",
        string_description="String representation rgba(r, g, b, a) with 0-255 integer channels and alpha 0-1",
        string_pattern=r"^rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*(?:0|1|0?\.\d+)\s*\)$",
        string_examples=["rgba(255, 0, 0, 1)", "rgba(0, 128, 255, 0.5)"],
        object_description="Object with integer channels 0-255 and alpha 0-1",
        object_properties={
            "red": {"type": "integer", "minimum": 0, "maximum": 255},
            "green": {"type": "integer", "minimum": 0, "maximum": 255},
            "blue": {"type": "integer", "minimum": 0, "maximum": 255},
            "alpha": {"type": "number", "minimum": 0, "maximum": 1},
        },
        object_required=["red", "green", "blue", "alpha"],
    )

    _register_color(
        HEX,
        parse_hex,
        title="HEX",
        string_description="String representation hex(#RRGGBB)",
        string_pattern=r"^hex\(\s*#?[0-9A-Fa-f]{6}\s*\)$",
        string_examples=["hex(#ffffff)", "hex(#0a1b2c)"],
        object_description="Object with hex string value #RRGGBB",
        object_properties={
            "value": {
                "type": "string",
                "pattern": r"^#?[0-9A-Fa-f]{6}$",
                "examples": ["#ffffff", "0A1B2C"],
            }
        },
        object_required=["value"],
    )

    _register_color(
        HSV,
        parse_hsv,
        title="HSV",
        string_description="String representation hsv(h, s, v)",
        string_pattern=r"^hsv\(\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*,\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*,\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*\)$",
        string_examples=["hsv(120.0, 100.0, 100.0)"],
        object_description="Object with hue 0-360, saturation/value 0-100",
        object_properties={
            "hue": {"type": "number", "minimum": 0, "maximum": 360},
            "saturation": {"type": "number", "minimum": 0, "maximum": 100},
            "value": {"type": "number", "minimum": 0, "maximum": 100},
        },
        object_required=["hue", "saturation", "value"],
    )

    _register_color(
        HSL,
        parse_hsl,
        title="HSL",
        string_description="String representation hsl(h, s, l)",
        string_pattern=r"^hsl\(\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*,\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*,\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*\)$",
        string_examples=["hsl(240.0, 100.0, 50.0)"],
        object_description="Object with hue 0-360, saturation/lightness 0-100",
        object_properties={
            "hue": {"type": "number", "minimum": 0, "maximum": 360},
            "saturation": {"type": "number", "minimum": 0, "maximum": 100},
            "lightness": {"type": "number", "minimum": 0, "maximum": 100},
        },
        object_required=["hue", "saturation", "lightness"],
    )

    _register_color(
        CMYK,
        parse_cmyk,
        title="CMYK",
        string_description="String representation cmyk(c, m, y, k)",
        string_pattern=r"^cmyk\(\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*,\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*,\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*,\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)\s*\)$",
        string_examples=["cmyk(0, 100, 100, 0)", "cmyk(10.5, 0, 25, 5)"],
        object_description="Object with CMYK percentages 0-100",
        object_properties={
            "cyan": {"type": "number", "minimum": 0, "maximum": 100},
            "magenta": {"type": "number", "minimum": 0, "maximum": 100},
            "yellow": {"type": "number", "minimum": 0, "maximum": 100},
            "key": {"type": "number", "minimum": 0, "maximum": 100},
        },
        object_required=["cyan", "magenta", "yellow", "key"],
    )

    _register_color(
        ASSA,
        parse_assa,
        title="ASSA",
        string_description="String representation assa(BBGGRR) or assa(AABBGGRR)",
        string_pattern=r"^assa\(\s*[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?\s*\)$",
        string_examples=["assa(00ff00)", "assa(ff00ff00)"],
        object_description="Object with ASSA hex value (BBGGRR or AABBGGRR)",
        object_properties={
            "value": {
                "type": "string",
                "pattern": r"^[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$",
                "examples": ["00ff00", "ff00ff00"],
            }
        },
        object_required=["value"],
    )

    _register_color(
        webcolor,
        parse_webcolor,
        title="Web Color",
        string_description="Named CSS color via webcolor('name')",
        string_pattern=r"^webcolor\(\s*['\"]?[A-Za-z]+['\"]?\s*\)$",
        string_examples=["webcolor('red')", 'webcolor("aliceblue")'],
        object_description="Object with CSS color name",
        object_properties={
            "name": {"type": "string", "enum": list(CSS_COLOR_TO_HEX.keys())},
        },
        object_required=["name"],
    )
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
    "CssColorName",
    "ColorValueError",
    "normalize_color",
]
