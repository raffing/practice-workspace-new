import sys
from PySide6.QtWidgets import QApplication
from app.main_window import PracticeWorkspace

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Practice Workspace")
    app.setOrganizationName("PracticeWorkspace")
    window = PracticeWorkspace()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
