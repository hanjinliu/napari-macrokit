from __future__ import annotations

import inspect
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Literal, Sequence, TypeVar, Union, overload

from macrokit import (
    BaseMacro,
    Expr,
    Head,
    Symbol,
    store,
    store_sequence,
    symbol,
)
from magicgui.widgets import FunctionGui

from napari_macrokit._literals import get_id_safe_class
from napari_macrokit._rename import SymbolGenerator
from napari_macrokit._type_resolution import resolve_single_type

_NEW_TYPES: dict[type, Callable[[Any], str]] = {}
_F = TypeVar("_F", bound=Callable)
_F1 = TypeVar("_F1", bound=Callable[[Any], str])
_R = TypeVar("_R")
_Symbolizer = Callable[[Any], Union[Symbol, Expr]]

SymbolGen = SymbolGenerator()


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


class NapariMacro(BaseMacro):
    def __init__(self):
        import datetime

        super().__init__()
        self._created_time = datetime.datetime.now()

    def __repr__(self) -> str:
        out = []
        for line in str(self).split("\n"):
            if line.strip() == "":
                continue
            if line.startswith("\t"):
                out.append(f"... {line}")
            else:
                out.append(f">>> {line}")
        return "\n".join(out)

    @overload
    def record(self, obj: _F, *, merge: bool = False) -> _F:
        ...

    @overload
    def record(
        self, obj: Literal[None], *, merge: bool = False
    ) -> Callable[[_F], _F]:
        ...

    def record(self, obj=None, *, merge: bool = False):
        """
        Record input function.

        Parameters
        ----------
        obj : callable, optional
            The function to be recorded.
        merge : bool, default is False
            If true, and the last function call was from the same function,
            then overwrite the last line of the macro.
        """

        def wrapper(f):
            if isinstance(f, Callable) and not isinstance(f, type):
                return _record_function(f, macro=self, merge=merge)
            raise TypeError(f"Cannot record {type(f)}")

        return wrapper if obj is None else wrapper(obj)

    @overload
    def magicgui(
        self, function: Callable[..., _R], **kwargs
    ) -> FunctionGui[_R]:
        ...

    @overload
    def magicgui(
        self,
        function: Literal[None] = None,
        **kwargs,
    ) -> Callable[[Callable[..., _R]], FunctionGui[_R]]:
        ...

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

        `auto_call=True` is interpreted as `merge=True`.
        """
        from magicgui import magicgui

        def wrapper(func):
            mfunc = self.record(func, merge=auto_call)
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


_TYPES_NOT_TO_RECORD: set[type] = {type(None)}


def set_unlinked(*types: type):
    """Set types that will not be tracked as output."""
    _TYPES_NOT_TO_RECORD.clear()
    _types = set(types)
    if None in _types:
        _types.discard(None)
        _types.add(type(None))
    _TYPES_NOT_TO_RECORD.clear()
    _TYPES_NOT_TO_RECORD.update(_types)


@contextmanager
def set_unlinked_context(*types: type):
    """Set types that will not be tracked as output."""
    _types = set(types)
    if None in _types:
        _types.discard(None)
        _types.add(type(None))

    _old_state = _TYPES_NOT_TO_RECORD.copy()
    _TYPES_NOT_TO_RECORD.clear()
    _TYPES_NOT_TO_RECORD.update(_types)
    try:
        yield
    finally:
        _TYPES_NOT_TO_RECORD.clear()
        _TYPES_NOT_TO_RECORD.update(_old_state)


def _record_function(_func_: _F, macro: NapariMacro, merge: bool) -> _F:
    """Convert a function into a macro recordable one."""
    if hasattr(_func_, "func"):  # partial
        return _record_function(_func_.func, macro)

    sig = inspect.signature(_func_)
    symbolizers: dict[str, _Symbolizer] = {}

    for name, param in sig.parameters.items():
        ann = param.annotation
        symbolizers[name] = _get_symbolizer(ann)
    if sig.return_annotation is not inspect.Parameter.empty:
        tp = resolve_single_type(sig.return_annotation)
        return_type = get_id_safe_class(tp, tp)
    else:
        return_type = None

    @wraps(_func_)
    def wrapper(*args, **kwargs):
        nonlocal sig, symbolizers, _func_, merge, return_type

        macro_args, macro_kwargs = _get_macro_arguments(
            sig, symbolizers, *args, **kwargs
        )
        # Run function with macro blocked (otherwise recorded macro
        # will call the inner function twice).
        with macro.blocked():
            out = _func_(*args, **kwargs)
        expr = Expr.parse_call(_func_, macro_args, macro_kwargs)

        # If the last function call is the same function, merge with the last
        if merge and _get_last_call_name(macro) == expr.args[0]:
            macro.pop()
            SymbolGen.discard_last()

        for tp in _TYPES_NOT_TO_RECORD:
            if isinstance(out, tp):
                break
        else:
            # If the function returned a value that is needed to be recorded,
            # then interpret the output and record as "var = func(...)"
            if (
                isinstance(out, Sequence)
                and not isinstance(out, str)
                and len(out) < 10
            ):
                sym_out = store_sequence(out)
            else:
                # NOTE: Python literals usually have the same ID, which
                # causes some fatal bugs in macro recording. As a workaround,
                # we convert them into custom int/bool type.
                if _cls := get_id_safe_class(type(out), None):
                    out = _cls(out)
                sym_out = Symbol.asvar(out)

            if return_type is None:
                return_type = type(out)

            sym_out = SymbolGen.generate(out, return_type, sym_out)
            expr = Expr(Head.assign, [sym_out, expr])
        macro.append(expr)
        return out

    store(_func_)
    return wrapper


def _get_symbolizer(ann):
    if isinstance(ann, type) or ann is inspect.Parameter.empty:
        out = _readable_symbol_from_object
    elif hasattr(ann, "__supertype__"):  # NewType
        if _out := _NEW_TYPES.get(ann, None):
            out = lambda x: _out(x)
        else:
            out = _readable_symbol_from_object
    else:
        tp = resolve_single_type(ann)
        out = _get_symbolizer(tp)
    return out


def _readable_symbol_from_object(obj):
    sym = symbol(obj)
    if isinstance(sym, Symbol) and sym.constant:
        return sym
    if isinstance(sym, Expr):
        return Expr(sym.head, [_rename_one(a) for a in sym.args])
    else:
        return SymbolGen.rename_or_generate(obj, type(obj), sym)


def _rename_one(arg: Symbol | Expr):
    if isinstance(arg, Expr):
        return Expr(arg.head, [_rename_one(a) for a in arg.args])
    else:
        return SymbolGen.rename_symbol(arg)


def _get_macro_arguments(
    sig: inspect.Signature,
    symbolizers: dict[str, _Symbolizer],
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


def _get_last_call_name(macro: NapariMacro):
    if len(macro) == 0:
        return None
    last_expr = macro[-1]
    if last_expr.head is Head.assign:
        last_call_expr = last_expr.args[1]
    else:
        last_call_expr = last_expr
    if last_call_expr.head is Head.call:
        return last_call_expr.args[0]
    return None
