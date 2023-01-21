from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._macrokit_ext import NapariMacro


_MACROS: dict[str, NapariMacro] = {}


def get_macro(name: str = "default") -> NapariMacro:
    from ._macrokit_ext import NapariMacro

    macro = _MACROS.get(name, None)
    if macro is None:
        macro = _MACROS[name] = NapariMacro()
    return macro
