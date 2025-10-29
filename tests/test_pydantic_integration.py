import pytest

pydantic = pytest.importorskip("pydantic")
from pydantic import BaseModel

from stdl.color import ASSA, CMYK, HEX, HSL, HSV, RGB, RGBA


class ColorContainer(BaseModel):
    rgb: RGB
    rgba: RGBA
    hex: HEX
    hsv: HSV
    hsl: HSL
    cmyk: CMYK
    assa: ASSA


def test_model_dump_preserves_objects_and_json_serializes():
    c = ColorContainer(
        rgb=RGB(255, 0, 0),
        rgba=RGBA(0, 255, 0, 0.8),
        hex=HEX("#0000FF"),
        hsv=HSV(120, 1.0, 1.0),
        hsl=HSL(240, 1.0, 0.5),
        cmyk=CMYK(0, 1.0, 1.0, 0),
        assa=ASSA("FFFF00"),
    )
    d = c.model_dump()
    assert isinstance(d["rgb"], RGB)
    assert isinstance(d["rgba"], RGBA)
    assert isinstance(d["hex"], HEX)
    assert isinstance(d["hsv"], HSV)
    assert isinstance(d["hsl"], HSL)
    assert isinstance(d["cmyk"], CMYK)
    assert isinstance(d["assa"], ASSA)
    # Ensure JSON dump still uses repr strings
    js = c.model_dump_json()
    assert isinstance(js, str)


def test_validate_from_repr_strings():
    payload = {
        "rgb": "rgb(255, 0, 0)",
        "rgba": "rgba(0, 255, 0, 0.8)",
        "hex": "hex(#0000ff)",
        "hsv": "hsv(120.0, 1.0, 1.0)",
        "hsl": "hsl(240.0, 1.0, 0.5)",
        "cmyk": "cmyk(0.0, 1.0, 1.0, 0.0)",
        "assa": "assa(ffff00)",
    }
    c = ColorContainer.model_validate(payload)
    assert isinstance(c.rgb, RGB)
    assert isinstance(c.rgba, RGBA)
    assert isinstance(c.hex, HEX)
    assert isinstance(c.hsv, HSV)
    assert isinstance(c.hsl, HSL)
    assert isinstance(c.cmyk, CMYK)
    assert isinstance(c.assa, ASSA)


def test_validate_from_dicts():
    payload = {
        "rgb": {"r": 255, "g": 0, "b": 0},
        "rgba": {"red": 0, "green": 255, "blue": 0, "alpha": 0.8},
        "hex": {"value": "#0000ff"},
        "hsv": {"h": 120, "s": 100, "v": 100},
        "hsl": {"hue": 240, "saturation": 100, "lightness": 50},
        "cmyk": {"c": 0, "m": 100, "y": 100, "k": 0},
        "assa": {"clean_value": "FFFF00"},
    }
    c = ColorContainer.model_validate(payload)
    assert isinstance(c.rgb, RGB)
    assert isinstance(c.rgba, RGBA)
    assert isinstance(c.hex, HEX)
    assert isinstance(c.hsv, HSV)
    assert isinstance(c.hsl, HSL)
    assert isinstance(c.cmyk, CMYK)
    assert isinstance(c.assa, ASSA)
