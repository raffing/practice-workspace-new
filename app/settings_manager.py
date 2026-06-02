"""
Settings manager for Practice Workspace.
Centralizes settings loading, saving, and dialog management.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import QSettings

from app.theme import ThemeMode


class SettingsManager:
    """Manages application settings."""
    
    ORG_NAME = "PracticeWorkspace"
    APP_NAME = "MainWindow"
    
    def __init__(
        self,
        main_window=None,
    ):
        self.main_window = main_window
        self._settings = QSettings(self.ORG_NAME, self.APP_NAME)
    
    def load(self):
        """Load all settings and apply them."""
        self._load_window_settings()
        self._load_workspace_settings()
        self._load_theme_settings()
        self._load_autosave_settings()
    
    def _load_window_settings(self):
        """Load window geometry and state."""
        if self.main_window:
            if geometry := self._settings.value("geometry"):
                self.main_window.restoreGeometry(geometry)
            if state := self._settings.value("windowState"):
                self.main_window.restoreState(state)
    
    def _load_workspace_settings(self):
        """Load workspace path."""
        if self.main_window:
            last_workspace = self._settings.value("lastWorkspace")
            if last_workspace and Path(last_workspace).exists():
                self.main_window.workspace_path = Path(last_workspace)
                self.main_window._load_workspace()
    
    def _load_theme_settings(self):
        """Load theme settings."""
        if self.main_window:
            theme_str = self._settings.value("theme", "auto")
            try:
                self.main_window.current_theme_mode = ThemeMode(theme_str)
            except ValueError:
                self.main_window.current_theme_mode = ThemeMode.AUTO
    
    def _load_autosave_settings(self):
        """Load autosave settings."""
        if self.main_window:
            autosave_enabled = self._settings.value("autosave_enabled", True, type=bool)
            autosave_interval = self._settings.value("autosave_interval", 60, type=int)
            self.main_window._autosave_interval = (
                int(autosave_interval) if autosave_enabled and autosave_interval is not None else 0
            )  # type: ignore[arg-type]
    
    def save_window_state(self):
        """Save current window geometry and state."""
        if self.main_window:
            self._settings.setValue("geometry", self.main_window.saveGeometry())
            self._settings.setValue("windowState", self.main_window.saveState())
    
    def save_workspace(self, workspace_path: Optional[Path]):
        """Save current workspace path."""
        if workspace_path:
            self._settings.setValue("lastWorkspace", str(workspace_path))
        else:
            self._settings.remove("lastWorkspace")
    
    def save_theme(self, theme_mode: ThemeMode):
        """Save current theme."""
        self._settings.setValue("theme", theme_mode.value)
    
    def save_autosave(self, enabled: bool, interval: int):
        """Save autosave settings."""
        self._settings.setValue("autosave_enabled", enabled)
        self._settings.setValue("autosave_interval", interval)
    
    def show_dialog(self):
        """Show settings dialog and apply changes."""
        from app.widgets.settings_dialog import SettingsDialog
        
        if not self.main_window:
            return
        
        dialog = SettingsDialog(
            self.main_window,
            current_theme=self.main_window.current_theme_mode,
            autosave_enabled=self.main_window._autosave_interval > 0,
            autosave_interval=self.main_window._autosave_interval if self.main_window._autosave_interval > 0 else 60
        )
        
        if dialog.exec():
            # Apply theme
            new_theme = dialog.get_theme()
            if new_theme != self.main_window.current_theme_mode:
                self.main_window.current_theme_mode = new_theme
                self.main_window._apply_theme()
            
            # Apply autosave
            new_interval = dialog.get_autosave_interval() if dialog.get_autosave_enabled() else 0
            self.main_window._autosave_interval = new_interval
            if new_interval > 0:
                self.main_window._autosave_timer.start(new_interval * 1000)
            else:
                self.main_window._autosave_timer.stop()
            
            # Save settings
            self.save_theme(self.main_window.current_theme_mode)
            self.save_autosave(dialog.get_autosave_enabled(), dialog.get_autosave_interval())
            
            if self.main_window.status_bar:
                self.main_window.status_bar.showMessage("Impostazioni salvate", 3000)
