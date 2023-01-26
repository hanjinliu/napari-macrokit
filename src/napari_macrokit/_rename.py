from __future__ import annotations

from keyword import iskeyword
from typing import Any, Iterator, MutableMapping

import numpy as np
import pandas as pd
from macrokit import Symbol
from napari import layers, types


class PrefixInfo:
    def __init__(self, prefix: str, count: int = 0):
        self.prefix = prefix
        self.count = count

    def get_name(self) -> str:
        name = f"{self.prefix}{self.count}"
        self.count += 1
        return name


_DEFAULT_PREFIX: dict[str, str] = {
    np.ndarray: "arr",
    pd.DataFrame: "df",
    types.ImageData: "image",
    types.LabelsData: "labels",
    types.PointsData: "points",
    types.ShapesData: "shapes",
    types.SurfaceData: "surface",
    types.TracksData: "tracks",
    types.VectorsData: "vectors",
    types.LayerDataTuple: "layer_data_tuple",
    layers.Image: "layer_image",
    layers.Labels: "layer_labels",
    layers.Points: "layer_points",
    layers.Shapes: "layer_shapes",
    layers.Surface: "layer_surface",
    layers.Tracks: "layer_tracks",
    layers.Vectors: "layer_vectors",
}


class TypeInfoMap(MutableMapping[type, PrefixInfo]):
    def __init__(self) -> None:
        self._info_map: dict[type, PrefixInfo] = {}
        self._existing_prefixes: set[str] = set()

    def __getitem__(self, __key: str) -> PrefixInfo:
        return self._info_map[__key]

    def __setitem__(self, __key: type, __value: PrefixInfo) -> None:
        self._info_map[__key] = __value
        self._existing_prefixes.add(__value.prefix)

    def __delitem__(self, __key: type) -> None:
        info = self._info_map.pop(__key)
        self._existing_prefixes.discard(info)

    def __len__(self) -> int:
        return len(self._info_map)

    def __iter__(self) -> Iterator[type]:
        return super().__iter__()

    def coerce_prefix(self, pref: str) -> str:
        """Find an unique prefix string."""
        pref_stem = pref
        i = 0
        while pref in self._existing_prefixes:
            pref = f"{pref_stem}{i}_"
            i += 1
        return pref

    def new_prefix(self, objtype: type, default: str | None = None):
        """Make a new prefix valid as an identifier."""
        if default is None:
            default = _DEFAULT_PREFIX.get(objtype, None)
            if default is None:
                default = objtype.__name__.split(".")[-1].lower()
                # some type names are not valid as an identifier.
                if not default.isidentifier():
                    default = _remove_bad_chars(default)
        info = PrefixInfo(self.coerce_prefix(default))
        self[objtype] = info
        return info

    def decrement_prefix(self, objtype: type):
        info = self[objtype]
        info.count -= 1


class SymbolGenerator:
    def __init__(self):
        self._type_infos = TypeInfoMap()
        self._rename_map: dict[Symbol, Symbol] = {}
        self._last_renamed: tuple[Symbol, type] | None = None

    def generate(self, obj: object, objtype: type, old: Symbol) -> Symbol:
        """Generate an unique symbol."""
        if renamed := self._rename_map.get(old, None):
            return renamed
        info = self._type_infos.get(objtype, None)
        if info is None:
            info = self._type_infos.new_prefix(objtype)
        name = info.get_name()
        if iskeyword(name):
            out = self._rename_map[old] = old
        else:
            out = self._rename_map[old] = Symbol(name, id(obj))
        self._last_renamed = old, objtype
        return out

    def discard_last(self):
        sym, objtype = self._last_renamed
        self._rename_map.pop(sym)
        self._type_infos.decrement_prefix(objtype)

    def as_renamed_symbol(self, obj: Any) -> Symbol:
        old_sym = Symbol.asvar(obj)
        return self._rename_map.get(old_sym, old_sym)

    def rename_symbol(self, sym: Symbol):
        if isinstance(sym, Symbol):
            if sym in self._rename_map:
                return self._rename_map[sym]
            return sym
        raise TypeError(f"Expected Symbol, got {type(sym)}")

    def rename_or_generate(
        self, obj: object, objtype: type, old: Symbol
    ) -> Symbol:
        if isinstance(old, Symbol):
            if old in self._rename_map:
                return self._rename_map[old]
        return self.generate(obj, objtype, old)


def _remove_bad_chars(txt: str):
    table = str.maketrans(dict.fromkeys("[]{}().,+-*/=~^|;:@?<>!\"#$%&'", "_"))
    return txt.translate(table)
