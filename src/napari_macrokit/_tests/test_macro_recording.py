import napari
import numpy as np
import pytest
from macrokit import symbol

from napari_macrokit._macrokit_ext import NapariMacro, SymbolGen

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
    out2 = func2(out[0])

    _data = SymbolGen.as_renamed_symbol(data)
    _out = SymbolGen.as_renamed_symbol(out)
    _out2 = SymbolGen.as_renamed_symbol(out2)
    assert str(macro[0]) == f"layer_data_tuple0 = func({_data})"
    assert str(macro[1]) == f"layer_data_tuple1 = func2(layer_data_tuple0[0])"
