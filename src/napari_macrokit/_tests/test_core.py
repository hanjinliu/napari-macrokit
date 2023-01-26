import pytest

from napari_macrokit import available_keys, get_macro
from napari_macrokit.core import collect_macro, temp_macro

from ._utils import macro_cleanup


def test_same_macro():
    with macro_cleanup():

        def f0():
            macro = get_macro("tests:test_same_macro")
            macro.append("a = 0")

        def f1():
            macro = get_macro("tests:test_same_macro")
            macro.append("a = 1")

        f0()
        f1()
        f0()
        macro = get_macro("tests:test_same_macro")
        assert str(macro[0]) == "a = 0"
        assert str(macro[1]) == "a = 1"
        assert str(macro[2]) == "a = 0"


def test_independent_macro():
    with macro_cleanup():

        def f0():
            macro = get_macro("tests:test_independent_macro(0)")
            macro.append("a = 0")

        def f1():
            macro = get_macro("tests:test_independent_macro(1)")
            macro.append("a = 1")

        f0()
        f1()
        f0()
        macro0 = get_macro("tests:test_independent_macro(0)")
        macro1 = get_macro("tests:test_independent_macro(1)")
        assert len(macro0) == 2
        assert len(macro1) == 1
        assert str(macro0[0]) == "a = 0"
        assert str(macro0[1]) == "a = 0"
        assert str(macro1[0]) == "a = 1"


def test_collect_macro():
    with temp_macro(["m0", "m1"]) as macros:
        m0, m1 = macros
        assert available_keys() == ["m0", "m1"]
        macro = collect_macro()
        m0.append("x0 = 0")
        m1.append("x1 = 0")
        assert len(macro) == 2
        assert str(macro[0]) == "x0 = 0"
        assert str(macro[1]) == "x1 = 0"


def test_collect_macro_partially():
    with temp_macro(["m0", "m1", "m2"]) as macros:
        m0, m1, m2 = macros
        assert available_keys() == ["m0", "m1", "m2"]
        with pytest.raises(TypeError):
            collect_macro(["m0", "m2"])
        macro = collect_macro(children=["m0", "m2"])
        m0.append("x0 = 0")
        m1.append("x1 = 0")
        m2.append("x2 = 0")
        assert len(macro) == 2
        assert str(macro[0]) == "x0 = 0"
        assert str(macro[1]) == "x2 = 0"
        assert str(m1[0]) == "x1 = 0"


def test_macro_repr():
    with temp_macro("m0") as macro:
        macro.append("a = 0")
        macro.append("def f(x):\n\treturn 0")
        assert repr(macro) == ">>> a = 0\n>>> def f(x):\n...     return 0"
