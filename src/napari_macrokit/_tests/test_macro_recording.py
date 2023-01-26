import datetime

import napari
import numpy as np
import pytest
from macrokit import symbol

from napari_macrokit import symbol_of
from napari_macrokit._macrokit_ext import NapariMacro

from . import _utils


def test_function_call():
    macro = NapariMacro()

    @macro.record
    def func(a, b):
        return a + b

    assert len(macro) == 0
    func(1, 2)
    assert len(macro) == 1
    func(1, b=2)
    assert len(macro) == 2
    func(a=1, b=2)
    assert len(macro) == 3
    assert str(macro[0]).split(" = ")[1] == "func(1, 2)"
    assert str(macro[1]).split(" = ")[1] == "func(1, b=2)"
    assert str(macro[2]).split(" = ")[1] == "func(a=1, b=2)"


@pytest.mark.parametrize(
    "getter, adder",
    [
        (_utils.image_data, "add_image"),
        (_utils.labels_data, "add_labels"),
        (_utils.points_data, "add_points"),
        (_utils.shapes_data, "add_shapes"),
        (_utils.surface_data, "add_surface"),
        (_utils.tracks_data, "add_tracks"),
        (_utils.vectors_data, "add_vectors"),
    ],
)
def test_napari_type(make_napari_viewer, getter, adder):
    viewer = make_napari_viewer()
    data = getter()
    name = "test"
    layer = getattr(viewer, adder)(data, name=name)

    assert napari.current_viewer() is viewer

    sym = symbol(layer)
    assert str(sym) == f"viewer.layers[{name!r}]"


@pytest.mark.parametrize(
    "getter, adder, annotation",
    [
        (_utils.image_data, "add_image", "Image"),
        (_utils.labels_data, "add_labels", "Labels"),
        (_utils.points_data, "add_points", "Points"),
        (_utils.shapes_data, "add_shapes", "Shapes"),
        (_utils.surface_data, "add_surface", "Surface"),
        (_utils.tracks_data, "add_tracks", "Tracks"),
        (_utils.vectors_data, "add_vectors", "Vectors"),
    ],
)
def test_get_layer(make_napari_viewer, getter, adder, annotation):
    viewer = make_napari_viewer()
    macro = NapariMacro()

    data = getter()
    name = "test"
    layer = getattr(viewer, adder)(data, name=name)
    assert napari.current_viewer() is viewer

    @macro.record
    def func(data: annotation):
        pass

    assert len(macro) == 0
    func(layer)
    assert len(macro) == 1
    assert str(macro[0]) == f"func(viewer.layers[{name!r}])"


@pytest.mark.parametrize(
    "getter, adder, annotation",
    [
        (_utils.image_data, "add_image", "ImageData"),
        (_utils.labels_data, "add_labels", "LabelsData"),
        (_utils.points_data, "add_points", "PointsData"),
        (_utils.shapes_data, "add_shapes", "ShapesData"),
        (_utils.surface_data, "add_surface", "SurfaceData"),
        (_utils.tracks_data, "add_tracks", "TracksData"),
        (_utils.vectors_data, "add_vectors", "VectorsData"),
    ],
)
def test_get_layer_data(make_napari_viewer, getter, adder, annotation):
    viewer = make_napari_viewer()
    macro = NapariMacro()
    assert napari.current_viewer() is viewer

    data = getter()
    name = "test"
    layer = getattr(viewer, adder)(data, name=name)

    @macro.record
    def func(data: annotation):
        pass

    assert len(macro) == 0
    func(layer.data)
    assert len(macro) == 1
    assert str(macro[0]) == f"func(viewer.layers[{name!r}].data)"


def test_layer_data_tuple():
    from napari.types import ImageData, LayerDataTuple

    macro = NapariMacro()

    @macro.record
    def func(data: ImageData) -> LayerDataTuple:
        assert isinstance(data, np.ndarray)
        return data, "name", {}

    @macro.record
    def func2(data: ImageData) -> LayerDataTuple:
        assert isinstance(data, np.ndarray)
        return data, "name", {"blending": "additive"}

    data = _utils.image_data()
    out = func(data)
    func2(out[0])

    _data = symbol_of(data)
    assert str(macro[0]) == f"layer_data_tuple0 = func({_data})"
    assert str(macro[1]) == "layer_data_tuple1 = func2(layer_data_tuple0[0])"


def test_merge():
    macro = NapariMacro()

    @macro.record(merge=True)
    def func(a: int, b: bool) -> int:
        if b:
            return -a
        return a

    @macro.record(merge=True)
    def func2(t: int):
        return t + 1

    out = func(1, True)
    _int0 = symbol_of(out)
    assert len(macro) == 1 and str(macro[0]) == f"{_int0} = func(1, True)"
    func(2, True)
    assert len(macro) == 1 and str(macro[0]) == f"{_int0} = func(2, True)"
    result = func(2, False)
    assert len(macro) == 1 and str(macro[0]) == f"{_int0} = func(2, False)"
    out = func2(result)
    _int1 = symbol_of(out)
    assert len(macro) == 2
    assert str(macro[0]) == f"{_int0} = func(2, False)"
    assert str(macro[1]) == f"{_int1} = func2({_int0})"


@pytest.mark.parametrize(
    "val",
    [
        datetime.datetime(2023, 1, 26, 10, 44, 23),
        datetime.date(2023, 1, 26),
        datetime.time(10, 45, 23),
    ],
)
def test_consistency(val):
    assert symbol(val).eval() == val


@pytest.mark.parametrize("obj", [0, int])
def test_wrong_type(obj):
    macro = NapariMacro()
    with pytest.raises(TypeError):
        macro.record(obj)


def test_magicgui():
    macro = NapariMacro()

    @macro.magicgui
    def f(x: int):
        pass

    assert f.x.widget_type == "SpinBox"
    f()
    assert str(macro[0]) == "f(0)"


def test_magicgui_with_autocall():
    macro = NapariMacro()

    @macro.magicgui(auto_call=True)
    def f(x: int):
        pass

    assert f.x.widget_type == "SpinBox"
    assert f.call_button is None
    f(0)
    assert len(macro) == 1 and str(macro[0]) == "f(0)"
    f(1)
    assert len(macro) == 1 and str(macro[0]) == "f(1)"
