import datetime

import pytest
from macrokit import symbol

from napari_macrokit import set_unlinked_context, symbol_of
from napari_macrokit._macrokit_ext import NapariMacro


class NoGC:
    """Store all instances of this class to avoid garbage collection."""

    instances = []

    def __init__(self) -> None:
        self.__class__.instances.append(self)


def test_function_call():
    macro = NapariMacro()

    @macro.record
    def func(a, b):
        return a + b

    assert len(macro) == 0
    func(1, 2)
    assert len(macro) == 1
    func(1, b=2)
    assert len(macro) == 2
    func(a=1, b=2)
    assert len(macro) == 3
    assert str(macro[0]).split(" = ")[1] == "func(1, 2)"
    assert str(macro[1]).split(" = ")[1] == "func(1, b=2)"
    assert str(macro[2]).split(" = ")[1] == "func(a=1, b=2)"


def test_merge():
    macro = NapariMacro()

    @macro.record(merge=True)
    def func(a: int, b: bool) -> int:
        if b:
            return -a
        return a

    @macro.record(merge=True)
    def func2(t: int):
        return t + 1

    out = func(1, True)
    _int0 = symbol_of(out)
    assert len(macro) == 1 and str(macro[0]) == f"{_int0} = func(1, True)"
    func(2, True)
    assert len(macro) == 1 and str(macro[0]) == f"{_int0} = func(2, True)"
    result = func(2, False)
    assert len(macro) == 1 and str(macro[0]) == f"{_int0} = func(2, False)"
    out = func2(result)
    _int1 = symbol_of(out)
    assert len(macro) == 2
    assert str(macro[0]) == f"{_int0} = func(2, False)"
    assert str(macro[1]) == f"{_int1} = func2({_int0})"


@pytest.mark.parametrize(
    "val",
    [
        datetime.datetime(2023, 1, 26, 10, 44, 23),
        datetime.date(2023, 1, 26),
        datetime.time(10, 45, 23),
    ],
)
def test_consistency(val):
    assert symbol(val).eval() == val


@pytest.mark.parametrize("obj", [0, int])
def test_wrong_type(obj):
    macro = NapariMacro()
    with pytest.raises(TypeError):
        macro.record(obj)


def test_magicgui():
    macro = NapariMacro()

    @macro.magicgui
    def f(x: int):
        pass

    assert f.x.widget_type == "SpinBox"
    f()
    assert str(macro[0]) == "f(0)"


def test_magicgui_with_autocall():
    macro = NapariMacro()

    @macro.magicgui(auto_call=True)
    def f(x: int):
        pass

    assert f.x.widget_type == "SpinBox"
    assert f.call_button is None
    f(0)
    assert len(macro) == 1 and str(macro[0]) == "f(0)"
    f(1)
    assert len(macro) == 1 and str(macro[0]) == "f(1)"


def test_unlink_types():
    macro = NapariMacro()

    @macro.record
    def f():
        return 0

    @macro.record
    def g():
        return "a"

    @macro.record
    def h():
        return 1.0

    with set_unlinked_context(int, str):
        f()
        g()
        out = h()

    _out = symbol_of(out)
    assert len(macro) == 3
    assert str(macro[0]) == "f()"
    assert str(macro[1]) == "g()"
    assert str(macro[2]) == f"{_out} = h()"

    fout = symbol_of(f())
    gout = symbol_of(g())
    hout = symbol_of(h())
    assert len(macro) == 6
    assert str(macro[3]) == f"{fout} = f()"
    assert str(macro[4]) == f"{gout} = g()"
    assert str(macro[5]) == f"{hout} = h()"


def test_keyword_like_symbol():
    class Import(NoGC):
        pass

    macro = NapariMacro()

    @macro.record
    def f():
        return Import()

    f()
    assert len(macro) == 1


def test_bad_type_name():
    class Bad(NoGC):
        pass

    Bad.__name__ = "$%&"

    macro = NapariMacro()

    @macro.record
    def f():
        return Bad()

    f()
    assert len(macro) == 1


def test_same_type_name():
    class XYZ(NoGC):
        pass

    class XYz(NoGC):
        pass

    class Xyz(NoGC):
        pass

    macro = NapariMacro()

    @macro.record
    def f0():
        return XYZ()

    @macro.record
    def f1():
        return XYz()

    @macro.record
    def f2():
        return Xyz()

    f0()
    f1()
    f2()
    assert len(macro) == 3
    assert str(macro[0]) == "xyz0 = f0()"
    assert str(macro[1]) == "xyz0_0 = f1()"
    assert str(macro[2]) == "xyz1_0 = f2()"
