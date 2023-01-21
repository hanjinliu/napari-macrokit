from __future__ import annotations

import inspect
from functools import wraps
from types import MethodType
from typing import Any, Callable, Literal, TypeVar, Union, overload

from macrokit import Expr, Macro, Symbol, symbol

from ._type_resolution import resolve_single_type

_NEW_TYPES: dict[type, Callable[[Any], str]] = {}
_F1 = TypeVar("_F1", bound=Callable[[Any], str])
Symbolizer = Callable[[Any], Union[Symbol, Expr]]


@overload
def register_new_type(tp: Callable, function: _F1) -> _F1:
    ...


@overload
def register_new_type(
    tp: Callable, function: Literal[None] = None
) -> Callable[[_F1], _F1]:
    ...


def register_new_type(tp, function=None):
    def wrapper(f):
        _NEW_TYPES[tp] = function
        return f

    return wrapper if function is None else wrapper(function)


class NapariMacro(Macro):
    def record(self, obj):
        if isinstance(obj, type):
            return super().record(obj)
        elif isinstance(obj, Callable):
            return _record_function(obj, macro=self)
        return super().record(obj)


_F = TypeVar("_F", bound=Callable)


def _record_function(func: _F, macro: NapariMacro) -> _F:
    sig = inspect.signature(func)
    symbolizers: dict[str, Symbolizer] = {}

    for name, param in sig.parameters.items():
        ann = param.annotation
        symbolizers[name] = _get_symbolizer(ann)

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal sig, symbolizers

        macro_args, macro_kwargs = _get_macro_arguments(
            sig, symbolizers, *args, **kwargs
        )
        out = func(*args, **kwargs)
        expr = Expr.parse_call(func, macro_args, macro_kwargs)
        macro.append(expr)
        return out

    if hasattr(func, "__get__"):
        wrapper.__get__ = lambda obj, objtype=None: _record_method(
            func.__get__(obj, objtype), macro
        )
    return wrapper


_M = TypeVar("_M", bound=MethodType)


def _record_method(func: _M, macro: NapariMacro) -> _M:
    sig = inspect.signature(func)
    symbolizers: dict[str, Symbolizer] = {}

    for name, param in sig.parameters.items():
        ann = param.annotation
        symbolizers[name] = _get_symbolizer(ann)

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal sig, symbolizers

        macro_args, macro_kwargs = _get_macro_arguments(
            sig, symbolizers, *args, **kwargs
        )
        out = func(*args, **kwargs)
        expr = Expr.parse_method(func.__self__, func, macro_args, macro_kwargs)

        macro.append(expr)
        return out

    return wrapper


def _get_symbolizer(ann):
    if isinstance(ann, type) or ann is inspect.Parameter.empty:
        out = symbol
    elif hasattr(ann, "__supertype__"):  # NewType
        out = _NEW_TYPES.get(ann, symbol)
    else:
        tp = resolve_single_type(ann)
        out = _get_symbolizer(tp)
    return out


def _get_macro_arguments(
    sig: inspect.Signature,
    symbolizers: dict[str, Symbolizer],
    *args,
    **kwargs,
):
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    nargs = len(args)
    argdict = bound.arguments
    argkeys = list(argdict.keys())
    macro_kwargs = {k: symbolizers[k](val) for k, val in argdict.items()}

    macro_args = tuple(macro_kwargs.pop(argkeys[i]) for i in range(nargs))
    return macro_args, macro_kwargs
