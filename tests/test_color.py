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
        assert rgb.red == 255
        assert rgb.green == 128
        assert rgb.blue == 64

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
        assert rgb.to_rgb() == rgb
        assert rgb.to_rgb() is rgb

    def test_rgb_to_hsv(self):
        rgb = RGB(255, 0, 0)
        hsv = rgb.to_hsv()
        assert hsv.hue == 0
        assert hsv.saturation == 100
        assert hsv.value == 100

    def test_rgb_to_hsl(self):
        rgb = RGB(255, 0, 0)
        hsl = rgb.to_hsl()
        assert hsl.hue == 0
        assert hsl.saturation == 100
        assert hsl.lightness == 50

    def test_rgb_to_cmyk(self):
        rgb = RGB(255, 0, 0)
        cmyk = rgb.to_cmyk()
        assert cmyk.cyan == 0
        assert cmyk.magenta == 100
        assert cmyk.yellow == 100
        assert cmyk.key == 0

    def test_rgb_to_hex(self):
        rgb = RGB(255, 128, 64)
        hex_color = rgb.to_hex()
        assert hex_color.value == "#ff8040"

    def test_rgb_to_rgba(self):
        rgb = RGB(255, 128, 64)
        rgba = rgb.to_rgba(0.5)
        assert rgba.red == 255
        assert rgba.green == 128
        assert rgba.blue == 64
        assert rgba.alpha == 0.5

    def test_rgb_to_assa(self):
        rgb = RGB(255, 128, 64)
        assa = rgb.to_assa()
        assert assa.clean_value == "4080ff"


class TestRGBA:
    def test_rgba_creation(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assert rgba.red == 255
        assert rgba.green == 128
        assert rgba.blue == 64
        assert rgba.alpha == 0.5

    def test_rgba_default_alpha(self):
        rgba = RGBA(255, 128, 64)
        assert rgba.alpha == 1.0

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
        rgb = rgba.to_rgb()
        assert rgb.red == 255
        assert rgb.green == 128
        assert rgb.blue == 64

    def test_rgba_to_assa(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assa = rgba.to_assa()
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
        assert repr(hex_color) == "hex(#ff8040)"

    def test_hex_str(self):
        hex_color = HEX("#ff8040")
        assert hex_color.to_str() == "#ff8040"

    def test_hex_equality(self):
        hex1 = HEX("#ff8040")
        hex2 = HEX("#FF8040")
        hex3 = HEX("#ff8041")
        assert hex1 == hex2
        assert hex1 != hex3

    def test_hex_to_rgb(self):
        hex_color = HEX("#ff8040")
        rgb = hex_color.to_rgb()
        assert rgb.red == 255
        assert rgb.green == 128
        assert rgb.blue == 64


class TestHSV:
    def test_hsv_creation(self):
        hsv = HSV(120, 50, 75)
        assert hsv.hue == 120
        assert hsv.saturation == 50
        assert hsv.value == 75

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
        assert hsv.to_str() == "hsv(120.0°, 50.0%, 75.0%)"

    def test_hsv_equality(self):
        hsv1 = HSV(120, 50, 75)
        hsv2 = HSV(120, 50, 75)
        hsv3 = HSV(120, 50, 76)
        assert hsv1 == hsv2
        assert hsv1 != hsv3

    def test_hsv_to_rgb(self):
        hsv = HSV(0, 100, 100)
        rgb = hsv.to_rgb()
        assert rgb.red == 255
        assert rgb.green == 0
        assert rgb.blue == 0

    def test_hsv_to_rgb_green(self):
        hsv = HSV(120, 100, 100)
        rgb = hsv.to_rgb()
        assert rgb.red == 0
        assert rgb.green == 255
        assert rgb.blue == 0

    def test_hsv_to_rgb_blue(self):
        hsv = HSV(240, 100, 100)
        rgb = hsv.to_rgb()
        assert rgb.red == 0
        assert rgb.green == 0
        assert rgb.blue == 255


class TestHSL:
    def test_hsl_creation(self):
        hsl = HSL(120, 50, 75)
        assert hsl.hue == 120
        assert hsl.saturation == 50
        assert hsl.lightness == 75

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
        assert hsl.to_str() == "hsl(120.0°, 50.0%, 75.0%)"

    def test_hsl_equality(self):
        hsl1 = HSL(120, 50, 75)
        hsl2 = HSL(120, 50, 75)
        hsl3 = HSL(120, 50, 76)
        assert hsl1 == hsl2
        assert hsl1 != hsl3

    def test_hsl_to_rgb(self):
        hsl = HSL(0, 100, 50)
        rgb = hsl.to_rgb()
        assert rgb.red == 255
        assert rgb.green == 0
        assert rgb.blue == 0

    def test_hsl_to_rgb_gray(self):
        hsl = HSL(0, 0, 50)
        rgb = hsl.to_rgb()
        assert rgb.red == 128
        assert rgb.green == 128
        assert rgb.blue == 128


class TestCMYK:
    def test_cmyk_creation(self):
        cmyk = CMYK(25, 50, 75, 10)
        assert cmyk.cyan == 25
        assert cmyk.magenta == 50
        assert cmyk.yellow == 75
        assert cmyk.key == 10

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
        assert cmyk.to_str() == "cmyk(25.0%, 50.0%, 75.0%, 10.0%)"

    def test_cmyk_equality(self):
        cmyk1 = CMYK(25, 50, 75, 10)
        cmyk2 = CMYK(25, 50, 75, 10)
        cmyk3 = CMYK(25, 50, 75, 11)
        assert cmyk1 == cmyk2
        assert cmyk1 != cmyk3

    def test_cmyk_to_rgb(self):
        cmyk = CMYK(0, 100, 100, 0)
        rgb = cmyk.to_rgb()
        assert rgb.red == 255
        assert rgb.green == 0
        assert rgb.blue == 0

    def test_cmyk_to_rgb_black(self):
        cmyk = CMYK(0, 0, 0, 100)
        rgb = cmyk.to_rgb()
        assert rgb.red == 0
        assert rgb.green == 0
        assert rgb.blue == 0


class TestASSA:
    def test_assa_repr(self):
        assa = ASSA("4080FF")
        assert repr(assa) == "assa(4080ff)"
        assa_alpha = ASSA("804080FF")
        assert repr(assa_alpha) == "assa(804080ff)"

    def test_assa_str(self):
        assa = ASSA("4080FF")
        assert assa.to_str() == "&H4080ff&"

    def test_assa_equality(self):
        assa1 = ASSA("4080FF")
        assa2 = ASSA("4080FF")
        assa3 = ASSA("4080FE")
        assert assa1 == assa2
        assert assa1 != assa3

    def test_assa_from_clean_value_validates_input(self):
        assa = ASSA.from_clean_value("80402010")
        assert assa.clean_value == "80402010"
        with pytest.raises(ColorValueError):
            ASSA.from_clean_value("12345")

    def test_assa_format_detection(self):
        assa_bbggrr = ASSA("4080FF")
        assa_aabbggrr = ASSA("804080FF")
        assert assa_bbggrr.is_BBGGRR_format()
        assert not assa_bbggrr.is_AABBGGRR_format()
        assert not assa_aabbggrr.is_BBGGRR_format()
        assert assa_aabbggrr.is_AABBGGRR_format()

    def test_assa_to_rgb(self):
        assa = ASSA("4080FF")
        rgb = assa.to_rgb()
        assert rgb.red == 255
        assert rgb.green == 128
        assert rgb.blue == 64

    def test_assa_embed_text(self):
        assa = ASSA("4080FF")
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
        assa = ASSA.from_rgb(rgb)
        assert assa.clean_value == "4080ff"

    def test_assa_from_rgb_with_alpha(self):
        rgb = RGB(255, 128, 64)
        assa = ASSA.from_rgb(rgb, alpha=128)
        assert assa.clean_value == "804080ff"

    def test_assa_from_rgba(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assa = ASSA.from_rgba(rgba)
        assert assa.clean_value == "804080ff"

    def test_assa_new_constructor_bbggrr(self):
        """Test new single-value constructor with BBGGRR format"""
        assa = ASSA("4080FF")
        assert assa.clean_value == "4080ff"
        assert assa.value == "&H4080ff&"
        assert assa.blue == 64
        assert assa.green == 128
        assert assa.red == 255
        assert assa.alpha is None
        assert assa.is_BBGGRR_format()
        assert not assa.is_AABBGGRR_format()

    def test_assa_new_constructor_aabbggrr(self):
        """Test new single-value constructor with AABBGGRR format"""
        assa = ASSA("804080FF")
        assert assa.clean_value == "804080ff"
        assert assa.value == "&H804080ff&"
        assert assa.blue == 64
        assert assa.green == 128
        assert assa.red == 255
        assert assa.alpha == 128
        assert not assa.is_BBGGRR_format()
        assert assa.is_AABBGGRR_format()

    def test_assa_integer_properties(self):
        """Test that blue, green, red, alpha properties return correct integers"""
        # Test BBGGRR format
        assa1 = ASSA("102030")
        assert assa1.blue == 16
        assert assa1.green == 32
        assert assa1.red == 48
        assert assa1.alpha is None

        # Test AABBGGRR format
        assa2 = ASSA("FF102030")
        assert assa2.blue == 16
        assert assa2.green == 32
        assert assa2.red == 48
        assert assa2.alpha == 255

    def test_assa_validation_invalid_strings(self):
        """Test validation of invalid hex strings in new constructor"""
        # Test invalid characters
        with pytest.raises(ColorValueError):
            ASSA.from_clean_value("GGHHII")
        with pytest.raises(ColorValueError):
            ASSA("GGHHII")

        # Test wrong lengths
        with pytest.raises(ColorValueError):
            ASSA.from_clean_value("12345")  # Too short
        with pytest.raises(ColorValueError):
            ASSA.from_clean_value("1234567")  # Wrong length

    def test_assa_clean_value_property(self):
        """Test clean_value property functionality"""
        # Test with uppercase
        assa1 = ASSA("4080FF")
        assert assa1.clean_value == "4080ff"

        # Test with mixed case
        assa2 = ASSA("40a0Bf")
        assert assa2.clean_value == "40a0bf"

        # Test from formatted value
        assa3 = ASSA.from_value("&H4080FF&")
        assert assa3.clean_value == "4080ff"


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
        assert wc.to_str() == "red"

    def test_webcolor_equality(self):
        wc1 = webcolor("red")
        wc2 = webcolor("RED")
        wc3 = webcolor("blue")
        assert wc1 == wc2
        assert wc1 != wc3

    def test_webcolor_to_rgb(self):
        wc = webcolor("red")
        rgb = wc.to_rgb()
        assert rgb.red == 255
        assert rgb.green == 0
        assert rgb.blue == 0

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
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 64

    def test_normalize_rgba_tuple(self):
        color = normalize_color((255, 128, 64, 0.5))
        assert isinstance(color, RGBA)
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 64
        assert color.alpha == 0.5

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
        hsv = rgb.to_hsv()
        rgb2 = hsv.to_rgb()
        assert abs(rgb.red - rgb2.red) <= 1
        assert abs(rgb.green - rgb2.green) <= 1
        assert abs(rgb.blue - rgb2.blue) <= 1

    def test_rgb_hsl_roundtrip(self):
        rgb = RGB(255, 128, 64)
        hsl = rgb.to_hsl()
        rgb2 = hsl.to_rgb()
        assert abs(rgb.red - rgb2.red) <= 1
        assert abs(rgb.green - rgb2.green) <= 1
        assert abs(rgb.blue - rgb2.blue) <= 1

    def test_rgb_cmyk_roundtrip(self):
        rgb = RGB(255, 128, 64)
        cmyk = rgb.to_cmyk()
        rgb2 = cmyk.to_rgb()
        assert abs(rgb.red - rgb2.red) <= 1
        assert abs(rgb.green - rgb2.green) <= 1
        assert abs(rgb.blue - rgb2.blue) <= 1

    def test_rgb_hex_roundtrip(self):
        rgb = RGB(255, 128, 64)
        hex_color = rgb.to_hex()
        rgb2 = hex_color.to_rgb()
        assert rgb == rgb2

    def test_rgb_assa_roundtrip(self):
        rgb = RGB(255, 128, 64)
        assa = rgb.to_assa()
        rgb2 = assa.to_rgb()
        assert rgb == rgb2

    def test_rgba_assa_roundtrip(self):
        rgba = RGBA(255, 128, 64, 0.5)
        assa = rgba.to_assa()
        rgba2 = RGBA.from_assa(assa)
        assert abs(rgba.alpha - rgba2.alpha) < 0.01


class TestColorDict:
    def test_rgb_dict(self):
        rgb = RGB(255, 128, 64)
        d = rgb.dict()
        assert d == {"red": 255, "green": 128, "blue": 64}

    def test_rgba_dict(self):
        rgba = RGBA(255, 128, 64, 0.5)
        d = rgba.dict()
        assert d == {"red": 255, "green": 128, "blue": 64, "alpha": 0.5}

    def test_hsv_dict(self):
        hsv = HSV(120, 50, 75)
        d = hsv.dict()
        assert d == {"hue": 120.0, "saturation": 50.0, "value": 75.0}

    def test_hsl_dict(self):
        hsl = HSL(120, 50, 75)
        d = hsl.dict()
        assert d == {"hue": 120.0, "saturation": 50.0, "lightness": 75.0}

    def test_cmyk_dict(self):
        cmyk = CMYK(25, 50, 75, 10)
        d = cmyk.dict()
        assert d == {"cyan": 25.0, "magenta": 50.0, "yellow": 75.0, "key": 10.0}


class TestColorCopy:
    def test_rgb_copy(self):
        rgb = RGB(255, 128, 64)
        rgb_copy = rgb.copy()
        assert rgb == rgb_copy
        assert rgb is rgb_copy

    def test_rgba_copy(self):
        rgba = RGBA(255, 128, 64, 0.5)
        rgba_copy = rgba.copy()
        assert rgba == rgba_copy
        assert rgba is rgba_copy
