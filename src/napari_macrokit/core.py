from __future__ import annotations

from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    ContextManager,
    Iterable,
    Sequence,
    overload,
)

from macrokit import Symbol

if TYPE_CHECKING:  # pragma: no cover
    from ._macrokit_ext import NapariMacro


_MACROS: dict[str, NapariMacro] = {}


def get_macro(name: str = "main") -> NapariMacro:
    """Get the macro object of given name."""
    from ._macrokit_ext import NapariMacro
    from ._widgets import QMacroView

    if not isinstance(name, str):
        raise TypeError(f"Macro name must be a string, got {type(name)}.")
    macro = _MACROS.get(name, None)
    if macro is None:
        macro = _MACROS[name] = NapariMacro()

    if widget := QMacroView.current():
        widget._tabwidget.add_macro(macro, name)
    return macro


def _safe_get_macro(name: str) -> NapariMacro:
    if name in _MACROS:
        raise ValueError(f"Macro of name {name!r} already exists.")
    return get_macro(name)


@overload
def temp_macro(name: str = "temp") -> ContextManager[NapariMacro]:
    ...


@overload
def temp_macro(name: Sequence[str]) -> ContextManager[list[NapariMacro]]:
    ...


@contextmanager
def temp_macro(name: str = "temp") -> ContextManager[NapariMacro]:
    """Create temporary macro object(s)."""
    is_sequence = not isinstance(name, str)
    if is_sequence:
        macro: list[NapariMacro] = []
        for n in name:
            macro.append(_safe_get_macro(n))
    else:
        macro = _safe_get_macro(name)
    try:
        yield macro
    finally:
        if is_sequence:
            for n in name:
                _MACROS.pop(n, None)
        else:
            _MACROS.pop(name, None)


def _merge_macros(macros: Iterable[NapariMacro], name) -> NapariMacro:
    macros = list(macros)
    if name in _MACROS:
        raise ValueError(f"Macro name {name} is already in use.")
    if len({id(x) for x in macros}) < len(macros):
        raise ValueError("Input macro list has duplicate references.")
    new = get_macro(name)
    for macro in macros:
        macro.on_appended.append(new.append)
        macro.on_popped.append(lambda: new.pop())
    return new


def collect_macro(
    name: str = "<collection>", children: list[str] | None = None
) -> NapariMacro:
    """
    Collect all the macro objects that exist at this point and link them
    to the returned macro.

    Parameters
    ----------
    name : str, optional
        Name of the macro to be returned
    children : list of str, optional
        List of names of macro objects that will be collected. Collect
        all by default.

    Returns
    -------
    NapariMacro
        The macro object.
    """
    if children is None:
        children = available_keys()
    if not isinstance(name, str):
        raise TypeError(f"`name` must be str, got {type(name)}")
    macros = [get_macro(n) for n in children]
    return _merge_macros(macros, name)


def available_keys() -> list[str]:
    return list(_MACROS.keys())


def symbol_of(obj: Any) -> Symbol:
    """Get the symbol object used to represent the input object."""
    from napari_macrokit._macrokit_ext import SymbolGen

    return SymbolGen.as_renamed_symbol(obj)
