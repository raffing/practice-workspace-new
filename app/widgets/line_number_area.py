from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QFontDatabase

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFont(editor.font())
        
    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

    def mousePressEvent(self, event):
        self.editor.line_number_area_mouse_press(event)
