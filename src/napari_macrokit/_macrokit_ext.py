from __future__ import annotations

import inspect
from functools import wraps
from types import MethodType
from typing import Any, Callable, Literal, TypeVar, Union, overload

from macrokit import Expr, Head, Macro, Symbol, symbol

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
        _NEW_TYPES[tp] = f
        return f

    return wrapper if function is None else wrapper(function)


class NapariMacro(Macro):
    def __init__(self):
        super().__init__()

    def __repr__(self) -> str:
        out = []
        for line in str(self).split("\n"):
            if line.startswith("\t"):
                out.append(f"... {line}")
            else:
                out.append(f">>> {line}")
        return "\n".join(out)

    def record(self, obj):
        if isinstance(obj, Callable) and not isinstance(obj, type):
            return _record_function(obj, macro=self)
        raise TypeError(f"Cannot record {type(obj)}")

    def magicgui(
        self,
        function: Callable | None = None,
        *,
        layout: str = "vertical",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        call_button: bool | str | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        main_window: bool = False,
        persist: bool = False,
        raise_on_unknown: bool = False,
        **param_options: dict,
    ):
        """
        A shortcut for creating a recordable magicgui widget.

        >>> @macro.magicgui
        >>> def func(a: int, b: str):
        >>>     ...

        is equivalent to

        >>> @magicgui
        >>> @macro.record
        >>> def func(a: int, b: str):
        >>>     ...
        """
        from magicgui import magicgui

        def wrapper(func):
            mfunc = self.record(func)
            return magicgui(
                mfunc,
                layout=layout,
                scrollable=scrollable,
                labels=labels,
                tooltips=tooltips,
                call_button=call_button,
                auto_call=auto_call,
                result_widget=result_widget,
                main_window=main_window,
                persist=persist,
                raise_on_unknown=raise_on_unknown,
                **param_options,
            )

        return wrapper if function is None else wrapper(function)


_F = TypeVar("_F", bound=Callable)


def _record_function(func: _F, macro: NapariMacro) -> _F:
    """Convert a function into a macro recordable one."""
    sig = inspect.signature(func)
    symbolizers: dict[str, Symbolizer] = {}

    for name, param in sig.parameters.items():
        ann = param.annotation
        symbolizers[name] = _get_symbolizer(ann)

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal sig, symbolizers, func

        macro_args, macro_kwargs = _get_macro_arguments(
            sig, symbolizers, *args, **kwargs
        )
        out = func(*args, **kwargs)
        expr = Expr.parse_call(func, macro_args, macro_kwargs)
        if _has_return_annotation(sig):
            expr = Expr(Head.assign, [Symbol.asvar(out), expr])

        macro.append(expr)
        return out

    # To avoid FunctionGui RecursionError
    wrapper.__name__ = f"<recordable>.{func.__name__}"

    if hasattr(func, "__get__"):
        wrapper.__get__ = lambda obj, objtype=None: _record_method(
            func.__get__(obj, objtype), macro
        )
    return wrapper


_M = TypeVar("_M", bound=MethodType)


def _record_method(func: _M, macro: NapariMacro) -> _M:
    """Convert a method into a macro recordable one."""
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
        if _has_return_annotation(sig):
            expr = Expr(Head.assign, [Symbol.asvar(out), expr])

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


def _has_return_annotation(sig: inspect.Signature) -> bool:
    ann = sig.return_annotation
    return ann is not inspect.Parameter.empty
