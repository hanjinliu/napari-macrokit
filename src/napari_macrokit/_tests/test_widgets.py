from napari_macrokit import available_keys, temp_macro
from napari_macrokit._widgets import QMacroView


def test_launch():
    wdt = QMacroView()
    wdt.show()
    wdt.close()


def test_adding_macro_after_construction():
    wdt = QMacroView()
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


def test_construction_after_adding_macro():
    with temp_macro(["m0", "m1"]) as macros:
        m0, m1 = macros
        m0.append("a = 0")
        m1.append("b = 0")
        wdt = QMacroView()
        assert wdt._tabwidget.count() == 2
        assert wdt._tabwidget.widget(0).text() == str(m0)
        assert wdt._tabwidget.widget(1).text() == str(m1)
