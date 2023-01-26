import pytest
from macrokit import symbol

from napari_macrokit import _literals as _lit
from napari_macrokit import symbol_of
from napari_macrokit._macrokit_ext import NapariMacro


@pytest.mark.parametrize(
    "value, typ",
    [
        (1, _lit.int),
        (1.2, _lit.float),
        (True, _lit.bool),
        ("abc", _lit.str),
    ],
)
def test_type_conversion(value, typ):
    cls = _lit.get_id_safe_class(type(value))
    v0 = cls(value)
    v1 = cls(value)
    assert type(v0) is typ
    assert type(v1) is typ
    assert id(v0) != id(v1)


@pytest.mark.parametrize(
    "value, typ",
    [
        (1, _lit.int),
        (1.2, _lit.float),
        (True, _lit.bool),
        ("abc", _lit.str),
    ],
)
def test_same_symbol(value, typ):
    macro = NapariMacro()

    @macro.record
    def f(a):
        return typ(a)

    @macro.record
    def g(a):
        pass

    out = f(value)
    g(out)
    _a = symbol_of(out)
    _v = symbol(value)
    assert str(macro[0]) == f"{_a} = f({_v})"
    assert str(macro[1]) == f"g({_a})"


@pytest.mark.parametrize(
    "typ0, typ",
    [
        (int, _lit.int),
        (float, _lit.float),
        (bool, _lit.bool),
        (str, _lit.str),
    ],
)
def test_doc(typ0, typ):
    assert typ0.__doc__ == typ.__doc__


def test_bool():
    assert _lit.bool(True)
    assert not _lit.bool(False)
    assert repr(_lit.bool(True)) == "True"
    assert repr(_lit.bool(False)) == "False"
