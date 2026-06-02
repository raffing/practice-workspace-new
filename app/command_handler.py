"""
Command handler for Practice Workspace.
Centralizes command execution logic from the command palette and shortcuts.
"""

from typing import Optional
from PySide6.QtGui import QTextCursor


class CommandHandler:
    """Handles command execution for the workspace."""
    
    def __init__(
        self,
        main_window=None,
        sidebar=None,
        editor=None,
    ):
        self.main_window = main_window
        self.sidebar = sidebar
        self.editor = editor
    
    def execute(self, command_id: str, param: str = ""):
        """Execute a command by ID."""
        handlers = {
            "open_practice": self._open_practice,
            "open_file": self._open_file,
            "focus_filter": self._focus_filter,
            "new_practice": self._new_practice,
            "new_task": self._new_task,
            "toggle_theme": self._toggle_theme,
            "save": self._save,
            "focus_editor": self._focus_editor,
            "refresh": self._refresh,
        }
        handler = handlers.get(command_id)
        if handler:
            handler(param)
    
    def _open_practice(self, param: str):
        """Open practice handler."""
        if self.main_window and hasattr(self.main_window, 'tree_search'):
            self.main_window.tree_search.setFocus()
    
    def _open_file(self, param: str):
        """Open file handler."""
        if self.main_window and hasattr(self.main_window, 'tree_search'):
            self.main_window.tree_search.setFocus()
    
    def _focus_filter(self, param: str):
        """Focus filter handler."""
        if self.main_window and hasattr(self.main_window, 'tree_search'):
            self.main_window.tree_search.setFocus()
    
    def _new_practice(self, param: str):
        """New practice handler."""
        if self.main_window:
            self.main_window._new_practice_dialog()
    
    def _new_task(self, param: str):
        """New task handler."""
        if self.editor:
            self.editor.setFocus()
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.editor.setTextCursor(cursor)
            self.editor.insertPlainText("\n- ")
    
    def _toggle_theme(self, param: str):
        """Toggle theme handler."""
        if self.main_window:
            self.main_window._cycle_theme()
    
    def _save(self, param: str):
        """Save handler."""
        if self.main_window:
            self.main_window._save_document()
    
    def _focus_editor(self, param: str):
        """Focus editor handler."""
        if self.editor:
            self.editor.setFocus()
    
    def _refresh(self, param: str):
        """Refresh handler."""
        if self.main_window:
            self.main_window._do_refresh_tree()
