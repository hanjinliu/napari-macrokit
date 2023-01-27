from pytestqt.qtbot import QtBot
from qtpy.QtCore import QPoint, Qt

from napari_macrokit import available_keys, temp_macro
from napari_macrokit._widgets import QMacroView


def test_launch(qtbot: QtBot):
    wdt = QMacroView()
    qtbot.addWidget(wdt)
    with temp_macro() as macro:
        wdt._tabwidget.add_macro(macro, "x")
    assert wdt._tabwidget.widget(0).tabSize() == 4


def test_adding_macro_after_construction(qtbot: QtBot):
    wdt = QMacroView()
    qtbot.addWidget(wdt)
    assert wdt._tabwidget.count() == 0, available_keys()
    with temp_macro("m0") as macro0:
        assert wdt._tabwidget
        assert wdt._tabwidget.count() == 1
        macro0.append("a = 0")
        assert wdt._tabwidget.widget(0).text() == str(macro0)
        with temp_macro("m1") as macro1:
            assert wdt._tabwidget.count() == 2
            macro1.append("b = 0")
            assert wdt._tabwidget.widget(1).text() == str(macro1)


def test_construction_after_adding_macro(qtbot: QtBot):
    with temp_macro(["m0", "m1"]) as macros:
        m0, m1 = macros
        m0.append("a = 0")
        m1.append("b = 0")
        wdt = QMacroView()
        qtbot.addWidget(wdt)
        assert wdt._tabwidget.count() == 2
        assert wdt._tabwidget.widget(0).text() == str(m0)
        assert wdt._tabwidget.widget(1).text() == str(m1)


def test_erase_last(qtbot: QtBot):
    with temp_macro("m0") as macro:
        wdt = QMacroView()
        qtbot.addWidget(wdt)

        @macro.magicgui(auto_call=True)
        def f(x: int):
            pass

        f()
        f(1)
        assert len(macro) == 1
        assert wdt._tabwidget.count() == 1
        assert wdt._tabwidget.widget(0).text() == str(macro)


def test_duplicate(qtbot: QtBot):
    wdt = QMacroView()
    qtbot.addWidget(wdt)
    with temp_macro("m0") as macro:
        macro.append("a = 0")
        wdt._tabwidget.add_duplicate(0)


def test_context_menu(qtbot: QtBot):
    with temp_macro("m0"):
        wdt = QMacroView()
        qtbot.addWidget(wdt)
        editor = wdt._tabwidget.widget(0)
        editor._show_context_menu(QPoint(2, 2))


def test_left_area(qtbot: QtBot):
    with temp_macro("m0"):
        wdt = QMacroView()
        qtbot.addWidget(wdt)
        editor = wdt._tabwidget.widget(0)
        qtbot.mousePress(
            editor._line_number_area,
            Qt.MouseButton.LeftButton,
            pos=QPoint(2, 2),
        )
        qtbot.mouseMove(editor._line_number_area, pos=QPoint(2, 5))
