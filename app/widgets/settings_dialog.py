"""Dialog per le impostazioni dell'applicazione."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout,
    QComboBox, QCheckBox, QSpinBox, QDialogButtonBox, QLabel
)
from PySide6.QtCore import Qt
from app.theme import ThemeMode

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_theme=ThemeMode.AUTO, autosave_enabled=True, autosave_interval=60):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.setMinimumSize(450, 350)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Tab Aspetto
        appearance_tab = QWidget()
        appearance_layout = QFormLayout(appearance_tab)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        theme_map = {ThemeMode.LIGHT: 0, ThemeMode.DARK: 1, ThemeMode.AUTO: 2}
        self.theme_combo.setCurrentIndex(theme_map.get(current_theme, 2))
        appearance_layout.addRow("Tema:", self.theme_combo)
        tabs.addTab(appearance_tab, "🎨 Aspetto")
        
        # Tab Salvataggio
        save_tab = QWidget()
        save_layout = QFormLayout(save_tab)
        self.autosave_check = QCheckBox()
        self.autosave_check.setChecked(autosave_enabled)
        save_layout.addRow("Auto-salvataggio:", self.autosave_check)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 600)
        self.interval_spin.setValue(autosave_interval)
        self.interval_spin.setSuffix(" secondi")
        self.interval_spin.setEnabled(autosave_enabled)
        self.autosave_check.toggled.connect(self.interval_spin.setEnabled)
        save_layout.addRow("Intervallo:", self.interval_spin)
        tabs.addTab(save_tab, "💾 Salvataggio")
        
        layout.addWidget(tabs)
        
        # Pulsanti OK/Annulla
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_theme(self):
        themes = [ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.AUTO]
        return themes[self.theme_combo.currentIndex()]
    
    def get_autosave_enabled(self):
        return self.autosave_check.isChecked()
    
    def get_autosave_interval(self):
        return self.interval_spin.value()