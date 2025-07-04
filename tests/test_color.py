import pytest

from stdl.color import (
    ASSA,
    CMYK,
    HEX,
    HSL,
    HSV,
    RGB,
    RGBA,
    ColorValueError,
    normalize_color,
    webcolor,
)


class TestRGB:
    def test_rgb_creation(self):
        rgb = RGB(255, 128, 64)
        assert rgb.r == 255
        assert rgb.g == 128
        assert rgb.b == 64

    def test_rgb_validation_valid(self):
        RGB(0, 0, 0)
        RGB(255, 255, 255)
        RGB(128, 64, 32)

    def test_rgb_validation_invalid(self):
        with pytest.raises(ColorValueError):
            RGB(-1, 0, 0)
        with pytest.raises(ColorValueError):
            RGB(256, 0, 0)
        with pytest.raises(ColorValueError):
            RGB(0, -1, 0)
        with pytest.raises(ColorValueError):
            RGB(0, 256, 0)
        with pytest.raises(ColorValueError):
            RGB(0, 0, -1)
        with pytest.raises(ColorValueError):
            RGB(0, 0, 256)

    def test_rgb_repr(self):
        rgb = RGB(255, 128, 64)
        assert repr(rgb) == "rgb(255, 128, 64)"

    def test_rgb_equality(self):
        rgb1 = RGB(255, 128, 64)
        rgb2 = RGB(255, 128, 64)
        rgb3 = RGB(255, 128, 65)
        assert rgb1 == rgb2
        assert rgb1 != rgb3

    def test_rgb_tuple(self):
        rgb = RGB(255, 128, 64)
        assert rgb.tuple() == (255, 128, 64)

    def test_rgb_to_rgb(self):
        rgb = RGB(255, 128, 64)
        assert rgb.RGB() == rgb
        assert rgb.RGB() is not rgb

    def test_rgb_to_hsv(self):
        rgb = RGB(255, 0, 0)
        hsv = rgb.HSV()
        assert hsv.h == 0
        assert hsv.s == 100
        assert hsv.v == 100

    def test_rgb_to_hsl(self):
        rgb = RGB(255, 0, 0)
        hsl = rgb.HSL()
        assert hsl.h == 0
        assert hsl.s == 100
        assert hsl.l == 50

    def test_rgb_to_cmyk(self):
        rgb = RGB(255, 0, 0)
        cmyk = rgb.CMYK()
        assert cmyk.c == 0
        assert cmyk.m == 100
        assert cmyk.y == 100
        assert cmyk.k == 0

    def test_rgb_to_hex(self):
        rgb = RGB(255, 128, 64)
        hex_color = rgb.HEX()
        assert hex_color.value == "#ff8040"

    def test_rgb_to_rgba(self):
        rgb = RGB(255, 128, 64)
        rgba = rgb.RGBA(0.5)
        assert rgba.r == 255
        assert rgba.g == 128
        assert rgba.b == 64
        assert rgba.a == 0.5

    def test_rgb_to_assa(self):
        rgb = RGB(255, 128, 64)
        assa = rgb.ASSA()
        assert assa.clean_value == "4080ff"


class TestRGBA:
    def test_rgba_creation(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assert rgba.r == 255
        assert rgba.g == 128
        assert rgba.b == 64
        assert rgba.a == 0.5

    def test_rgba_default_alpha(self):
        rgba = RGBA(255, 128, 64)
        assert rgba.a == 1.0

    def test_rgba_validation_valid(self):
        RGBA(0, 0, 0, 0)
        RGBA(255, 255, 255, 1)
        RGBA(128, 64, 32, 0.5)

    def test_rgba_validation_invalid(self):
        with pytest.raises(ColorValueError):
            RGBA(-1, 0, 0, 0.5)
        with pytest.raises(ColorValueError):
            RGBA(256, 0, 0, 0.5)
        with pytest.raises(ColorValueError):
            RGBA(128, 128, 128, -0.1)
        with pytest.raises(ColorValueError):
            RGBA(128, 128, 128, 1.1)

    def test_rgba_repr(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assert repr(rgba) == "rgba(255, 128, 64, 0.5)"

    def test_rgba_equality(self):
        rgba1 = RGBA(255, 128, 64, 0.5)
        rgba2 = RGBA(255, 128, 64, 0.5)
        rgba3 = RGBA(255, 128, 64, 0.6)
        assert rgba1 == rgba2
        assert rgba1 != rgba3

    def test_rgba_to_rgb(self):
        rgba = RGBA(255, 128, 64, 0.5)
        rgb = rgba.RGB()
        assert rgb.r == 255
        assert rgb.g == 128
        assert rgb.b == 64

    def test_rgba_to_assa(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assa = rgba.ASSA()
        assert assa.alpha == 128


class TestHEX:
    def test_hex_creation(self):
        hex_color = HEX("#ff8040")
        assert hex_color.value == "#ff8040"

    def test_hex_creation_without_hash(self):
        hex_color = HEX("ff8040")
        assert hex_color.value == "#ff8040"

    def test_hex_creation_uppercase(self):
        hex_color = HEX("#FF8040")
        assert hex_color.value == "#ff8040"

    def test_hex_validation_valid(self):
        HEX("#000000")
        HEX("#ffffff")
        HEX("#123abc")
        HEX("123ABC")

    def test_hex_validation_invalid(self):
        with pytest.raises(ColorValueError):
            HEX("#12345")
        with pytest.raises(ColorValueError):
            HEX("#1234567")
        with pytest.raises(ColorValueError):
            HEX("#gggggg")
        with pytest.raises(ColorValueError):
            HEX("invalid")

    def test_hex_repr(self):
        hex_color = HEX("#ff8040")
        assert repr(hex_color) == "hex('#ff8040')"

    def test_hex_str(self):
        hex_color = HEX("#ff8040")
        assert hex_color.str() == "#ff8040"

    def test_hex_equality(self):
        hex1 = HEX("#ff8040")
        hex2 = HEX("#FF8040")
        hex3 = HEX("#ff8041")
        assert hex1 == hex2
        assert hex1 != hex3

    def test_hex_to_rgb(self):
        hex_color = HEX("#ff8040")
        rgb = hex_color.RGB()
        assert rgb.r == 255
        assert rgb.g == 128
        assert rgb.b == 64


class TestHSV:
    def test_hsv_creation(self):
        hsv = HSV(120, 50, 75)
        assert hsv.h == 120
        assert hsv.s == 50
        assert hsv.v == 75

    def test_hsv_validation_valid(self):
        HSV(0, 0, 0)
        HSV(360, 100, 100)
        HSV(180, 50, 75)

    def test_hsv_validation_invalid(self):
        with pytest.raises(ColorValueError):
            HSV(-1, 50, 75)
        with pytest.raises(ColorValueError):
            HSV(361, 50, 75)
        with pytest.raises(ColorValueError):
            HSV(180, -1, 75)
        with pytest.raises(ColorValueError):
            HSV(180, 101, 75)
        with pytest.raises(ColorValueError):
            HSV(180, 50, -1)
        with pytest.raises(ColorValueError):
            HSV(180, 50, 101)

    def test_hsv_repr(self):
        hsv = HSV(120, 50, 75)
        assert repr(hsv) == "hsv(120.0, 50.0, 75.0)"

    def test_hsv_str(self):
        hsv = HSV(120, 50, 75)
        assert hsv.str() == "hsv(120.0°, 50.0%, 75.0%)"

    def test_hsv_equality(self):
        hsv1 = HSV(120, 50, 75)
        hsv2 = HSV(120, 50, 75)
        hsv3 = HSV(120, 50, 76)
        assert hsv1 == hsv2
        assert hsv1 != hsv3

    def test_hsv_to_rgb(self):
        hsv = HSV(0, 100, 100)
        rgb = hsv.RGB()
        assert rgb.r == 255
        assert rgb.g == 0
        assert rgb.b == 0

    def test_hsv_to_rgb_green(self):
        hsv = HSV(120, 100, 100)
        rgb = hsv.RGB()
        assert rgb.r == 0
        assert rgb.g == 255
        assert rgb.b == 0

    def test_hsv_to_rgb_blue(self):
        hsv = HSV(240, 100, 100)
        rgb = hsv.RGB()
        assert rgb.r == 0
        assert rgb.g == 0
        assert rgb.b == 255


class TestHSL:
    def test_hsl_creation(self):
        hsl = HSL(120, 50, 75)
        assert hsl.h == 120
        assert hsl.s == 50
        assert hsl.l == 75

    def test_hsl_validation_valid(self):
        HSL(0, 0, 0)
        HSL(360, 100, 100)
        HSL(180, 50, 75)

    def test_hsl_validation_invalid(self):
        with pytest.raises(ColorValueError):
            HSL(-1, 50, 75)
        with pytest.raises(ColorValueError):
            HSL(361, 50, 75)
        with pytest.raises(ColorValueError):
            HSL(180, -1, 75)
        with pytest.raises(ColorValueError):
            HSL(180, 101, 75)
        with pytest.raises(ColorValueError):
            HSL(180, 50, -1)
        with pytest.raises(ColorValueError):
            HSL(180, 50, 101)

    def test_hsl_repr(self):
        hsl = HSL(120, 50, 75)
        assert repr(hsl) == "hsl(120.0, 50.0, 75.0)"

    def test_hsl_str(self):
        hsl = HSL(120, 50, 75)
        assert hsl.str() == "hsl(120.0°, 50.0%, 75.0%)"

    def test_hsl_equality(self):
        hsl1 = HSL(120, 50, 75)
        hsl2 = HSL(120, 50, 75)
        hsl3 = HSL(120, 50, 76)
        assert hsl1 == hsl2
        assert hsl1 != hsl3

    def test_hsl_to_rgb(self):
        hsl = HSL(0, 100, 50)
        rgb = hsl.RGB()
        assert rgb.r == 255
        assert rgb.g == 0
        assert rgb.b == 0

    def test_hsl_to_rgb_gray(self):
        hsl = HSL(0, 0, 50)
        rgb = hsl.RGB()
        assert rgb.r == 128
        assert rgb.g == 128
        assert rgb.b == 128


class TestCMYK:
    def test_cmyk_creation(self):
        cmyk = CMYK(25, 50, 75, 10)
        assert cmyk.c == 25
        assert cmyk.m == 50
        assert cmyk.y == 75
        assert cmyk.k == 10

    def test_cmyk_validation_valid(self):
        CMYK(0, 0, 0, 0)
        CMYK(100, 100, 100, 100)
        CMYK(25, 50, 75, 10)

    def test_cmyk_validation_invalid(self):
        with pytest.raises(ColorValueError):
            CMYK(-1, 50, 75, 10)
        with pytest.raises(ColorValueError):
            CMYK(101, 50, 75, 10)
        with pytest.raises(ColorValueError):
            CMYK(25, -1, 75, 10)
        with pytest.raises(ColorValueError):
            CMYK(25, 101, 75, 10)
        with pytest.raises(ColorValueError):
            CMYK(25, 50, -1, 10)
        with pytest.raises(ColorValueError):
            CMYK(25, 50, 101, 10)
        with pytest.raises(ColorValueError):
            CMYK(25, 50, 75, -1)
        with pytest.raises(ColorValueError):
            CMYK(25, 50, 75, 101)

    def test_cmyk_repr(self):
        cmyk = CMYK(25, 50, 75, 10)
        assert repr(cmyk) == "cmyk(25.0, 50.0, 75.0, 10.0)"

    def test_cmyk_str(self):
        cmyk = CMYK(25, 50, 75, 10)
        assert cmyk.str() == "cmyk(25.0%, 50.0%, 75.0%, 10.0%)"

    def test_cmyk_equality(self):
        cmyk1 = CMYK(25, 50, 75, 10)
        cmyk2 = CMYK(25, 50, 75, 10)
        cmyk3 = CMYK(25, 50, 75, 11)
        assert cmyk1 == cmyk2
        assert cmyk1 != cmyk3

    def test_cmyk_to_rgb(self):
        cmyk = CMYK(0, 100, 100, 0)
        rgb = cmyk.RGB()
        assert rgb.r == 255
        assert rgb.g == 0
        assert rgb.b == 0

    def test_cmyk_to_rgb_black(self):
        cmyk = CMYK(0, 0, 0, 100)
        rgb = cmyk.RGB()
        assert rgb.r == 0
        assert rgb.g == 0
        assert rgb.b == 0


class TestASSA:
    def test_assa_creation_bbggrr(self):
        assa = ASSA("4080ff")
        assert assa.clean_value == "4080ff"
        assert assa.value == "&H4080ff&"

    def test_assa_creation_aabbggrr(self):
        assa = ASSA("804080ff")
        assert assa.clean_value == "804080ff"
        assert assa.value == "&H804080ff&"

    def test_assa_creation_with_prefix(self):
        assa = ASSA("&H4080ff&")
        assert assa.clean_value == "4080ff"

    def test_assa_validation_valid(self):
        ASSA("000000")
        ASSA("ffffff")
        ASSA("4080ff")
        ASSA("804080ff")

    def test_assa_validation_invalid(self):
        with pytest.raises(ColorValueError):
            ASSA("12345")
        with pytest.raises(ColorValueError):
            ASSA("1234567")
        with pytest.raises(ColorValueError):
            ASSA("123456789")
        with pytest.raises(ColorValueError):
            ASSA("gggggg")

    def test_assa_repr(self):
        assa = ASSA("4080ff")
        assert repr(assa) == "assa('4080ff')"

    def test_assa_str(self):
        assa = ASSA("4080ff")
        assert assa.str() == "&H4080ff&"

    def test_assa_equality(self):
        assa1 = ASSA("4080ff")
        assa2 = ASSA("4080FF")
        assa3 = ASSA("4080fe")
        assert assa1 == assa2
        assert assa1 != assa3

    def test_assa_alpha_property(self):
        assa_no_alpha = ASSA("4080ff")
        assa_with_alpha = ASSA("804080ff")
        assert assa_no_alpha.alpha is None
        assert assa_with_alpha.alpha == 128

    def test_assa_format_detection(self):
        assa_bbggrr = ASSA("4080ff")
        assa_aabbggrr = ASSA("804080ff")
        assert assa_bbggrr.is_BBGGRR_format()
        assert not assa_bbggrr.is_AABBGGRR_format()
        assert not assa_aabbggrr.is_BBGGRR_format()
        assert assa_aabbggrr.is_AABBGGRR_format()

    def test_assa_to_rgb(self):
        assa = ASSA("4080ff")
        rgb = assa.RGB()
        assert rgb.r == 255
        assert rgb.g == 128
        assert rgb.b == 64

    def test_assa_embed_text(self):
        assa = ASSA("4080ff")
        embedded = assa.embed_text("Hello")
        assert embedded == "{\\c&H4080ff&}Hello{\\c}"

    def test_assa_is_valid_format(self):
        assert ASSA.is_valid_format("4080ff")
        assert ASSA.is_valid_format("804080ff")
        assert not ASSA.is_valid_format("12345")
        assert not ASSA.is_valid_format("gggggg")

    def test_assa_from_alpha(self):
        assa = ASSA.from_alpha(128)
        assert assa.clean_value == "80000000"
        assert assa.alpha == 128

    def test_assa_from_rgb(self):
        rgb = RGB(255, 128, 64)
        assa = ASSA.from_RGB(rgb)
        assert assa.clean_value == "4080ff"

    def test_assa_from_rgb_with_alpha(self):
        rgb = RGB(255, 128, 64)
        assa = ASSA.from_RGB(rgb, alpha=128)
        assert assa.clean_value == "804080ff"

    def test_assa_from_rgba(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assa = ASSA.from_RGBA(rgba)
        assert assa.clean_value == "804080ff"


class TestWebcolor:
    def test_webcolor_creation(self):
        wc = webcolor("red")
        assert wc.name == "red"

    def test_webcolor_case_insensitive(self):
        wc = webcolor("RED")
        assert wc.name == "red"

    def test_webcolor_validation_valid(self):
        webcolor("red")
        webcolor("blue")
        webcolor("green")

    def test_webcolor_validation_invalid(self):
        with pytest.raises(ColorValueError):
            webcolor("notacolor")

    def test_webcolor_repr(self):
        wc = webcolor("red")
        assert repr(wc) == "webcolor('red')"

    def test_webcolor_str(self):
        wc = webcolor("red")
        assert wc.str() == "red"

    def test_webcolor_equality(self):
        wc1 = webcolor("red")
        wc2 = webcolor("RED")
        wc3 = webcolor("blue")
        assert wc1 == wc2
        assert wc1 != wc3

    def test_webcolor_to_rgb(self):
        wc = webcolor("red")
        rgb = wc.RGB()
        assert rgb.r == 255
        assert rgb.g == 0
        assert rgb.b == 0

    def test_webcolor_from_hex(self):
        wc = webcolor.from_hex("#ff0000")
        assert wc.name == "red"

    def test_webcolor_from_hex_invalid(self):
        with pytest.raises(ColorValueError):
            webcolor.from_hex("#123456")


class TestNormalizeColor:
    def test_normalize_rgb_tuple(self):
        color = normalize_color((255, 128, 64))
        assert isinstance(color, RGB)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 64

    def test_normalize_rgba_tuple(self):
        color = normalize_color((255, 128, 64, 0.5))
        assert isinstance(color, RGBA)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 64
        assert color.a == 0.5

    def test_normalize_hex_string(self):
        color = normalize_color("#ff8040")
        assert isinstance(color, HEX)
        assert color.value == "#ff8040"

    def test_normalize_assa_string(self):
        color = normalize_color("&H4080ff&")
        assert isinstance(color, ASSA)
        assert color.clean_value == "4080ff"

    def test_normalize_webcolor_string(self):
        color = normalize_color("red")
        assert isinstance(color, webcolor)
        assert color.name == "red"

    def test_normalize_invalid_sequence_length(self):
        with pytest.raises(ColorValueError):
            normalize_color((255, 128))
        with pytest.raises(ColorValueError):
            normalize_color((255, 128, 64, 0.5, 100))

    def test_normalize_invalid_type(self):
        with pytest.raises(ColorValueError):
            normalize_color(123)


class TestColorConversions:
    def test_rgb_hsv_roundtrip(self):
        rgb = RGB(255, 128, 64)
        hsv = rgb.HSV()
        rgb2 = hsv.RGB()
        assert abs(rgb.r - rgb2.r) <= 1
        assert abs(rgb.g - rgb2.g) <= 1
        assert abs(rgb.b - rgb2.b) <= 1

    def test_rgb_hsl_roundtrip(self):
        rgb = RGB(255, 128, 64)
        hsl = rgb.HSL()
        rgb2 = hsl.RGB()
        assert abs(rgb.r - rgb2.r) <= 1
        assert abs(rgb.g - rgb2.g) <= 1
        assert abs(rgb.b - rgb2.b) <= 1

    def test_rgb_cmyk_roundtrip(self):
        rgb = RGB(255, 128, 64)
        cmyk = rgb.CMYK()
        rgb2 = cmyk.RGB()
        assert abs(rgb.r - rgb2.r) <= 1
        assert abs(rgb.g - rgb2.g) <= 1
        assert abs(rgb.b - rgb2.b) <= 1

    def test_rgb_hex_roundtrip(self):
        rgb = RGB(255, 128, 64)
        hex_color = rgb.HEX()
        rgb2 = hex_color.RGB()
        assert rgb == rgb2

    def test_rgb_assa_roundtrip(self):
        rgb = RGB(255, 128, 64)
        assa = rgb.ASSA()
        rgb2 = assa.RGB()
        assert rgb == rgb2

    def test_rgba_assa_roundtrip(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assa = rgba.ASSA()
        rgba2 = RGBA.from_assa(assa)
        assert abs(rgba.a - rgba2.a) < 0.01


class TestColorDict:
    def test_rgb_dict(self):
        rgb = RGB(255, 128, 64)
        d = rgb.dict()
        assert d == {"r": 255, "g": 128, "b": 64}

    def test_rgba_dict(self):
        rgba = RGBA(255, 128, 64, 0.5)
        d = rgba.dict()
        assert d == {"r": 255, "g": 128, "b": 64, "a": 0.5}

    def test_hsv_dict(self):
        hsv = HSV(120, 50, 75)
        d = hsv.dict()
        assert d == {"h": 120.0, "s": 50.0, "v": 75.0}

    def test_hsl_dict(self):
        hsl = HSL(120, 50, 75)
        d = hsl.dict()
        assert d == {"h": 120.0, "s": 50.0, "l": 75.0}

    def test_cmyk_dict(self):
        cmyk = CMYK(25, 50, 75, 10)
        d = cmyk.dict()
        assert d == {"c": 25.0, "m": 50.0, "y": 75.0, "k": 10.0}


class TestColorCopy:
    def test_rgb_copy(self):
        rgb = RGB(255, 128, 64)
        rgb_copy = rgb.copy()
        assert rgb == rgb_copy
        assert rgb is not rgb_copy

    def test_rgba_copy(self):
        rgba = RGBA(255, 128, 64, 0.5)
        rgba_copy = rgba.copy()
        assert rgba == rgba_copy
        assert rgba is not rgba_copy
