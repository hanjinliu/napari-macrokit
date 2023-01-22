import builtins
from typing import overload

# int/bool that live in different ID for different object.


class int(builtins.int):
    __doc__ = builtins.int.__doc__


class bool(builtins.int):
    __doc__ = builtins.bool.__doc__

    def __repr__(self) -> str:
        return repr(builtins.bool(self))

    @overload
    def __and__(self, __x: builtins.bool) -> builtins.bool:
        ...

    @overload
    def __and__(self, __x: builtins.int) -> builtins.int:
        ...

    @overload
    def __or__(self, __x: builtins.bool) -> builtins.bool:
        ...

    @overload
    def __or__(self, __x: builtins.int) -> builtins.int:
        ...

    @overload
    def __xor__(self, __x: builtins.bool) -> builtins.bool:
        ...

    @overload
    def __xor__(self, __x: builtins.int) -> builtins.int:
        ...

    @overload
    def __rand__(self, __x: builtins.bool) -> builtins.bool:
        ...

    @overload
    def __rand__(self, __x: builtins.int) -> builtins.int:
        ...

    @overload
    def __ror__(self, __x: builtins.bool) -> builtins.bool:
        ...

    @overload
    def __ror__(self, __x: builtins.int) -> builtins.int:
        ...

    @overload
    def __rxor__(self, __x: builtins.bool) -> builtins.bool:
        ...

    @overload
    def __rxor__(self, __x: builtins.int) -> builtins.int:
        ...
