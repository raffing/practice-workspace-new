import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import yaml
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QSplitter,
    QLineEdit, QPushButton, QLabel, QFileDialog, QMessageBox,
    QToolBar, QStatusBar, QInputDialog, QCheckBox, QFrame,
    QMenu
)
from PySide6.QtCore import Qt, QTimer, QFileSystemWatcher, QSettings
from PySide6.QtGui import QAction, QKeySequence, QColor, QTextCursor

from app.theme import Theme, ThemeMode
from app.parser import DocumentParser
from app.models import DocumentNode
from app.constants import FILE_ICONS
from app.widgets import PracticeEditor, AutocompletePopup, CommandPalette


class PracticeWorkspace(QMainWindow):
    def __init__(self):
        super().__init__()
        self.workspace_path: Optional[Path] = None
        self.current_practice: Optional[str] = None
        self.parser = DocumentParser()
        self.file_watcher = QFileSystemWatcher()
        self.autocomplete_popup = None
        self.command_palette = None
        self.current_theme_mode = ThemeMode.AUTO
        self.current_theme = Theme.get_theme()
        self._refresh_timer = QTimer()
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._do_refresh_tree)
        self.practice_paths: Dict[str, str] = {}

        self._setup_ui()
        self._setup_connections()
        self._setup_shortcuts()
        self._load_settings()
        self._apply_theme()

    # ========================================================================
    # UI SETUP
    # ========================================================================

    def _setup_ui(self):
        self.setWindowTitle("Practice Workspace")
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self._setup_toolbar()
        splitter = QSplitter(Qt.Horizontal)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Workspace"])
        self.tree_widget.setMinimumWidth(300)
        splitter.addWidget(self.tree_widget)
        self.editor = PracticeEditor()
        splitter.addWidget(self.editor)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.workspace_label = QLabel("Nessun workspace aperto")
        self.status_bar.addWidget(self.workspace_label)

    def _update_modified_indicator(self):
        """Aggiunge/rimuove * accanto al nome del file nella status bar."""
        if not self.workspace_path:
            return
        
        clean_text = self.editor.toPlainText()
        lines = clean_text.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith('# '):
                name = line[2:].strip()
                if name in self.practice_paths:
                    new_lines.append(f'# [{name}]({self.practice_paths[name]})')
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        current_with_paths = '\n'.join(new_lines)
        
        if current_with_paths != self.editor.last_saved_content:
            self.workspace_label.setText("Agenda.md *")
        else:
            self.workspace_label.setText("Agenda.md")
    
    def _setup_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        self.open_action = QAction("📂 Apri", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addSeparator()
        self.filter_frame = QFrame()
        filter_layout = QHBoxLayout(self.filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(6)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("🔍 Cerca pratiche e task...")
        self.filter_edit.setMinimumWidth(250)
        filter_layout.addWidget(self.filter_edit)
        self.toolbar.addWidget(self.filter_frame)
        self.toolbar.addSeparator()
        self.open_tasks_only = QCheckBox("Solo aperti")
        self.toolbar.addWidget(self.open_tasks_only)
        self.today_only = QCheckBox("Solo oggi")
        self.toolbar.addWidget(self.today_only)
        self.with_files_only = QCheckBox("Con allegati")
        self.toolbar.addWidget(self.with_files_only)
        self.toolbar.addSeparator()
        self.save_action = QAction("💾 Salva", self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.toolbar.addAction(self.save_action)
        self.theme_btn = QPushButton("🌓")
        self.theme_btn.setToolTip("Cambia tema (Light/Dark/Auto)")
        self.theme_btn.setFixedSize(36, 36)
        self.toolbar.addWidget(self.theme_btn)

    def _setup_connections(self):
        file_menu = self.menuBar().addMenu("📁 File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        edit_menu = self.menuBar().addMenu("✏️ Modifica")
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)
        view_menu = self.menuBar().addMenu("👁️ Vista")
        theme_action = QAction("🌓 Cambia tema", self)
        theme_action.triggered.connect(self._cycle_theme)
        view_menu.addAction(theme_action)

        self.open_action.triggered.connect(self._open_workspace)
        self.save_action.triggered.connect(self._save_document)
        self.theme_btn.clicked.connect(self._cycle_theme)
        self.editor.practiceClicked.connect(self._on_practice_name_clicked)
        self.editor.fileClicked.connect(self._open_file)
        self.editor.autocompleteRequested.connect(self._show_autocomplete)
        self.editor.documentChanged.connect(self._on_document_changed)
        self.editor.ctrlFPressed.connect(lambda: self.filter_edit.setFocus())
        self.editor.ctrlEPressed.connect(lambda: self.editor.setFocus())
        self.editor.ctrlNPressed.connect(self._new_practice_dialog)
        self.editor.f5Pressed.connect(self._do_refresh_tree)
        self.tree_widget.itemClicked.connect(self._on_tree_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.filter_edit.textChanged.connect(self._apply_filter)
        self.open_tasks_only.toggled.connect(self._apply_filter)
        self.today_only.toggled.connect(self._apply_filter)
        self.with_files_only.toggled.connect(self._apply_filter)
        self.file_watcher.fileChanged.connect(self._on_file_changed)

    def _setup_shortcuts(self):
        shortcut = QAction("Command Palette", self)
        shortcut.setShortcut(QKeySequence("Ctrl+P"))
        shortcut.triggered.connect(self._show_command_palette)
        self.addAction(shortcut)

    # ========================================================================
    # THEME
    # ========================================================================

    def _cycle_theme(self):
        if self.current_theme_mode == ThemeMode.AUTO:
            self.current_theme_mode = ThemeMode.LIGHT
        elif self.current_theme_mode == ThemeMode.LIGHT:
            self.current_theme_mode = ThemeMode.DARK
        else:
            self.current_theme_mode = ThemeMode.AUTO
        self._apply_theme()
        icons = {ThemeMode.LIGHT: "☀️", ThemeMode.DARK: "🌙", ThemeMode.AUTO: "🌓"}
        self.theme_btn.setText(icons[self.current_theme_mode])
        self.status_bar.showMessage(f"Tema: {self.current_theme_mode.value}", 2000)

    def _apply_theme(self):
        from PySide6.QtWidgets import QApplication
        self.current_theme = Theme.get_theme(self.current_theme_mode)
        Theme.apply_to_app(QApplication.instance(), self.current_theme)
        self.editor.update_theme(self.current_theme)
        icons = {ThemeMode.LIGHT: "☀️", ThemeMode.DARK: "🌙", ThemeMode.AUTO: "🌓"}
        self.theme_btn.setText(icons[self.current_theme_mode])

    # ========================================================================
    # WORKSPACE & DOCUMENT
    # ========================================================================

    def _open_workspace(self):
        path = QFileDialog.getExistingDirectory(self, "Seleziona Workspace")
        if path:
            self.workspace_path = Path(path)
            self._load_workspace()

    def _load_workspace(self):
        if not self.workspace_path or not self.workspace_path.exists():
            return
        self.workspace_label.setText(f"Workspace: {self.workspace_path}")
        self.setWindowTitle(f"Practice Workspace - {self.workspace_path.name}")
        self.file_watcher.addPath(str(self.workspace_path))
        agenda_file = self.workspace_path / "Agenda.md"
        if not agenda_file.exists():
            agenda_file.write_text(
                "# Villa Rossi\n- Verificare computo @computo.xlsx\n"
                "  - Aggiornare prezziario\n"
                "  - Verificare quantità\n"
                "- Appuntamento con @Cliente domani #urgenze\n\n"
                "# Baldassarre\n- Primo sopralluogo oggi #catasto\n"
                "- Preparare relazione @relazione.docx\n\n"
                "# Condominio Alfa\n- Task amministrativo\n",
                encoding='utf-8'
            )
        self._load_document(agenda_file) 


    def _load_document(self, file_path: Path):
        try:
            raw_content = file_path.read_text(encoding='utf-8')
            self.practice_paths = dict(
                re.findall(r'^# \[([^\]]+)\]\(([^)]+)\)', raw_content, re.MULTILINE)
            )
            clean_content = re.sub(
                r'^# \[([^\]]+)\]\([^)]+\)', r'# \1', raw_content, flags=re.MULTILINE
            )
            self.editor.setPlainText(clean_content)
            self.editor.last_saved_content = raw_content
            self._update_modified_indicator()
            self._do_refresh_tree()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile caricare il documento: {e}")

    def _save_document(self):
        if not self.workspace_path:
            return
        agenda_file = self.workspace_path / "Agenda.md"
        try:
            clean_text = self.editor.toPlainText()
            lines = clean_text.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('# '):
                    name = line[2:].strip()
                    if name in self.practice_paths:
                        rel_path = self.practice_paths[name]
                        new_lines.append(f'# [{name}]({rel_path})')
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            content_with_paths = '\n'.join(new_lines)
            agenda_file.write_text(content_with_paths, encoding='utf-8')
            self.editor.last_saved_content = content_with_paths
            self._update_modified_indicator()
            self.status_bar.showMessage("Documento salvato", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile salvare il documento: {e}")

    def _on_file_changed(self, path: str):
        if self.workspace_path and path == str(self.workspace_path / "Agenda.md"):
            reply = QMessageBox.question(
                self, "Documento modificato",
                "Agenda.md è stato modificato esternamente. Ricaricare?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._load_document(self.workspace_path / "Agenda.md")
                self._update_modified_indicator()

    # ========================================================================
    # PRACTICE & FILE OPENING
    # ========================================================================

    def _open_practice_folder(self, practice_name: str) -> bool:
        if not self.workspace_path:
            return False
        if practice_name in self.practice_paths:
            rel_path = self.practice_paths[practice_name]
            full_path = self.workspace_path / rel_path
            if full_path.is_dir():
                os.startfile(str(full_path))
                self.status_bar.showMessage(f"Aperta: {practice_name}", 3000)
                return True
        self.status_bar.showMessage(f"Nessun path per '{practice_name}'", 3000)
        return False

    def _find_practice_folder_for_file(self, practice_name: str) -> Optional[Path]:
        if not self.workspace_path:
            return None
        if practice_name in self.practice_paths:
            full_path = self.workspace_path / self.practice_paths[practice_name]
            if full_path.is_dir():
                return full_path
        return None

    def _open_file(self, filename: str):
        if not self.workspace_path:
            return
        clean_filename = filename.strip("'\"")
        practice_name = self.editor.get_current_practice_name()
        if not practice_name or practice_name not in self.practice_paths:
            QMessageBox.warning(self, "File non trovato",
                               f"Nessun path associato alla pratica '{practice_name}'.")
            return
        practice_dir = self.workspace_path / self.practice_paths[practice_name]
        file_path = practice_dir / clean_filename
        if file_path.is_file():
            os.startfile(str(file_path))
            self.status_bar.showMessage(f"Aperto: {clean_filename}", 3000)
            return
        for f in practice_dir.rglob(clean_filename):
            if f.is_file():
                os.startfile(str(f))
                self.status_bar.showMessage(f"Aperto: {clean_filename}", 3000)
                return
        QMessageBox.warning(self, "File non trovato",
                           f"Il file '{clean_filename}' non è stato trovato in '{practice_dir}'.")

    def _on_practice_name_clicked(self, practice_name: str):
        self._open_practice_folder(practice_name)

    # ========================================================================
    # TREE WIDGET
    # ========================================================================

    def _do_refresh_tree(self):
        self.tree_widget.clear()
        if not self.workspace_path:
            return

        # Root workspace
        root_item = QTreeWidgetItem()
        root_item.setText(0, f"📁 {self.workspace_path.name}")
        root_item.setToolTip(0, str(self.workspace_path))
        root_item.setData(0, Qt.UserRole, {
            'type': 'folder',
            'path': str(self.workspace_path),
            'is_practice': False
        })
        root_item.setForeground(0, QColor(self.current_theme['tree_practice']))
        font = root_item.font(0)
        font.setBold(True)
        root_item.setFont(0, font)
        self.tree_widget.addTopLevelItem(root_item)
        self._populate_tree_folder(root_item, self.workspace_path)
        root_item.setExpanded(True)

        # Sezione pratiche da Agenda
        text = self.editor.toPlainText()
        if text:
            nodes = self.parser.parse_document(text)
            practices_item = QTreeWidgetItem()
            practices_item.setText(0, "📋 Pratiche in Agenda")
            practices_item.setForeground(0, QColor(self.current_theme['accent']))
            font = practices_item.font(0)
            font.setBold(True)
            practices_item.setFont(0, font)
            practices_item.setFlags(practices_item.flags() & ~Qt.ItemIsSelectable)
            self.tree_widget.addTopLevelItem(practices_item)

            for practice_node in nodes:
                if practice_node.is_task:
                    continue
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
                practice_item.setForeground(0, QColor(self.current_theme['tree_practice']))
                practices_item.addChild(practice_item)

                practice_files = set()
                for task_node in practice_node.children:
                    self._add_task_to_tree(task_node, practice_item, practice_files)

                if practice_files:
                    file_section = QTreeWidgetItem()
                    file_section.setText(0, f"📎 File collegati ({len(practice_files)})")
                    file_section.setForeground(0, QColor(self.current_theme['text_secondary']))
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
            practices_item.setExpanded(True)

    def _populate_tree_folder(self, parent_item: QTreeWidgetItem, path: Path, depth: int = 0):
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

    def _add_task_to_tree(self, task_node: DocumentNode, parent_item: QTreeWidgetItem, practice_files: set):
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
            'type': 'task', 'line_number': task_node.line_number,
            'text': task_node.text, 'is_practice': False
        })
        parent_item.addChild(task_item)
        for child in task_node.children:
            self._add_task_to_tree(child, task_item, practice_files)
        if task_node.children:
            task_item.setExpanded(True)

    def _create_file_item(self, filename: str, practice_name: str) -> Optional[QTreeWidgetItem]:
        if not self.workspace_path:
            return None
        if practice_name not in self.practice_paths:
            return self._make_missing_file_item(filename, "Pratica senza path")
        practice_dir = self.workspace_path / self.practice_paths[practice_name]
        if not practice_dir.is_dir():
            return self._make_missing_file_item(filename, "Cartella pratica non trovata")
        file_path = practice_dir / filename
        if not file_path.exists():
            for f in practice_dir.rglob(filename):
                if f.is_file():
                    file_path = f
                    break
            else:
                return self._make_missing_file_item(filename, "File non trovato nella cartella")
        file_item = QTreeWidgetItem()
        icon = FILE_ICONS.get(file_path.suffix.lower(), '📎')
        file_item.setText(0, f"{icon} {filename}")
        file_item.setToolTip(0, f"File: {filename}\nPercorso: {file_path}\nClicca per aprire")
        file_item.setForeground(0, QColor(self.current_theme['tree_file']))
        file_item.setData(0, Qt.UserRole, {
            'type': 'file', 'filename': filename,
            'practice': practice_name, 'path': str(file_path)
        })
        return file_item

    def _make_missing_file_item(self, filename: str, reason: str) -> QTreeWidgetItem:
        item = QTreeWidgetItem()
        item.setText(0, f"⚠️ {filename}")
        item.setToolTip(0, f"File: {filename}\n{reason}")
        item.setForeground(0, QColor(self.current_theme['tree_missing']))
        item.setData(0, Qt.UserRole, {
            'type': 'file_missing', 'filename': filename, 'practice': ''
        })
        return item

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        item_type = data.get('type')
        if item_type == 'practice':
            self._open_practice_folder(data.get('text'))
            return
        if item_type == 'file':
            filepath = data.get('path')
            if filepath and Path(filepath).exists():
                os.startfile(filepath)
                self.status_bar.showMessage(f"Aperto: {data.get('filename', '')}", 3000)
            return
        if item_type == 'file_missing':
            QMessageBox.warning(self, "File non trovato",
                               f"Il file '{data.get('filename')}' non è stato trovato.")
            return
        line_number = data.get('line_number')
        if line_number is not None:
            block = self.editor.document().findBlockByLineNumber(line_number)
            if block.isValid():
                self.editor.setTextCursor(QTextCursor(block))
                self.editor.setFocus()

    def _on_tree_context_menu(self, pos):
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
                    self.practice_paths[folder_name] = rel_str
                    self.editor.append(f"\n# {folder_name}\n- ")
                    self._save_document()
                    self._do_refresh_tree()
                    self.status_bar.showMessage(f"Pratica '{folder_name}' aggiunta", 3000)
                except ValueError:
                    self.status_bar.showMessage("Errore: cartella fuori dal workspace", 3000)

    # ========================================================================
    # FILTER
    # ========================================================================

    def _apply_filter(self):
        filter_text = self.filter_edit.text().lower()
        show_open_only = self.open_tasks_only.isChecked()
        show_today_only = self.today_only.isChecked()
        show_with_files = self.with_files_only.isChecked()
        today_str = datetime.now().strftime("%Y-%m-%d")

        def filter_items(item: QTreeWidgetItem):
            data = item.data(0, Qt.UserRole)
            item_type = data.get('type') if data else None

            if item_type is None and 'File collegati' in item.text(0):
                return

            visible = True
            text = item.text(0).lower()

            if filter_text and filter_text not in text:
                visible = False
            if show_open_only and item_type == 'task':
                if text.startswith('☑'):
                    visible = False
            if show_today_only and item_type == 'task':
                if today_str not in item.text(0):
                    visible = False
            if show_with_files and item_type == 'practice':
                has_files = False
                for i in range(item.childCount()):
                    child = item.child(i)
                    child_data = child.data(0, Qt.UserRole)
                    if child_data and child_data.get('type') in ('file', 'file_missing'):
                        has_files = True
                        break
                    if 'File collegati' in child.text(0) and child.childCount() > 0:
                        has_files = True
                        break
                if not has_files:
                    visible = False

            item.setHidden(not visible)
            for i in range(item.childCount()):
                filter_items(item.child(i))

        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            filter_items(root.child(i))

    # ========================================================================
    # AUTOCOMPLETE
    # ========================================================================

    def _show_autocomplete(self, type: str, position: int, practice_name: str = ""):
        if not self.workspace_path:
            return
        if self.autocomplete_popup:
            self.autocomplete_popup.close()
        self.editor.autocomplete_active = True
        start_path = self.workspace_path
        if type == 'file':
            if practice_name and practice_name in self.practice_paths:
                practice_dir = self.workspace_path / self.practice_paths[practice_name]
                if practice_dir.is_dir():
                    start_path = practice_dir
        self.autocomplete_popup = AutocompletePopup(
            ["file_navigation"], self, self.workspace_path,
            show_files=(type == 'file'),
            show_directories=True,
            start_path=start_path,
            theme=self.current_theme
        )
        self.autocomplete_popup.itemSelected.connect(
            lambda name, full_path: self._insert_autocomplete_item(name, position, full_path)
        )
        self.autocomplete_popup.finished.connect(self._on_autocomplete_closed)
        cursor_rect = self.editor.cursorRect()
        global_pos = self.editor.mapToGlobal(cursor_rect.bottomRight())
        self.autocomplete_popup.show_at_cursor(global_pos)

    def _on_autocomplete_closed(self):
        self.editor.autocomplete_active = False
        self.autocomplete_popup = None

    def _insert_autocomplete_item(self, item: str, position: int, full_path: Path = None):
        cursor = self.editor.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        line_text = cursor.selectedText()
        cursor.setPosition(position)
        is_practice = line_text.strip() == "#"
        prefix = " " if is_practice else ""
        if item == "➕ Nuova pratica":
            name, ok = QInputDialog.getText(self, "Nuova Pratica", "Nome pratica:")
            if ok and name:
                self._create_new_practice(name)
                cursor.insertText(f"{prefix}{name}\n")
        else:
            if is_practice and full_path is not None:
                if full_path.is_dir():
                    try:
                        rel = full_path.relative_to(self.workspace_path)
                        rel_str = str(rel).replace('\\', '/')
                        self.practice_paths[item] = rel_str
                        self._save_document()
                        self.status_bar.showMessage(f"Pratica '{item}' associata a {rel_str}", 3000)
                    except ValueError:
                        pass
                cursor.insertText(f" {item}\n")
            else:
                item_to_insert = f"'{item}'" if " " in item else item
                cursor.insertText(f"{prefix}{item_to_insert}\n")
        self.editor.setTextCursor(cursor)
        self.editor.autocomplete_active = False
        self._do_refresh_tree()

    # ========================================================================
    # COMMAND PALETTE
    # ========================================================================

    def _show_command_palette(self):
        if self.command_palette:
            self.command_palette.close()
        self.command_palette = CommandPalette(self, self.current_theme)
        self.command_palette.commandExecuted.connect(self._on_command_executed)
        self.command_palette.show_centered()

    def _on_command_executed(self, command_id: str, param: str):
        if command_id == "open_practice":
            self.filter_edit.setFocus()
        elif command_id == "open_file":
            self.filter_edit.setFocus()
        elif command_id == "new_practice":
            self._new_practice_dialog()
        elif command_id == "new_task":
            self.editor.setFocus()
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.editor.setTextCursor(cursor)
            self.editor.insertPlainText("\n- ")
        elif command_id == "toggle_theme":
            self._cycle_theme()
        elif command_id == "save":
            self._save_document()
        elif command_id == "focus_filter":
            self.filter_edit.setFocus()
        elif command_id == "focus_editor":
            self.editor.setFocus()
        elif command_id == "refresh":
            self._do_refresh_tree()

    # ========================================================================
    # NEW PRACTICE
    # ========================================================================

    def _new_practice_dialog(self):
        name, ok = QInputDialog.getText(self, "Nuova Pratica", "Nome pratica:")
        if ok and name:
            self._create_new_practice(name)

    def _create_new_practice(self, name: str):
        if not self.workspace_path:
            return
        practice_dir = self.workspace_path / name
        practice_dir.mkdir(exist_ok=True)
        metadata = {
            'id': name.lower().replace(' ', '-'),
            'title': name,
            'status': 'active',
            'created': datetime.now().strftime("%Y-%m-%d")
        }
        with open(practice_dir / "practice.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False)
        try:
            rel = practice_dir.relative_to(self.workspace_path)
            self.practice_paths[name] = str(rel).replace('\\', '/')
        except ValueError:
            pass
        self.editor.append(f"\n# {name}\n- ")
        self._save_document()
        self.status_bar.showMessage(f"Pratica '{name}' creata", 3000)
        self._do_refresh_tree()

    # ========================================================================
    # DOCUMENT CHANGE
    # ========================================================================

    def _on_document_changed(self):
        self._update_modified_indicator()
        self._refresh_timer.start(300)

    # ========================================================================
    # SETTINGS
    # ========================================================================

    def _load_settings(self):
        settings = QSettings("PracticeWorkspace", "MainWindow")
        if geometry := settings.value("geometry"):
            self.restoreGeometry(geometry)
        if state := settings.value("windowState"):
            self.restoreState(state)
        last_workspace = settings.value("lastWorkspace")
        if last_workspace and Path(last_workspace).exists():
            self.workspace_path = Path(last_workspace)
            self._load_workspace()
        theme_str = settings.value("theme", "auto")
        try:
            self.current_theme_mode = ThemeMode(theme_str)
        except ValueError:
            self.current_theme_mode = ThemeMode.AUTO

    def closeEvent(self, event):
        settings = QSettings("PracticeWorkspace", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("theme", self.current_theme_mode.value)
        if self.workspace_path:
            settings.setValue("lastWorkspace", str(self.workspace_path))
        
        # Rigenera il contenuto con path per confrontarlo con last_saved_content
        if self.workspace_path:
            clean_text = self.editor.toPlainText()
            lines = clean_text.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('# '):
                    name = line[2:].strip()
                    if name in self.practice_paths:
                        new_lines.append(f'# [{name}]({self.practice_paths[name]})')
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            current_with_paths = '\n'.join(new_lines)
            
            if current_with_paths != self.editor.last_saved_content:
                reply = QMessageBox.question(
                    self, "Modifiche non salvate",
                    "Vuoi salvare le modifiche prima di uscire?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                if reply == QMessageBox.Save:
                    self._save_document()
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return
        
        event.accept()