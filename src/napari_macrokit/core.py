from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from ._macrokit_ext import NapariMacro


_MACROS: dict[str, NapariMacro] = {}


def get_macro(name: str = "main") -> NapariMacro:
    from ._macrokit_ext import NapariMacro

    if not isinstance(name, str):
        raise TypeError(f"Macro name must be a string, got {type(name)}.")
    macro = _MACROS.get(name, None)
    if macro is None:
        macro = _MACROS[name] = NapariMacro()
    return macro


def merge_macros(
    macros: Iterable[NapariMacro], name: str = "merged"
) -> NapariMacro:
    macros = list(macros)
    if name in _MACROS:
        raise ValueError(f"Macro name {name} is already in use.")
    if len({id(x) for x in macros}) < len(macros):
        raise ValueError("Input macro list has duplicate references.")
    new = get_macro(name)
    for macro in macros:
        macro.callbacks.append(new.append)
    return new


def get_merged_macro(
    name: str = "merged", children: list[str] | None = None
) -> NapariMacro:
    if children is None:
        children = list_macro_keys()
    macros = [get_macro(name) for name in children]
    return merge_macros(macros, name)


def list_macro_keys() -> list[str]:
    return list(_MACROS.keys())
