import re
from typing import Dict

from PySide6.QtCore import Qt, Signal, QTimer, QRect
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QPainter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit

from app.highlighter import MarkdownHighlighter
from app.parser import DocumentParser
from app.widgets.line_number_area import LineNumberArea


class PracticeEditor(QTextEdit):
    practiceClicked = Signal(str)
    fileClicked = Signal(str)
    autocompleteRequested = Signal(str, int, str)
    documentChanged = Signal()
    ctrlFPressed = Signal()
    ctrlEPressed = Signal()
    ctrlNPressed = Signal()
    f5Pressed = Signal()
    findRequested = Signal()

    _practice_link_pattern = re.compile(r'^#\s+(.+)$')
    _quoted_file_pattern = re.compile(r"""@['"]([^'"]+\.\w+)['"]""")
    _simple_file_pattern = re.compile(r'@(\S+\.\w+)')
    _task_indent_pattern = re.compile(r'^(\s*)-\s+')
    _practice_line_pattern = re.compile(r'^#\s+')
    _task_line_pattern = re.compile(r'^(\s*)-\s+(?:\[x\]\s+)?(.+)$')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_font()
        self._search_bar = None
        self._search_input = None
        self._replace_input = None
        self._search_count = None
        self._search_highlights = []
        self._last_search = ""
        self.line_number_area = LineNumberArea(self)
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.verticalScrollBar().valueChanged.connect(self.update_line_number_area_scroll)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.setTabStopDistance(40)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.highlighter = MarkdownHighlighter(self.document())
        self.last_saved_content = ""
        self.autocomplete_active = False
        self.setMouseTracking(True)
        self._cached_practice_name = ""
        self._cached_block_number = -1

    def _setup_font(self):
        preferred_fonts = ["JetBrains Mono", "Cascadia Code", "Fira Code", "Consolas"]
        font = QFont()
        for font_name in preferred_fonts:
            font.setFamily(font_name)
            if QFontDatabase.hasFamily(font_name):
                break
        font.setPointSize(11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

    def line_number_area_width(self):
        digits = len(str(max(1, self.document().blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area_scroll(self, value):
        self.line_number_area.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
        if self._search_bar and self._search_bar.isVisible():
            self._search_bar.setGeometry(0, self.height() - 40, self.width(), 40)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)

        if self.palette().window().color().lightness() > 128:
            painter.fillRect(event.rect(), QColor("#F5F5F5"))
            painter.setPen(QColor("#999999"))
        else:
            painter.fillRect(event.rect(), QColor("#2D2D2D"))
            painter.setPen(QColor("#666666"))

        block = self.document().begin()
        block_number = 0

        while block.isValid():
            block_cursor = QTextCursor(block)
            rect = self.cursorRect(block_cursor)

            if rect.bottom() >= event.rect().top() and rect.top() <= event.rect().bottom():
                if block.isVisible():
                    number = str(block_number + 1)
                    painter.drawText(
                        0, rect.top(),
                        self.line_number_area.width() - 5,
                        self.fontMetrics().height(),
                        Qt.AlignRight, number
                    )

            block = block.next()
            block_number += 1

    def highlight_current_line(self):
        pass

    def update_theme(self, theme: Dict):
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['editor_background']};
                color: {theme['editor_text']};
                border: none;
                padding: 16px;
                line-height: 1.6;
                selection-background-color: {theme['accent_light']};
            }}
        """)
        self.highlighter.update_theme(theme)

    def _get_link_info(self, text, pos_in_block):
        if text.startswith('# '):
            name = text[2:].strip()
            if 2 <= pos_in_block < 2 + len(name):
                return ('practice', name)
            return (None, None)
        for match in self._quoted_file_pattern.finditer(text):
            if match.start() <= pos_in_block < match.end():
                return ('file', match.group(1))
        for match in self._simple_file_pattern.finditer(text):
            if match.start() <= pos_in_block < match.end():
                return ('file', match.group(1))
        return (None, None)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        cursor = self.cursorForPosition(pos)
        block = cursor.block()
        link_type, _ = self._get_link_info(block.text(), cursor.positionInBlock())
        self.viewport().setCursor(Qt.PointingHandCursor if link_type else Qt.IBeamCursor)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            cursor = self.cursorForPosition(pos)
            block = cursor.block()
            link_type, value = self._get_link_info(block.text(), cursor.positionInBlock())
            if link_type == 'practice':
                self.practiceClicked.emit(value)
                return
            elif link_type == 'file':
                self.fileClicked.emit(value)
                return
        super().mousePressEvent(event)

    def get_current_practice_name(self) -> str:
        cursor = self.textCursor()
        block = cursor.block()
        block_num = block.blockNumber()
        if block_num == self._cached_block_number and self._cached_practice_name:
            return self._cached_practice_name
        match = self._practice_link_pattern.match(block.text().strip())
        if match:
            name = match.group(1).strip()
            self._cached_practice_name = name
            self._cached_block_number = block_num
            return name
        block = block.previous()
        while block.isValid():
            match = self._practice_link_pattern.match(block.text().strip())
            if match:
                name = match.group(1).strip()
                self._cached_practice_name = name
                self._cached_block_number = block.blockNumber()
                return name
            block = block.previous()
        return ""

    def keyPressEvent(self, event):
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        pos_in_block = cursor.positionInBlock()

        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            if event.key() == Qt.Key_Up:
                self._move_line(-1)
                return
            elif event.key() == Qt.Key_Down:
                self._move_line(1)
                return

        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_D:
                self._toggle_task_done()
                return
            elif event.key() == Qt.Key_F:
                self._show_search_bar(replace=False)
                self.findRequested.emit()
                return
            elif event.key() == Qt.Key_H:
                self._show_search_bar(replace=True)
                return
            elif event.key() == Qt.Key_E:
                self.ctrlEPressed.emit()
                return
            elif event.key() == Qt.Key_N:
                self.ctrlNPressed.emit()
                return

        if event.key() == Qt.Key_F5:
            self.f5Pressed.emit()
            return

        if event.text() == '#' and pos_in_block == 0 and not self.autocomplete_active:
            super().keyPressEvent(event)
            QTimer.singleShot(0, lambda: self.autocompleteRequested.emit('practice', cursor.position(), ""))
            return

        if event.text() == '@' and not self.autocomplete_active:
            super().keyPressEvent(event)
            practice_name = self.get_current_practice_name()
            QTimer.singleShot(0, lambda: self.autocompleteRequested.emit('file', cursor.position(), practice_name))
            return

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self._practice_line_pattern.match(text):
                super().keyPressEvent(event)
                self.textCursor().insertText("- ")
                return
            task_match = self._task_indent_pattern.match(text)
            if task_match:
                indent = task_match.group(1)
                super().keyPressEvent(event)
                self.textCursor().insertText(f"{indent}- ")
                return

        if event.key() == Qt.Key_Tab:
            if cursor.hasSelection():
                self._indent_selection(1)
                return
            task_match = self._task_indent_pattern.match(text)
            if task_match:
                cursor.movePosition(QTextCursor.StartOfBlock)
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cursor.insertText("  " + text)
                return

        if event.key() == Qt.Key_Backtab:
            if cursor.hasSelection():
                self._indent_selection(-1)
                return
            task_match = re.match(r'^(\s+)-\s+', text)
            if task_match and len(task_match.group(1)) >= 2:
                cursor.movePosition(QTextCursor.StartOfBlock)
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                cursor.insertText(text[2:])
                return

        super().keyPressEvent(event)
        if not self.autocomplete_active:
            QTimer.singleShot(100, lambda: self.documentChanged.emit())

    def _show_search_bar(self, replace=False):
        if self._search_bar:
            self._search_bar.show()
            if self._replace_input:
                self._replace_input.setVisible(replace)
            for widget in self._search_bar.findChildren(QPushButton):
                if widget.text() in ("Sostituisci", "Tutti"):
                    widget.setVisible(replace)
            self._search_input.setFocus()
            self._search_input.selectAll()
            return

        self._search_bar = QFrame(self)
        self._search_bar.setObjectName("searchBar")
        self._search_bar.setStyleSheet("""
            QFrame#searchBar {
                background-color: palette(window);
                border-top: 1px solid palette(mid);
            }
        """)
        layout = QHBoxLayout(self._search_bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Cerca...")
        self._search_input.textChanged.connect(self._do_find)
        self._search_input.returnPressed.connect(self._find_next)
        layout.addWidget(self._search_input)

        self._search_count = QLabel("")
        self._search_count.setStyleSheet("padding: 0 8px;")
        layout.addWidget(self._search_count)

        prev_btn = QPushButton("↑")
        prev_btn.setFixedSize(28, 28)
        prev_btn.clicked.connect(self._find_prev)
        layout.addWidget(prev_btn)

        next_btn = QPushButton("↓")
        next_btn.setFixedSize(28, 28)
        next_btn.clicked.connect(self._find_next)
        layout.addWidget(next_btn)

        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("Sostituisci...")
        self._replace_input.setVisible(replace)
        layout.addWidget(self._replace_input)

        replace_btn = QPushButton("Sostituisci")
        replace_btn.setVisible(replace)
        replace_btn.clicked.connect(self._replace_current)
        layout.addWidget(replace_btn)

        replace_all_btn = QPushButton("Tutti")
        replace_all_btn.setVisible(replace)
        replace_all_btn.clicked.connect(self._replace_all)
        layout.addWidget(replace_all_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self._hide_search_bar)
        layout.addWidget(close_btn)

        self._search_bar.setGeometry(0, self.height() - 40, self.width(), 40)
        self._search_bar.show()
        self._search_input.setFocus()

    def _hide_search_bar(self):
        if self._search_bar:
            self._search_bar.hide()
        self.setFocus()

    def _clear_search_highlights(self):
        self._search_highlights = []
        self.setExtraSelections([])

    def _do_find(self, text):
        self._last_search = text
        self._clear_search_highlights()
        if not text:
            if self._search_count:
                self._search_count.setText("")
            return

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#FFEB3B"))
        selections = []
        count = 0

        while self.find(text):
            count += 1
            extra = QTextEdit.ExtraSelection()
            extra.format = fmt
            extra.cursor = self.textCursor()
            selections.append(extra)

        self.setTextCursor(cursor)
        self.setExtraSelections(selections)
        self._search_highlights = selections
        if self._search_count:
            self._search_count.setText(f"{count} risultati" if count else "Nessun risultato")

    def _find_next(self):
        if not self._last_search:
            return
        if not self.find(self._last_search):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.setTextCursor(cursor)
            self.find(self._last_search)

    def _find_prev(self):
        if not self._last_search:
            return
        if not self.find(self._last_search, QTextDocument.FindBackward):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            self.find(self._last_search, QTextDocument.FindBackward)

    def _replace_current(self):
        if not self._last_search or not self._replace_input:
            return
        cursor = self.textCursor()
        if cursor.hasSelection() and cursor.selectedText().lower() == self._last_search.lower():
            cursor.insertText(self._replace_input.text())
        self._do_find(self._search_input.text() if self._search_input else self._last_search)
        self._find_next()

    def _replace_all(self):
        if not self._last_search or not self._replace_input:
            return
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.setTextCursor(cursor)
        count = 0
        while self.find(self._last_search):
            self.textCursor().insertText(self._replace_input.text())
            count += 1
        if self._search_count:
            self._search_count.setText(f"{count} sostituzioni")
        self._do_find(self._search_input.text() if self._search_input else self._last_search)

    def _toggle_task_done(self):
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        new_text = DocumentParser.toggle_task_status(text)
        if new_text != text:
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            cursor.insertText(new_text)
            self.documentChanged.emit()

    def _move_line(self, direction: int):
        """Sposta la riga corrente su/giù scambiandola con quella adiacente."""
        cursor = self.textCursor()
        block = cursor.block()

        if direction < 0:
            prev_block = block.previous()
            if not prev_block.isValid():
                return

            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
            current_text = cursor.selectedText()

            prev_cursor = QTextCursor(prev_block)
            prev_cursor.movePosition(QTextCursor.StartOfBlock)
            prev_cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
            prev_text = prev_cursor.selectedText()

            cursor.removeSelectedText()
            prev_cursor.removeSelectedText()

            insert_cursor = QTextCursor(prev_block)
            insert_cursor.movePosition(QTextCursor.StartOfBlock)
            insert_cursor.insertText(current_text)
            insert_cursor.insertText(prev_text)

            self.setTextCursor(QTextCursor(prev_block))

        else:
            next_block = block.next()
            if not next_block.isValid():
                return

            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
            current_text = cursor.selectedText()

            next_cursor = QTextCursor(next_block)
            next_cursor.movePosition(QTextCursor.StartOfBlock)
            next_cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
            next_text = next_cursor.selectedText()

            next_cursor.removeSelectedText()
            cursor.removeSelectedText()

            insert_cursor = QTextCursor(block)
            insert_cursor.movePosition(QTextCursor.StartOfBlock)
            insert_cursor.insertText(next_text)
            insert_cursor.insertText(current_text)

            self.setTextCursor(QTextCursor(next_block))

        self.documentChanged.emit()

    def _indent_selection(self, direction: int):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        start_block = cursor.block()
        cursor.setPosition(end)
        end_block = cursor.block()
        cursor.beginEditBlock()
        block = start_block
        while True:
            text = block.text()
            task_match = self._task_line_pattern.match(text)
            if task_match:
                block_cursor = QTextCursor(block)
                block_cursor.movePosition(QTextCursor.StartOfBlock)
                block_cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                if direction > 0:
                    block_cursor.insertText("  " + text)
                else:
                    if text.startswith("  "):
                        block_cursor.insertText(text[2:])
            if block == end_block:
                break
            block = block.next()
            if not block.isValid():
                break
        cursor.endEditBlock()
        self.documentChanged.emit()
