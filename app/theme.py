from enum import Enum
from typing import Dict
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class Theme:
    LIGHT = {
        'background': '#FFFFFF',
        'surface': '#F5F5F5',
        'surface_hover': '#E8E8E8',
        'surface_selected': '#E3F2FD',
        'text': '#212121',
        'text_secondary': '#666666',
        'text_disabled': '#999999',
        'accent': '#1976D2',
        'accent_light': '#BBDEFB',
        'accent_text': '#FFFFFF',
        'border': '#E0E0E0',
        'border_focus': '#1976D2',
        'success': '#2E7D32',
        'warning': '#FF6F00',
        'error': '#C62828',
        'info': '#00796B',
        'purple': '#7B1FA2',
        'tree_practice': '#2E7D32',
        'tree_task': '#1976D2',
        'tree_file': '#00796B',
        'tree_missing': '#FF6F00',
        'editor_background': '#FFFFFF',
        'editor_text': '#212121',
        'scrollbar_handle': '#BDBDBD',
        'scrollbar_handle_hover': '#9E9E9E',
        'shadow_color': QColor(0, 0, 0, 40)
    }
    
    DARK = {
        'background': '#1E1E1E',
        'surface': '#2D2D2D',
        'surface_hover': '#383838',
        'surface_selected': '#264F78',
        'text': '#D4D4D4',
        'text_secondary': '#9E9E9E',
        'text_disabled': '#616161',
        'accent': '#4FC3F7',
        'accent_light': '#264F78',
        'accent_text': '#1E1E1E',
        'border': '#424242',
        'border_focus': '#4FC3F7',
        'success': '#66BB6A',
        'warning': '#FFA726',
        'error': '#EF5350',
        'info': '#4DD0E1',
        'purple': '#CE93D8',
        'tree_practice': '#66BB6A',
        'tree_task': '#4FC3F7',
        'tree_file': '#4DD0E1',
        'tree_missing': '#FFA726',
        'editor_background': '#1E1E1E',
        'editor_text': '#D4D4D4',
        'scrollbar_handle': '#555555',
        'scrollbar_handle_hover': '#777777',
        'shadow_color': QColor(0, 0, 0, 100)
    }
    
    @classmethod
    def get_theme(cls, mode: ThemeMode = ThemeMode.AUTO) -> Dict:
        if mode == ThemeMode.AUTO:
            import darkdetect
            return cls.DARK if darkdetect.isDark() else cls.LIGHT
        elif mode == ThemeMode.DARK:
            return cls.DARK
        return cls.LIGHT

    @classmethod
    def apply_to_app(cls, app: QApplication, theme: Dict):
        app.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['background']};
            }}
            QToolBar {{
                background-color: {theme['surface']};
                border-bottom: 1px solid {theme['border']};
                spacing: 8px;
                padding: 4px 8px;
            }}
            QToolBar QLabel {{
                color: {theme['text']};
            }}
            QLineEdit {{
                background-color: {theme['background']};
                color: {theme['text']};
                border: 2px solid {theme['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {theme['border_focus']};
            }}
            QPushButton {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme['surface_hover']};
            }}
            QPushButton:checked {{
                background-color: {theme['accent_light']};
                color: {theme['accent']};
                border-color: {theme['accent']};
            }}
            QCheckBox {{
                color: {theme['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {theme['border']};
                border-radius: 4px;
                background-color: {theme['background']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme['accent']};
                border-color: {theme['accent']};
            }}
            QTreeWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
                border: none;
                border-right: 1px solid {theme['border']};
            }}
            QTreeWidget::item {{
                padding: 6px 8px;
                border-radius: 6px;
            }}
            QTreeWidget::item:hover {{
                background-color: {theme['surface_hover']};
            }}
            QTreeWidget::item:selected {{
                background-color: {theme['surface_selected']};
                color: {theme['text']};
            }}
            QStatusBar {{
                background-color: {theme['surface']};
                color: {theme['text_secondary']};
                border-top: 1px solid {theme['border']};
            }}
            QSplitter::handle {{
                background-color: {theme['border']};
                width: 2px;
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 12px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme['scrollbar_handle']};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 12px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {theme['scrollbar_handle']};
                border-radius: 6px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {theme['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            QMenuBar {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border-bottom: 1px solid {theme['border']};
            }}
            QMenuBar::item:selected {{
                background-color: {theme['surface_hover']};
            }}
            QMenu {{
                background-color: {theme['background']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
            }}
            QMenu::item:selected {{
                background-color: {theme['surface_selected']};
            }}
        """)