__version__ = "0.0.1"
from ._register_types import register_all

register_all()

del register_all

from .core import get_macro, record, recordable_magicgui

__all__ = ["get_macro", "record", "recordable_magicgui"]
