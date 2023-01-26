from __future__ import annotations

import builtins
from typing import overload

# int/bool that live in different ID for different object.


class int(builtins.int):
    __doc__ = builtins.int.__doc__


class bool(builtins.int):
    __doc__ = builtins.bool.__doc__

    def __repr__(self) -> str:
        return repr(builtins.bool(self))

    # fmt: off
    @overload
    def __and__(self, __x: builtins.bool) -> builtins.bool: ...  # pragma: no cover
    @overload
    def __and__(self, __x: builtins.int) -> builtins.int: ...  # pragma: no cover
    @overload
    def __or__(self, __x: builtins.bool) -> builtins.bool: ...  # pragma: no cover
    @overload
    def __or__(self, __x: builtins.int) -> builtins.int: ...  # pragma: no cover
    @overload
    def __xor__(self, __x: builtins.bool) -> builtins.bool: ...  # pragma: no cover
    @overload
    def __xor__(self, __x: builtins.int) -> builtins.int: ...  # pragma: no cover
    @overload
    def __rand__(self, __x: builtins.bool) -> builtins.bool: ...  # pragma: no cover
    @overload
    def __rand__(self, __x: builtins.int) -> builtins.int: ...  # pragma: no cover
    @overload
    def __ror__(self, __x: builtins.bool) -> builtins.bool: ...  # pragma: no cover
    @overload
    def __ror__(self, __x: builtins.int) -> builtins.int: ...  # pragma: no cover
    @overload
    def __rxor__(self, __x: builtins.bool) -> builtins.bool: ...  # pragma: no cover
    @overload
    def __rxor__(self, __x: builtins.int) -> builtins.int: ...  # pragma: no cover
    # fmt: on


class float(builtins.float):
    __doc__ = builtins.float.__doc__


class str(builtins.str):
    __doc__ = builtins.str.__doc__


_ID_SAFE_MAP = {
    builtins.int: int,
    builtins.bool: bool,
    builtins.float: float,
    builtins.str: str,
}


def get_id_safe_class(cls, default=None) -> type | None:
    return _ID_SAFE_MAP.get(cls, default)
