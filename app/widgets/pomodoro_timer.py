"""Timer Pomodoro per task in corso."""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer, Signal

class PomodoroTimer(QWidget):
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._seconds = 25 * 60  # 25 minuti
        self._remaining = self._seconds
        self._running = False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        self.label = QLabel("🍅 25:00")
        self.label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.label)
        
        self.start_btn = QPushButton("▶")
        self.start_btn.setFixedSize(28, 28)
        self.start_btn.setToolTip("Avvia/Pausa")
        self.start_btn.clicked.connect(self._toggle)
        layout.addWidget(self.start_btn)
        
        self.reset_btn = QPushButton("↺")
        self.reset_btn.setFixedSize(28, 28)
        self.reset_btn.setToolTip("Reset")
        self.reset_btn.clicked.connect(self._reset)
        layout.addWidget(self.reset_btn)
        
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
    
    def _toggle(self):
        if self._running:
            self._timer.stop()
            self.start_btn.setText("▶")
        else:
            self._timer.start(1000)
            self.start_btn.setText("⏸")
        self._running = not self._running
    
    def _reset(self):
        self._timer.stop()
        self._running = False
        self._remaining = self._seconds
        self.start_btn.setText("▶")
        self._update_label()
    
    def _tick(self):
        self._remaining -= 1
        self._update_label()
        if self._remaining <= 0:
            self._timer.stop()
            self._running = False
            self.start_btn.setText("▶")
            self.finished.emit()
    
    def _update_label(self):
        mins = self._remaining // 60
        secs = self._remaining % 60
        self.label.setText(f"🍅 {mins:02d}:{secs:02d}")