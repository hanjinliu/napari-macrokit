# napari-macrokit

[![License BSD-3](https://img.shields.io/pypi/l/napari-macrokit.svg?color=green)](https://github.com/hanjinliu/napari-macrokit/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-macrokit.svg?color=green)](https://pypi.org/project/napari-macrokit)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-macrokit.svg?color=green)](https://python.org)
[![tests](https://github.com/hanjinliu/napari-macrokit/workflows/tests/badge.svg)](https://github.com/hanjinliu/napari-macrokit/actions)
[![codecov](https://codecov.io/gh/hanjinliu/napari-macrokit/branch/main/graph/badge.svg)](https://codecov.io/gh/hanjinliu/napari-macrokit)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-macrokit)](https://napari-hub.org/plugins/napari-macrokit)

Executable script generation for napari plugins.

This napari plugin aims at making image analysis reproducible with arbitrary input/output types.


## Example

Suppose you have two modules that uses `napari-macrokit`.

```python
# napari_module_0.py

from napari.types import ImageData
from scipy import ndimage as ndi
from napari_macrokit import get_macro

macro = get_macro("napari-module-0")

@macro.record
def gaussian_filter(image: ImageData, sigma: float) -> ImageData:
    return ndi.gaussian_filter(image, sigma=sigma)

@macro.record
def threshold(image: ImageData, value: float) -> ImageData:
    return image > value
```

```python
# napari_module_1.py

from napari.types import ImageData
import numpy as np
from napari_macrokit import get_macro
macro = get_macro("napari-module-1")

@macro.record
def estimate_background(image: ImageData) -> float:
    return np.percentile(image, 10.0)

```

```python
import numpy as np
from napari_macrokit import get_merged_macro
from napari_module_0 import gaussian_filter, threshold
from napari_module_1 import estimate_background

# global_macro will record all the macro available at this point
global_macro = get_merged_macro()

# start image analysis!
image = np.random.random((100, 100))

out = gaussian_filter(image, 2.0)
thresh = estimate_background(out)
binary = threshold(out, thresh)
```

---------------------------------

This [napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template.

## Installation

You can install `napari-macrokit` via [pip]:

    pip install napari-macrokit



To install latest development version :

    pip install git+https://github.com/hanjinliu/napari-macrokit.git


## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-macrokit" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/hanjinliu/napari-macrokit/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
