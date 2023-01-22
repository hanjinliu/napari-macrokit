from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtWidgets as QtW

from ._code_editor import QCodeEditor

if TYPE_CHECKING:
    from napari_macrokit._macrokit_ext import NapariMacro


class QMacroView(QtW.QWidget):
    _current_widget = None

    def __init__(self, parent: QtW.QWidget | None = None):
        super().__init__(parent)
        _layout = QtW.QVBoxLayout()
        self.setLayout(_layout)
        self._toolbar = QtW.QToolBar()
        self._tabwidget = QMacroViewTabWidget(self)

        _layout.addWidget(self._toolbar)
        _layout.addWidget(self._tabwidget)

        self._toolbar.addAction(
            "Duplicate",
            lambda: self._tabwidget.add_duplicate(
                self._tabwidget.currentIndex()
            ),
        )
        self._toolbar.addAction(
            "Close",
            lambda: self._tabwidget.remove_editor(
                self._tabwidget.currentIndex()
            ),
        )

        self.__class__._current_widget = self

    @classmethod
    def current(self) -> QMacroView:
        return self._current_widget


class QMacroViewTabWidget(QtW.QTabWidget):
    def __init__(self, parent: QtW.QWidget | None = None):
        super().__init__(parent)

        self.add_all_editors()

    def add_macro(self, macro: NapariMacro, name: str):
        editor = QCodeEditor(parent=self, macro=macro)
        editor.setReadOnly(True)
        self.addTab(editor, name)
        self.setCurrentIndex(self.count() - 1)
        return editor

    def add_editor(self, name: str = "main"):
        from napari_macrokit import get_macro

        macro = get_macro(name)
        return self.add_macro(macro, name)

    def add_all_editors(self):
        from napari_macrokit import list_macro_keys

        existing_names = {self.tabText(i) for i in range(self.count())}
        for name in list_macro_keys():
            if name not in existing_names:
                self.add_editor(name)

    def add_duplicate(self, index: int):
        name = self.tabText(index) + "-copy"
        editor = QCodeEditor(parent=self)
        editor.setPlainText(self.widget(index).toPlainText())
        return self.addTab(editor, name)

    def remove_editor(self, index: int):
        if self.widget(index).macro is None:
            return self.removeTab(index)

    if TYPE_CHECKING:

        def widget(self, index: int) -> QCodeEditor:
            ...
