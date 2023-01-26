from typing import ForwardRef, List

import napari
import pytest
from napari.layers import Image
from napari.types import ImageData
from typing_extensions import Annotated

from napari_macrokit._type_resolution import resolve_single_type


@pytest.mark.parametrize(
    "tp, expected",
    [
        (int, int),
        ("int", int),
        (ImageData, ImageData),
        ("ImageData", ImageData),
        ("napari.types.ImageData", ImageData),
        (Image, Image),
        ("Image", Image),
        ("napari.layers.Image", Image),
        (napari.Viewer, napari.Viewer),
        ("napari.Viewer", napari.Viewer),
        (Annotated[int, {"a": 1}], int),
        (Annotated["int", {"a": 1}], int),
    ],
)
def test_type_resolution(tp, expected):
    assert resolve_single_type(tp) == expected


@pytest.mark.parametrize(
    "tp, expected",
    [
        (ForwardRef("int"), int),
        (ForwardRef("ImageData"), ImageData),
        (ForwardRef("napari.types.ImageData"), ImageData),
        (ForwardRef("Image"), Image),
        (ForwardRef("napari.layers.Image"), Image),
        (ForwardRef("napari.Viewer"), napari.Viewer),
        (List[ForwardRef("napari.layers.Image")], List[Image]),
    ],
)
def test_forwardref(tp, expected):
    assert resolve_single_type(tp) == expected
