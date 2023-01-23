from napari_macrokit._macrokit_ext import NapariMacro, SymbolGen


def test_int():
    macro = NapariMacro()

    @macro.record
    def add(a: int, b: int) -> int:
        return a + b

    @macro.record
    def mul(a: int, b: int) -> int:
        return a * b

    x0 = add(3, 5)
    x1 = mul(x0, 2)
    x2 = add(x0, x1)
    _x0 = SymbolGen.as_renamed_symbol(x0)
    _x1 = SymbolGen.as_renamed_symbol(x1)
    _x2 = SymbolGen.as_renamed_symbol(x2)
    assert str(macro[0]) == f"{_x0} = add(3, 5)"
    assert str(macro[1]) == f"{_x1} = mul({_x0}, 2)"
    assert str(macro[2]) == f"{_x2} = add({_x0}, {_x1})"
