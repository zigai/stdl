import pytest

pydantic = pytest.importorskip("pydantic")
from pydantic import BaseModel, ValidationError

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
    assert isinstance(c.model_dump_json(), str)


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


def test_union_validation_accepts_hex_instance():
    class NumberColorModel(BaseModel):
        color: RGB | RGBA | HEX

    payload = {"color": HEX("#2055b9")}

    model = NumberColorModel.model_validate(payload)

    assert isinstance(model.color, HEX)


def test_union_validation_accepts_repr_for_late_branch():
    class ColorUnionModel(BaseModel):
        color: RGB | HEX

    payload = {"color": "hex(#123456)"}

    model = ColorUnionModel.model_validate(payload)

    assert isinstance(model.color, HEX)
    assert model.color.value == "#123456"


def test_union_validation_accepts_mapping_for_late_branch():
    class ColorUnionModel(BaseModel):
        color: RGBA | HEX

    payload = {"color": {"value": "#abcdef"}}

    model = ColorUnionModel.model_validate(payload)

    assert isinstance(model.color, HEX)
    assert model.color.value == "#abcdef"


def test_union_validation_keeps_first_branch_instance():
    class ColorUnionModel(BaseModel):
        color: RGB | HEX

    rgb = RGB(1, 2, 3)

    model = ColorUnionModel.model_validate({"color": rgb})

    assert model.color is rgb


def test_union_validation_reports_invalid_values():
    class ColorUnionModel(BaseModel):
        color: RGB | HEX

    with pytest.raises(ValidationError):
        ColorUnionModel.model_validate({"color": 42})
