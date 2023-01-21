from macrokit import Symbol

from napari_macrokit import get_macro


def test_int():
    macro = get_macro()

    @macro.record
    def add(a: int, b: int) -> int:
        return a + b

    @macro.record
    def mul(a: int, b: int) -> int:
        return a * b

    x0 = add(3, 5)
    x1 = mul(x0, 2)
    x2 = add(x0, x1)
    _x0 = Symbol.asvar(x0)
    _x1 = Symbol.asvar(x1)
    _x2 = Symbol.asvar(x2)
    assert str(macro[0]) == f"{_x0} = add(3, 5)"
    assert str(macro[1]) == f"{_x1} = mul({_x0}, 2)"
    assert str(macro[2]) == f"{_x2} = add({_x0}, {_x1})"
