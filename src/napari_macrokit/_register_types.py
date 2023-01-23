from __future__ import annotations

import datetime
from enum import Enum
from pathlib import Path

import numpy as np
from macrokit import Expr, Head, Mock, Symbol, register_type, symbol

from ._macrokit_ext import register_new_type


def register_all():
    _register_builtin_types()
    _register_numpy_types()
    _register_napari_types()


def _register_builtin_types():
    # classes
    _datetime = Expr(Head.getattr, [datetime, datetime.datetime])
    _date = Expr(Head.getattr, [datetime, datetime.date])
    _time = Expr(Head.getattr, [datetime, datetime.time])
    _timedelta = Expr(Head.getattr, [datetime, datetime.timedelta])

    # magicgui-style input
    register_type(Enum, lambda e: symbol(e.value))
    register_type(Path, lambda e: f"r'{e}'")
    register_type(float, lambda e: str(round(e, 8)))

    try:
        from magicgui.widgets._concrete import ListDataView
    except ImportError:
        pass
    else:
        register_type(ListDataView, lambda e: list(e))

    register_type(
        datetime.datetime,
        lambda e: Expr.parse_call(
            _datetime, (e.year, e.month, e.day, e.hour, e.minute, e.second), {}
        ),
    )

    register_type(
        datetime.date,
        lambda e: Expr.parse_call(_date, (e.year, e.month, e.day), {}),
    )
    register_type(
        datetime.time, lambda e: Expr.parse_call(_time, (e.hour, e.minute), {})
    )
    register_type(
        datetime.timedelta,
        lambda e: Expr.parse_call(_timedelta, (e.days, e.seconds), {}),
    )


def _register_numpy_types():
    register_type(np.dtype, lambda e: e.name)
    register_type(np.integer, str)
    register_type(np.floating, lambda e: str(round(e, 8)))
    register_type(np.complex_, str)
    register_type(np.bool_, str)


def _register_napari_types():
    import napari
    from napari.layers import (
        Image,
        Labels,
        Layer,
        Points,
        Shapes,
        Surface,
        Tracks,
        Vectors,
    )
    from napari.types import (
        ImageData,
        LabelsData,
        PointsData,
        ShapesData,
        SurfaceData,
        TracksData,
        VectorsData,
    )

    _viewer_symbol = Symbol.var("viewer")
    _viewer_ = Mock(_viewer_symbol)

    register_type(napari.Viewer, lambda _: _viewer_symbol)
    register_type(Layer, lambda layer: _viewer_.layers[layer.name].expr)

    def find_name(data: np.ndarray, tp: type[Layer]):
        out = None
        if id(data) not in Symbol._variables:
            if viewer := napari.current_viewer():
                for layer in viewer.layers:
                    if not isinstance(layer, tp):
                        continue
                    if layer.data is data:
                        out = layer.name
                        break
        if out is None:
            from napari_macrokit._macrokit_ext import (
                _readable_symbol_from_object,
            )

            return _readable_symbol_from_object(data)
        return _viewer_.layers[out].data.expr

    def find_name_1(
        data: list[np.ndarray], tp: type[Shapes | Surface]
    ) -> str | None:
        out = None
        if id(data) not in Symbol._variables:
            if viewer := napari.current_viewer():
                for layer in viewer.layers:
                    if not isinstance(layer, tp):
                        continue
                    layer_data = layer.data
                    if len(layer_data) != len(data):
                        continue
                    if all(a is b for a, b in zip(layer_data, data)):
                        out = layer.name
                        break
        if out is None:
            from napari_macrokit._macrokit_ext import (
                _readable_symbol_from_object,
            )

            return _readable_symbol_from_object(data)
        return _viewer_.layers[out].data.expr

    register_new_type(
        ImageData,
        lambda data: find_name(data, Image),
    )
    register_new_type(
        LabelsData,
        lambda data: find_name(data, Labels),
    )
    register_new_type(
        PointsData,
        lambda data: find_name(data, Points),
    )
    register_new_type(
        ShapesData,
        lambda data: find_name_1(data, Shapes),
    )
    register_new_type(
        SurfaceData,
        lambda data: find_name_1(data, Surface),
    )
    register_new_type(
        TracksData,
        lambda data: find_name(data, Tracks),
    )
    register_new_type(
        VectorsData,
        lambda data: find_name(data, Vectors),
    )
