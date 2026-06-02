"""
Sidebar widget for Practice Workspace.
Handles the tree view, filtering, and interactions with workspace items.
"""

from pathlib import Path
from typing import Optional, Dict, Set

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLineEdit, QMenu
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QFont

from app.parser import DocumentParser
from app.models import DocumentNode
from app.constants import FILE_ICONS
from app.system_open import open_path, find_named_path


class SidebarSignals(QObject):
    """Signals for sidebar interactions."""
    practice_clicked = Signal(str)  # practice_name
    file_clicked = Signal(str)  # filename
    folder_clicked = Signal(str)  # folder_path
    refresh_requested = Signal()
    practice_added = Signal(str, str)  # practice_name, relative_path


class SidebarWidget(QWidget):
    """Widget for the sidebar tree view and search."""

    def __init__(
        self,
        workspace_path: Optional[Path] = None,
        practice_paths: Optional[Dict[str, str]] = None,
        theme: Optional[Dict] = None,
        parent=None
    ):
        super().__init__(parent)
        self.workspace_path = workspace_path
        self.practice_paths = practice_paths or {}
        self.current_theme = theme or {}
        self.parser = DocumentParser()
        self.signals = SidebarSignals()

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Set up the sidebar UI: search bar + tree widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search bar
        self.tree_search = QLineEdit()
        self.tree_search.setPlaceholderText("🔍 Filtra albero...")
        self.tree_search.setStyleSheet("""
            QLineEdit {
                border: none;
                border-bottom: 1px solid palette(mid);
                padding: 8px 12px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.tree_search)

        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Workspace"])
        self.tree_widget.setMinimumWidth(300)
        layout.addWidget(self.tree_widget)

    def _setup_connections(self):
        """Connect signals for tree interactions."""
        self.tree_widget.itemClicked.connect(self._on_tree_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.tree_search.textChanged.connect(self._apply_filter)

    def update_theme(self, theme: Dict):
        """Update the theme colors."""
        self.current_theme = theme

    def update_workspace(self, workspace_path: Path, practice_paths: Dict[str, str]):
        """Update workspace path and practice paths."""
        self.workspace_path = workspace_path
        self.practice_paths = practice_paths

    def refresh_tree(self, document_text: str = ""):
        """Refresh the tree view with workspace and document data."""
        self.tree_widget.clear()
        if not self.workspace_path:
            return

        # Root workspace folder
        root_item = QTreeWidgetItem()
        root_item.setText(0, f"📁 {self.workspace_path.name}")
        root_item.setToolTip(0, str(self.workspace_path))
        root_item.setData(0, Qt.UserRole, {
            'type': 'folder',
            'path': str(self.workspace_path),
            'is_practice': False
        })
        root_item.setForeground(0, QColor(self.current_theme.get('tree_practice', '#FFFFFF')))
        font = root_item.font(0)
        font.setBold(True)
        root_item.setFont(0, font)
        self.tree_widget.addTopLevelItem(root_item)
        self._populate_tree_folder(root_item, self.workspace_path)
        root_item.setExpanded(False)

        # Practices section from Agenda
        if document_text:
            nodes = self.parser.parse_document(document_text)
            practices_item = QTreeWidgetItem()
            practices_item.setText(0, "📋 Pratiche in Agenda")
            practices_item.setForeground(0, QColor(self.current_theme.get('accent', '#FF0000')))
            font = practices_item.font(0)
            font.setBold(True)
            practices_item.setFont(0, font)
            practices_item.setFlags(practices_item.flags() & ~Qt.ItemIsSelectable)
            self.tree_widget.addTopLevelItem(practices_item)

            for practice_node in nodes:
                if practice_node.is_task:
                    continue
                self._add_practice_to_tree(practice_node, practices_item)

            practices_item.setExpanded(True)

    def _populate_tree_folder(self, parent_item: QTreeWidgetItem, path: Path, depth: int = 0):
        """Recursively populate tree with folder contents."""
        if depth > 3:
            return
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if item.name.startswith('.'):
                    continue
                if item.name == 'Agenda.md':
                    continue
                tree_item = QTreeWidgetItem()
                if item.is_dir():
                    tree_item.setText(0, f"📁 {item.name}")
                    tree_item.setData(0, Qt.UserRole, {
                        'type': 'folder',
                        'path': str(item),
                        'is_practice': False
                    })
                    self._populate_tree_folder(tree_item, item, depth + 1)
                else:
                    icon = FILE_ICONS.get(item.suffix.lower(), '📎')
                    tree_item.setText(0, f"{icon} {item.name}")
                    tree_item.setData(0, Qt.UserRole, {
                        'type': 'file',
                        'path': str(item)
                    })
                parent_item.addChild(tree_item)
        except PermissionError:
            pass

    def _add_practice_to_tree(self, practice_node: DocumentNode, parent_item: QTreeWidgetItem):
        """Add a practice and its tasks/files to the tree."""
        practice_item = QTreeWidgetItem()
        practice_item.setText(0, f"📁 {practice_node.text}")
        tooltip = f"Pratica: {practice_node.text}"
        if practice_node.text in self.practice_paths:
            tooltip += f"\nPath: {self.practice_paths[practice_node.text]}"
        practice_item.setToolTip(0, tooltip)
        practice_item.setData(0, Qt.UserRole, {
            'type': 'practice',
            'text': practice_node.text,
            'line_number': practice_node.line_number
        })
        practice_item.setForeground(0, QColor(self.current_theme.get('tree_practice', '#FFFFFF')))
        parent_item.addChild(practice_item)

        # Collect files from tasks
        practice_files: Set[str] = set()
        for task_node in practice_node.children:
            self._add_task_to_tree(task_node, practice_item, practice_files)

        # Add files section if there are any
        if practice_files:
            file_section = QTreeWidgetItem()
            file_section.setText(0, f"📎 File collegati ({len(practice_files)})")
            file_section.setForeground(0, QColor(self.current_theme.get('text_secondary', '#AAAAAA')))
            font = file_section.font(0)
            font.setItalic(True)
            file_section.setFont(0, font)
            file_section.setFlags(file_section.flags() & ~Qt.ItemIsSelectable)
            practice_item.addChild(file_section)
            for filename in sorted(practice_files):
                file_item = self._create_file_item(filename, practice_node.text)
                if file_item:
                    file_section.addChild(file_item)

        practice_item.setExpanded(True)

    def _add_task_to_tree(
        self,
        task_node: DocumentNode,
        parent_item: QTreeWidgetItem,
        practice_files: Set[str]
    ):
        """Add a task and its children to the tree."""
        task_item = QTreeWidgetItem()
        status = task_node.task_data.get('status', 'open') if task_node.task_data else 'open'
        icon = "☑" if status == 'done' else "☐"
        clean_text = DocumentParser.clean_task_text(task_node.text[:100])

        if task_node.task_data and task_node.task_data.get('files'):
            for f in task_node.task_data['files']:
                practice_files.add(f)

        display_text = f"{icon} {clean_text}"
        extras = []
        if task_node.task_data:
            if task_node.task_data.get('tags'):
                extras.append(' '.join(f'#{t}' for t in task_node.task_data['tags']))
            if task_node.task_data.get('people'):
                extras.append(' '.join(f'@{p}' for p in task_node.task_data['people']))
            if task_node.task_data.get('dates'):
                extras.append(f"📅 {', '.join(task_node.task_data['dates'])}")
        if extras:
            display_text += f"  | {' | '.join(extras)}"

        task_item.setText(0, display_text)
        task_item.setToolTip(0, f"Task: {clean_text}\nLinea: {task_node.line_number + 1}")
        task_item.setData(0, Qt.UserRole, {
            'type': 'task',
            'line_number': task_node.line_number,
            'text': task_node.text,
            'is_practice': False
        })
        parent_item.addChild(task_item)

        for child in task_node.children:
            self._add_task_to_tree(child, task_item, practice_files)

        if task_node.children:
            task_item.setExpanded(True)

    def _create_file_item(self, filename: str, practice_name: str) -> Optional[QTreeWidgetItem]:
        """Create a tree item for a file linked to a practice."""
        if not self.workspace_path:
            return None
        if practice_name not in self.practice_paths:
            return self._make_missing_file_item(filename, "Pratica senza path")

        practice_dir = self.workspace_path / self.practice_paths[practice_name]
        if not practice_dir.is_dir():
            return self._make_missing_file_item(filename, "Cartella pratica non trovata")

        file_path = find_named_path(practice_dir, filename)
        if not file_path:
            return self._make_missing_file_item(filename, "File non trovato nella cartella")

        file_item = QTreeWidgetItem()
        icon = FILE_ICONS.get(file_path.suffix.lower(), '📎')
        file_item.setText(0, f"{icon} {filename}")
        file_item.setToolTip(0, f"File: {filename}\nPercorso: {file_path}\nClicca per aprire")
        file_item.setForeground(0, QColor(self.current_theme.get('tree_file', '#FFFFFF')))
        file_item.setData(0, Qt.UserRole, {
            'type': 'file',
            'filename': filename,
            'practice': practice_name,
            'path': str(file_path)
        })
        return file_item

    def _make_missing_file_item(self, filename: str, reason: str) -> QTreeWidgetItem:
        """Create a tree item for a missing file."""
        item = QTreeWidgetItem()
        item.setText(0, f"⚠️ {filename}")
        item.setToolTip(0, f"File: {filename}\n{reason}")
        item.setForeground(0, QColor(self.current_theme.get('tree_missing', '#FF0000')))
        item.setData(0, Qt.UserRole, {
            'type': 'file_missing',
            'filename': filename,
            'practice': ''
        })
        return item

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle clicks on tree items."""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get('type')
        if item_type == 'practice':
            self.signals.practice_clicked.emit(data.get('text'))
            return

        if item_type == 'file':
            filepath = data.get('path')
            if filepath and Path(filepath).exists():
                self.signals.file_clicked.emit(filepath)
            return

        if item_type == 'file_missing':
            # Emit a signal or show a message (handled by parent)
            return

        if item_type == 'folder':
            self.signals.folder_clicked.emit(data.get('path'))
            return

        # Handle task clicks (jump to line in editor)
        line_number = data.get('line_number')
        if line_number is not None:
            self.signals.refresh_requested.emit()

    def _on_tree_context_menu(self, pos):
        """Handle right-click context menu on tree items."""
        item = self.tree_widget.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data.get('type') == 'folder' and not data.get('is_practice'):
            menu = QMenu(self)
            add_action = menu.addAction("➕ Aggiungi come pratica")
            action = menu.exec(self.tree_widget.mapToGlobal(pos))
            if action == add_action:
                folder_path = Path(data['path'])
                folder_name = folder_path.name
                try:
                    rel = folder_path.relative_to(self.workspace_path)
                    rel_str = str(rel).replace('\\', '/')
                    self.signals.practice_added.emit(folder_name, rel_str)
                except ValueError:
                    pass  # Handled by parent

    def _apply_filter(self):
        """Apply filter text to tree items."""
        filter_text = self.tree_search.text().lower()

        def filter_items(item: QTreeWidgetItem):
            if not filter_text:
                item.setHidden(False)
            else:
                text = item.text(0).lower()
                item.setHidden(filter_text not in text)

            for i in range(item.childCount()):
                filter_items(item.child(i))

        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            filter_items(root.child(i))
