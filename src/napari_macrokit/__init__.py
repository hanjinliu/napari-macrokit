__version__ = "0.0.1"
from ._register_types import register_all

register_all()

del register_all

from ._widget import QCodeEditor
from .core import get_macro

__all__ = ["get_macro", "QCodeEditor"]
