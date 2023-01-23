from __future__ import annotations

import sys

from macrokit import BaseMacro
from qtpy import QtCore, QtGui
from qtpy import QtWidgets as QtW
from qtpy.QtCore import Qt


class QLineNumberArea(QtW.QWidget):
    def __init__(self, editor: QCodeEditor):
        super().__init__(editor)
        self.editor = editor
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.editor._show_context_menu)

    def sizeHint(self):
        return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event: QtGui.QPaintEvent):
        self.editor.lineNumberAreaPaintEvent(event)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        editor = self.editor
        y = a0.pos().y()

        num, block = editor.blockAt(y)
        if num < 0:
            return
        cursor = editor.textCursor()
        cursor.setPosition(
            block.position(), QtGui.QTextCursor.MoveMode.MoveAnchor
        )
        cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)
        editor.setTextCursor(cursor)
        editor.horizontalScrollBar().setValue(0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.buttons() & Qt.MouseButton.LeftButton:
            y = a0.pos().y()
            num, block = self.editor.blockAt(y)
            if num < 0:
                return
            cursor = self.editor.textCursor()
            cursor.setPosition(
                block.position(), QtGui.QTextCursor.MoveMode.KeepAnchor
            )
            cursor.movePosition(
                QtGui.QTextCursor.MoveOperation.EndOfLine,
                QtGui.QTextCursor.MoveMode.KeepAnchor,
            )
            self.editor.setTextCursor(cursor)


class QCodeEditor(QtW.QPlainTextEdit):
    def __init__(
        self, parent: QtW.QWidget | None = None, macro: BaseMacro | None = None
    ):
        super().__init__(parent)
        if sys.platform == "win32":
            _font = "Consolas"
        elif sys.platform == "darwin":
            _font = "Menlo"
        else:
            _font = "Monospace"
        font = QtGui.QFont(_font, self.font().pointSize())
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

        self._line_number_area = QLineNumberArea(self)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_number_area_width()

        self.setTabSize(4)
        self.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.syntaxHighlight()

        self._macro = macro
        if macro is not None:
            self.connectMacro(macro)

        self.setMinimumHeight(100)

    @property
    def macro(self) -> BaseMacro:
        return self._macro

    def connectMacro(self, macro: BaseMacro):
        @macro.on_appended.append
        def _on_appended(expr):
            self.appendPlainText(str(expr))
            cursor = self.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)

        @macro.on_popped.append
        def _on_removed(expr):
            self.eraseLast()

        return self.setPlainText(str(macro))

    def tabSize(self):
        metrics = self.fontMetrics()
        return self.tabStopWidth() // metrics.width(" ")

    def setTabSize(self, size: int):
        metrics = self.fontMetrics()
        self.setTabStopWidth(size * metrics.width(" "))

    def lineNumberAreaWidth(self):
        count = max(1, self.blockCount())
        digits = len(str(count))
        space = 8 + self.fontMetrics().width("9") * digits
        return space

    def _update_line_number_area_width(self):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def _update_line_number_area(self, rect: QtCore.QRect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)

        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QtCore.QRect(
                cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()
            )
        )

    def _show_context_menu(self, pos: QtCore.QPoint):
        menu = QtW.QMenu(self.viewport())
        cursor = self.textCursor()
        new_pos = self.cursorForPosition(pos).position()
        if not cursor.selectionStart() <= new_pos <= cursor.selectionEnd():
            cursor.setPosition(new_pos, QtGui.QTextCursor.MoveMode.MoveAnchor)
        text = cursor.selectedText()
        has_selection = len(text) > 0

        # fmt: off
        menu.addAction("Select All", self.selectAll, "Ctrl+A")
        menu.addAction("Cut", self.cut, "Ctrl+X").setEnabled(has_selection)
        menu.addAction("Copy", self.copy, "Ctrl+C").setEnabled(has_selection)
        menu.addAction("Paste", self.paste, "Ctrl+V").setEnabled(not self.isReadOnly())
        menu.addSeparator()
        menu.addAction("Undo", self.undo, "Ctrl+Z").setEnabled(not self.isReadOnly())
        menu.addAction("Redo", self.redo, "Ctrl+Y").setEnabled(not self.isReadOnly())
        # fmt: on

        return menu.exec(self.mapToGlobal(pos))

    def _iter_visible_blocks(self, rect: QtCore.QRect = None):
        if rect is None:
            rect = self.viewport().rect()
        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = (
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and (top <= rect.bottom()):
            if block.isVisible() and (bottom >= rect.top()):
                yield block_num, block

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_num += 1

    def blockAt(self, y: int):
        for num, block in self._iter_visible_blocks():
            rect = self.blockBoundingGeometry(block)
            if rect.top() <= y <= rect.bottom():
                return num, block
        return -1, None

    def block(self, index: int) -> QtGui.QTextBlock | None:
        """Return the text block at index or None if not found."""
        for num, block in self._iter_visible_blocks():
            if num == index:
                return block
        return None

    def blocks(self, indices: list[int]) -> list[QtGui.QTextBlock]:
        blocks: list[QtGui.QTextBlock] = []
        indices = set(indices)
        for num, block in self._iter_visible_blocks():
            if num in indices:
                blocks.append(block)
        return blocks

    def lineNumberAreaPaintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self._line_number_area)

        bgcolor = self.palette().color(self.backgroundRole())
        color = QtGui.QColor(
            bgcolor.red() - 14, bgcolor.green() - 14, bgcolor.blue() + 14
        )
        painter.fillRect(event.rect(), color)

        height = self.fontMetrics().height()
        text_color = self.palette().color(self.foregroundRole())

        for num, block in self._iter_visible_blocks(event.rect()):
            painter.setPen(text_color)
            block_rect = self.blockBoundingGeometry(block)
            block_height = block_rect.height()
            draw_y = block_rect.top() + max(block_height - height, 0) / 2
            painter.drawText(
                0,
                int(draw_y),
                int(self._line_number_area.width() - 2),
                int(height),
                Qt.AlignmentFlag.AlignRight,
                str(num + 1),
            )

    def _highlight_current_line(self):
        extraSelections = []

        bgcolor = self.palette().color(self.parentWidget().backgroundRole())
        _highlight_color = QtGui.QColor(
            bgcolor.red() - 6, bgcolor.green() - 6, bgcolor.blue() + 6
        )

        if not self.isReadOnly():
            selection = QtW.QTextEdit.ExtraSelection()
            selection.format.setBackground(_highlight_color)
            selection.format.setProperty(
                QtGui.QTextFormat.Property.FullWidthSelection, True
            )
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def syntaxHighlight(self, lang: str = "python", theme: str = "default"):
        """Highlight syntax."""
        from superqt.utils import CodeSyntaxHighlight

        highlight = CodeSyntaxHighlight(self.document(), lang, theme=theme)
        self._highlight = highlight
        return None

    def selectedText(self) -> str:
        """Return selected string."""
        cursor = self.textCursor()
        return cursor.selectedText().replace("\u2029", "\n")

    def text(self) -> str:
        """Return the text."""
        return self.toPlainText().replace("\u2029", "\n")

    def setText(self, text: str):
        """Set the text."""
        self.setPlainText(text.replace("\n", "\u2029"))

    def eraseLast(self):
        """Erase the last line."""
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        self.setTextCursor(cursor)
