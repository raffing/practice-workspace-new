from typing import Dict
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListView, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, QEvent, QPropertyAnimation, QEasingCurve, QStringListModel
from PySide6.QtGui import QColor

class CommandPalette(QDialog):
    commandExecuted = Signal(str, str)
    
    COMMANDS = [
        {"id": "open_practice", "label": "🔍 Apri pratica...", "shortcut": "Ctrl+P"},
        {"id": "open_file", "label": "📄 Apri file...", "shortcut": ""},
        {"id": "new_practice", "label": "➕ Nuova pratica", "shortcut": "Ctrl+N"},
        {"id": "new_task", "label": "✅ Nuovo task", "shortcut": ""},
        {"id": "toggle_theme", "label": "🎨 Cambia tema", "shortcut": ""},
        {"id": "save", "label": "💾 Salva", "shortcut": "Ctrl+S"},
        {"id": "focus_filter", "label": "🔍 Vai al filtro", "shortcut": "Ctrl+F"},
        {"id": "focus_editor", "label": "✏️ Vai all'editor", "shortcut": "Ctrl+E"},
        {"id": "refresh", "label": "🔄 Aggiorna albero", "shortcut": "F5"},
    ]
    
    def __init__(self, parent=None, theme: Dict = None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.theme = theme or {}
        self._setup_ui()
        self._add_shadow()
        self._fade_in()
    
    def _add_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(self.theme.get('shadow_color', QColor(0, 0, 0, 40)))
        self.setGraphicsEffect(shadow)
    
    def _fade_in(self):
        self.setWindowOpacity(0.0)
        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(100)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()
    
    def _setup_ui(self):
        t = self.theme
        self.setStyleSheet(f"""
            QDialog {{
                border: 2px solid {t.get('accent', '#1976D2')};
                border-radius: 12px;
                background-color: {t.get('background', '#FFFFFF')};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Digita un comando...")
        layout.addWidget(self.search_edit)
        self.list_view = QListView()
        self.model = QStringListModel([c['label'] for c in self.COMMANDS])
        self.list_view.setModel(self.model)
        if self.model.rowCount() > 0:
            self.list_view.setCurrentIndex(self.model.index(0, 0))
        layout.addWidget(self.list_view)
        self.search_edit.textChanged.connect(self._on_filter)
        self.search_edit.installEventFilter(self)
        self.list_view.installEventFilter(self)
        self.setFixedSize(550, 400)
    
    def _on_filter(self, text: str):
        if not text:
            self.model.setStringList([c['label'] for c in self.COMMANDS])
        else:
            text_lower = text.lower()
            filtered = [c['label'] for c in self.COMMANDS if text_lower in c['label'].lower()]
            self.model.setStringList(filtered)
        if self.model.rowCount() > 0:
            self.list_view.setCurrentIndex(self.model.index(0, 0))
    
    def _execute_current(self):
        current_index = self.list_view.currentIndex()
        if not current_index.isValid():
            return
        label = self.model.data(current_index, Qt.DisplayRole)
        for cmd in self.COMMANDS:
            if cmd['label'] == label:
                self.commandExecuted.emit(cmd['id'], "")
                break
        self.accept()
    
    def eventFilter(self, obj, event):
        if event.type() != QEvent.KeyPress:
            return super().eventFilter(obj, event)
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self._execute_current()
            return True
        if key == Qt.Key_Escape:
            self.reject()
            return True
        if key == Qt.Key_Down and obj == self.search_edit:
            if self.model.rowCount() > 0:
                self.list_view.setCurrentIndex(self.model.index(0, 0))
                self.list_view.setFocus()
            return True
        return super().eventFilter(obj, event)
    
    def show_centered(self):
        parent = self.parent()
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.center().x() - self.width() // 2
            y = parent_geo.top() + 100
            self.move(x, y)
        self.show()
        self.search_edit.setFocus()