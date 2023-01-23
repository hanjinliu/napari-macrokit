import numpy as np
from napari.types import ImageData
from scipy import ndimage as ndi

from napari_macrokit import collect_macro, get_macro


def module_0():
    macro = get_macro("napari-module-0")

    @macro.record
    def gaussian_filter(image: ImageData, sigma: float) -> ImageData:
        return ndi.gaussian_filter(image, sigma=sigma)

    @macro.record
    def threshold(image: ImageData, value: float) -> ImageData:
        return image > value

    return gaussian_filter, threshold


def module_1():
    macro = get_macro("napari-module-1")

    @macro.record
    def estimate_background(image: ImageData) -> float:
        return np.percentile(image, 10.0)

    return estimate_background


if __name__ == "__main__":
    # import modules
    gaussian_filter, threshold = module_0()
    estimate_background = module_1()

    # global_macro will record all the macro available at this point
    global_macro = collect_macro()

    image = np.random.random((100, 100))  # sample image
    out = gaussian_filter(image, 2.0)
    thresh = estimate_background(out)
    binary = threshold(out, thresh)

    print("Done! Recorded macro is following:")
    print(global_macro)
