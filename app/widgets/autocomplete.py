from typing import List, Dict, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QLabel, QListView,
    QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtCore import (
    Qt, Signal, QEvent, QPropertyAnimation, QEasingCurve,
    QStringListModel
)
from PySide6.QtGui import QColor
from .file_navigator import FileSystemNavigator, FileSystemListModel

class AutocompletePopup(QDialog):
    # Ora emettiamo (name, full_path) dove full_path è un Path o None
    itemSelected = Signal(str, object)

    def __init__(
        self,
        items: List[str],
        parent=None,
        workspace_path: Path = None,
        show_files: bool = True,
        show_directories: bool = True,
        start_path: Path = None,
        theme: Dict = None
    ):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.workspace_path = workspace_path
        self.navigator: Optional[FileSystemNavigator] = None
        self.is_file_navigation = False
        self.theme = theme or {}

        if workspace_path and (not items or items == ["file_navigation"]):
            self.navigator = FileSystemNavigator(
                workspace_path,
                show_files=show_files,
                show_directories=show_directories,
                start_path=start_path
            )
            self.is_file_navigation = True
            self.all_items = []
        else:
            self.all_items = items.copy() if items else []

        self._setup_ui()
        self.setFocusPolicy(Qt.StrongFocus)
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
        self._animation.setDuration(150)
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

        self.header = QLabel()
        self.header.setStyleSheet(
            f"color: {t.get('text_secondary', '#666')}; font-size: 10px; "
            f"padding: 6px 8px; "
            f"background-color: {t.get('surface', '#F5F5F5')}; "
            f"border-radius: 6px; font-weight: bold;"
        )
        self._update_header()
        layout.addWidget(self.header)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(
            "Filtra... ↑↓ naviga | → entra | ← indietro | Invio seleziona | Esc chiudi"
        )
        layout.addWidget(self.filter_edit)

        self.list_view = QListView()
        self.list_view.setStyleSheet(f"""
            QListView {{
                border: 1px solid {t.get('border', '#E0E0E0')};
                border-radius: 8px;
                font-size: 13px;
                min-height: 200px;
                background-color: {t.get('background', '#FFFFFF')};
                color: {t.get('text', '#212121')};
            }}
            QListView::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {t.get('border', '#E0E0E0')};
            }}
            QListView::item:selected {{
                background-color: {t.get('surface_selected', '#E3F2FD')};
                color: {t.get('accent', '#1976D2')};
            }}
            QListView::item:hover {{
                background-color: {t.get('surface_hover', '#E8E8E8')};
            }}
        """)

        if self.is_file_navigation:
            self.model = FileSystemListModel()
        else:
            self.model = QStringListModel(self.all_items)

        self.list_view.setModel(self.model)

        if self.is_file_navigation:
            self._populate_items()
        if self.model.rowCount() > 0:
            self.list_view.setCurrentIndex(self.model.index(0, 0))

        layout.addWidget(self.list_view)

        self.filter_edit.textChanged.connect(self._on_filter_text_changed)
        self.filter_edit.installEventFilter(self)
        self.list_view.installEventFilter(self)

        self.setMinimumSize(450, 350)
        self.resize(500, 400)

    def _update_header(self):
        if self.is_file_navigation and self.navigator:
            rel_path = self.navigator.get_relative_path()
            type_text = (
                "Pratiche"
                if (self.navigator.show_directories and not self.navigator.show_files)
                else "File e Cartelle"
            )
            self.header.setText(
                f"📂 {rel_path} | {type_text} | "
                "↑↓ Naviga | → Entra | ← Indietro | Invio Seleziona | Esc Chiudi"
            )
        else:
            self.header.setText("🔍 ↑↓ Naviga | Invio Seleziona | Esc Chiudi")

    def _populate_items(self, filter_text=""):
        if not self.is_file_navigation or not self.navigator:
            return
        items = self.navigator.get_items()
        if filter_text:
            filter_lower = filter_text.lower()
            items = [
                i for i in items
                if filter_lower in i.get('display_name', i['name']).lower()
            ]
        self.model.set_items(items)
        if self.model.rowCount() > 0:
            self.list_view.setCurrentIndex(self.model.index(0, 0))

    def _on_filter_text_changed(self, text: str):
        if self.is_file_navigation:
            self._populate_items(text)
        else:
            if not text:
                self.model.setStringList(self.all_items)
            else:
                text_lower = text.lower()
                filtered = [i for i in self.all_items if text_lower in i.lower()]
                self.model.setStringList(filtered)
            if self.model.rowCount() > 0:
                self.list_view.setCurrentIndex(self.model.index(0, 0))

    def _navigate_into_folder(self):
        if not self.is_file_navigation or not self.navigator:
            return False
        current_index = self.list_view.currentIndex()
        if not current_index.isValid():
            return False
        item = self.model.get_item(current_index)
        if item and item.get('is_dir'):
            target_path = item.get('path')
            if target_path and target_path.is_dir():
                self.navigator.navigate_to(target_path)
                self.filter_edit.clear()
                self._populate_items()
                self._update_header()
                if self.model.rowCount() > 0:
                    self.list_view.setCurrentIndex(self.model.index(0, 0))
                return True
        return False

    def _navigate_back(self):
        if not self.is_file_navigation or not self.navigator:
            return False
        if self.navigator.current_path != self.navigator.root_path:
            parent_path = self.navigator.current_path.parent
            if parent_path >= self.navigator.root_path:
                self.navigator.navigate_to(parent_path)
                self.filter_edit.clear()
                self._populate_items()
                self._update_header()
                if self.model.rowCount() > 0:
                    self.list_view.setCurrentIndex(self.model.index(0, 0))
                return True
        return False

    def _select_current_item(self):
        current_index = self.list_view.currentIndex()
        if not current_index.isValid():
            return
        if self.is_file_navigation:
            item = self.model.get_item(current_index)
            if item:
                name = item.get('display_name', item['path'].name)
                full_path = item.get('path')  # Path completo
                self.itemSelected.emit(name, full_path)
        else:
            selected_text = self.model.data(current_index, Qt.DisplayRole)
            if selected_text:
                self.itemSelected.emit(selected_text, None)
        self.accept()

    def eventFilter(self, obj, event):
        if event.type() != QEvent.KeyPress:
            return super().eventFilter(obj, event)
        key = event.key()

        if key == Qt.Key_Right:
            if obj == self.filter_edit and self.filter_edit.cursorPosition() < len(self.filter_edit.text()):
                return False
            self._navigate_into_folder()
            return True

        if key == Qt.Key_Left:
            if obj == self.filter_edit and self.filter_edit.cursorPosition() > 0:
                return False
            self._navigate_back()
            return True

        if key == Qt.Key_Up:
            if obj == self.filter_edit:
                count = self.model.rowCount()
                if count > 0:
                    self.list_view.setCurrentIndex(self.model.index(count - 1, 0))
                    self.list_view.setFocus()
                return True
            return False

        if key == Qt.Key_Down:
            if obj == self.filter_edit and self.model.rowCount() > 0:
                self.list_view.setCurrentIndex(self.model.index(0, 0))
                self.list_view.setFocus()
                return True
            return False

        if key in (Qt.Key_Return, Qt.Key_Enter):
            if obj == self.filter_edit and self.model.rowCount() > 0:
                self.list_view.setCurrentIndex(self.model.index(0, 0))
            self._select_current_item()
            return True

        if key == Qt.Key_Escape:
            self.reject()
            return True

        if key == Qt.Key_Tab:
            if obj == self.filter_edit and self.model.rowCount() > 0:
                self.list_view.setCurrentIndex(self.model.index(0, 0))
                self.list_view.setFocus()
            else:
                self.filter_edit.setFocus()
            return True

        return super().eventFilter(obj, event)

    def show_at_cursor(self, global_pos):
        screen = QApplication.primaryScreen().geometry()
        x = max(0, min(global_pos.x(), screen.right() - self.width()))
        y = max(0, min(global_pos.y(), screen.bottom() - self.height()))
        self.move(x, y)
        self.show()
        self.filter_edit.setFocus()
        self.filter_edit.selectAll()