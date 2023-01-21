from __future__ import annotations

import typing
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Hashable,
    TypeVar,
    overload,
)

from magicgui.widgets import EmptyWidget, Widget
from typing_extensions import Annotated, _AnnotatedAlias

try:
    from typing import _tp_cache
except ImportError:
    _tp_cache = lambda x: x

if TYPE_CHECKING:
    from magicgui.widgets import FunctionGui
    from magicgui.widgets.bases import CategoricalWidget


# Bound type

_W = TypeVar("_W", bound=Widget)
_V = TypeVar("_V", bound=object)
_T = TypeVar("_T")


def bound(obj: Callable[[_W], _V]) -> type[_V]:
    """Function version of ``Bound[...]``."""
    if callable(obj):
        outtype = obj.__annotations__.get("return", Any)
    else:
        outtype = type(obj)
    while isinstance(outtype, _AnnotatedAlias):
        outtype, _ = split_annotated_type(outtype)
    return Annotated[outtype, {"bind": obj, "widget_type": EmptyWidget}]


class _BoundAlias(type):
    @overload
    def __getitem__(cls, value: Callable[..., _V]) -> type[_V]:
        ...

    @overload
    def __getitem__(cls, value: type[_V]) -> type[_V]:
        ...

    @_tp_cache
    def __getitem__(cls, value):
        if isinstance(value, tuple):
            raise TypeError(
                "Bound[...] should be used with only one "
                "argument (the object to be bound)."
            )
        return bound(value)


class Bound(metaclass=_BoundAlias):
    """
    Make Annotated type from a MagicField or a method, such as:

    ``Bound[value]`` is identical to ``Annotated[Any, {"bind": value}]``.
    """

    def __new__(cls, *args):
        raise TypeError(
            "`Bound(...)` is deprecated since 0.5.21. Bound is now a generic alias instead "
            "of a function. Please use `Bound[...]`."
        )

    def __init_subclass__(cls, *args, **kwargs):
        raise TypeError(f"Cannot subclass {cls.__module__}.Bound")


# Stored type


class _StoredLastAlias(type):
    @overload
    def __getitem__(cls, value: type[_T]) -> type[_T]:
        ...

    @overload
    def __getitem__(cls, value: tuple[type[_T], Hashable]) -> type[_T]:
        ...

    def __getitem__(cls, value):
        stored_cls = Stored._class_getitem(value)

        def _getter(w=None):
            store = stored_cls._store
            if len(store) > 0:
                return store[-1]
            raise IndexError(f"Storage of {stored_cls} is empty.")

        return Annotated[
            stored_cls.__args__[0],
            {"bind": _getter, "widget_type": EmptyWidget},
        ]


class StoredLast(Generic[_T], metaclass=_StoredLastAlias):
    def __new__(cls, *args, **kwargs):
        raise TypeError("Type StoredLast cannot be instantiated.")

    def __init_subclass__(cls, *args, **kwargs):
        raise TypeError(f"Cannot subclass {cls.__module__}.StoredLast.")


class _StoredMeta(type):
    _instances: dict[Hashable, _StoredMeta] = {}
    _categorical_widgets: defaultdict[
        Hashable, list[CategoricalWidget]
    ] = defaultdict(list)

    _store: list
    _maxsize: int
    __args__: tuple[type]

    @overload
    def __getitem__(cls, value: type[_T]) -> type[_T]:
        ...

    @overload
    def __getitem__(cls, value: tuple[type[_T], Hashable]) -> type[_T]:
        ...

    def __getitem__(cls, value):
        return Stored._class_getitem(value)


_U = TypeVar("_U")


class DefaultSpec:
    def __repr__(self) -> str:
        return "<default>"

    def __hash__(self) -> int:
        return id(self)


class Stored(Generic[_T], metaclass=_StoredMeta):
    """
    Use variable store of specific type.

    ``Stored[T]`` is identical to ``T`` for the type checker. However, outputs
    are stored for later use in functions with the same annotation.
    """

    _store: list[_T]
    _maxsize: int
    _hash_value: Hashable
    Last = StoredLast
    _no_spec = DefaultSpec()

    __args__: tuple[type] = ()
    _repr_map: dict[type[_U], Callable[[_U], str]] = {}

    @classmethod
    def new(cls, tp: type[_U], maxsize: int | None = None) -> Stored[_U]:
        """Create a new storage with given maximum size."""
        i = 0
        while (tp, i) in _StoredMeta._instances:
            i += 1
        outtype = Stored[tp, 0]
        if maxsize is None:
            maxsize = _maxsize_for_type(tp)
        else:
            if not isinstance(maxsize, int) or maxsize <= 0:
                raise TypeError("maxsize must be a positive integer")
            outtype._maxsize = maxsize
        return outtype

    @classmethod
    def hash_key(cls) -> tuple[type[_T], Hashable]:
        return cls.__args__[0], cls._hash_value

    @overload
    @classmethod
    def register_repr(
        cls, tp: type[_U], func: Callable[[_U], str]
    ) -> Callable[[_U], str]:
        ...

    @overload
    @classmethod
    def register_repr(
        cls, tp: type[_U]
    ) -> Callable[[Callable[[_U], str]], Callable[[_U], str]]:
        ...

    @classmethod
    def register_repr(cls, tp, func=None):
        """Register a function to convert a value to string."""

        def wrapper(f):
            if not callable(f):
                raise TypeError("func must be a callable")
            cls._repr_map[tp] = f
            return f

        return wrapper(func) if func is not None else wrapper

    @classmethod
    def clear(cls):
        cls._store.clear()

    @classmethod
    def get_widget(cls):
        raise NotImplementedError

    @classmethod
    def _get_choice(cls, w: CategoricalWidget):
        # NOTE: cls is Stored, not Stored[X]!
        ann: type[Stored] = w.annotation
        widgets = _StoredMeta._categorical_widgets[ann.hash_key()]
        if w not in widgets:
            widgets.append(w)
        _repr_func = cls._repr_map.get(ann.__args__[0], _repr_like)
        return [
            (f"{i}: {_repr_func(x)}", x)
            for i, x in enumerate(reversed(ann._store))
        ]

    @staticmethod
    def _store_value(gui: FunctionGui, value, return_type: type[Stored]):
        return_type._store.append(value)
        if len(return_type._store) > return_type._maxsize:
            return_type._store.pop(0)

        # reset all the related categorical widgets.
        for w in _StoredMeta._categorical_widgets.get(
            return_type.hash_key(), []
        ):
            w.reset_choices()

        # Callback of the inner type annotation
        try:
            from magicgui.type_map import type2callback
        except ImportError:
            # magicgui < 0.7.0
            from magicgui.type_map import _type2callback as type2callback

        inner_type = return_type.__args__[0]
        for cb in type2callback(inner_type):
            cb(gui, value, inner_type)

    @classmethod
    def _class_getitem(cls, value):
        if isinstance(value, tuple):
            if len(value) != 2:
                raise TypeError(
                    "Input of Stored must be a type or (type, Any)"
                )
            _tp, _hash = value
        else:
            if not _is_type_like(value):
                raise TypeError(
                    "The first argument of Stored must be a type but "
                    f"got {type(value)}."
                )
            _tp, _hash = value, cls._no_spec
        key = (_tp, _hash)
        if outtype := _StoredMeta._instances.get(key):
            return outtype
        name = f"Stored[{_tp.__name__}, {_hash!r}]"

        ns = {
            "_store": [],
            "_hash_value": _hash,
            "_maxsize": _maxsize_for_type(_tp),
        }
        outtype: cls = _StoredMeta(name, (cls,), ns)
        outtype.__args__ = (_tp,)
        _StoredMeta._instances[key] = outtype
        return outtype


def _is_type_like(x: Any):
    return isinstance(x, (type, typing._GenericAlias)) or hasattr(
        x, "__supertype__"
    )


def _repr_like(x: Any):
    lines = repr(x).split("\n")
    if len(lines) == 1:
        return lines[0]
    else:
        return lines[0] + " ... "


def _maxsize_for_type(tp: type[_T]) -> int:
    if hasattr(tp, "__array__"):
        return 12
    elif tp is object:
        return 120
    else:
        return 10000


def split_annotated_type(annotation: _AnnotatedAlias) -> tuple[Any, dict]:
    """Split an Annotated type into its base type and options dict."""
    if not isinstance(annotation, _AnnotatedAlias):
        raise TypeError("Type hint must be an 'Annotated' type.")
    if not isinstance(annotation.__metadata__[0], dict):
        raise TypeError(
            "Invalid Annotated format for magicgui. First arg must be a dict"
        )

    meta: dict = {}
    for _meta in annotation.__metadata__:
        meta.update(_meta)

    return annotation.__args__[0], meta
