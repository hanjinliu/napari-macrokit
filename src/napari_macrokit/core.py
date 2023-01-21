from __future__ import annotations

from typing import Callable

from magicgui import magicgui

from ._macrokit_ext import NapariMacro

_MACRO = NapariMacro()


def get_macro():
    return _MACRO


def record(obj):
    return _MACRO.record(obj)


def recordable_magicgui(
    function: Callable | None = None,
    *,
    layout: str = "vertical",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: bool = False,
    persist: bool = False,
    raise_on_unknown: bool = False,
    **param_options: dict,
):
    def wrapper(func):
        mfunc = record(func)
        return magicgui(
            mfunc,
            layout=layout,
            scrollable=scrollable,
            labels=labels,
            tooltips=tooltips,
            call_button=call_button,
            auto_call=auto_call,
            result_widget=result_widget,
            main_window=main_window,
            persist=persist,
            raise_on_unknown=raise_on_unknown,
            **param_options,
        )

    return wrapper if function is None else wrapper(function)
