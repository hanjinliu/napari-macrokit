from pathlib import Path

import napari
import numpy as np
import pandas as pd
from magicgui.widgets import Container, PushButton, Table
from napari.types import ImageData, LabelsData

from napari_macrokit import get_macro

macro = get_macro("regionprops")


@macro.magicgui
def read_image(path: Path) -> ImageData:
    from skimage import io

    return io.imread(path)


@macro.magicgui(
    auto_call=True, sigma={"widget_type": "FloatSlider", "max": 10}
)
def gaussian_filter(img: ImageData, sigma=1.0) -> ImageData:
    from scipy import ndimage as ndi

    return ndi.gaussian_filter(img, sigma)


@macro.magicgui(
    auto_call=True, thresh={"widget_type": "FloatSlider", "max": 1.0}
)
def threshold(img: ImageData, thresh: float = 0.5) -> LabelsData:
    from skimage.measure import label

    thr = np.percentile(img, thresh * 100)
    return label(img > thr)


@macro.magicgui
def calculate_mean(img: ImageData, label: LabelsData):
    from skimage.measure import regionprops_table

    df = regionprops_table(
        label,
        img,
        properties=("intensity_mean", "intensity_max", "intensity_min"),
    )
    table = Table(value=df)
    viewer.window.add_dock_widget(table, name="result")
    return pd.DataFrame(df)


if __name__ == "__main__":
    viewer = napari.Viewer()

    viewer.window.add_dock_widget(read_image)
    btn0 = PushButton(text="Gaussian filter")
    btn1 = PushButton(text="Threshold")
    btn2 = PushButton(text="regiongprops")

    cnt = Container(widgets=[btn0, btn1, btn2], layout="horizontal")

    viewer.window.add_dock_widget(cnt)

    btn0.changed.connect(
        lambda: viewer.window.add_dock_widget(gaussian_filter)
    )
    btn1.changed.connect(lambda: viewer.window.add_dock_widget(threshold))
    btn2.changed.connect(lambda: viewer.window.add_dock_widget(calculate_mean))

    napari.run()
