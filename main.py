import sys, os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
import ctypes

if __name__ == "__main__":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SLC.IDE.App")
    except Exception:
        pass

    app = QApplication([])

    icon_path = os.path.join(os.path.dirname(__file__), "src", "assets", "icons", "goose_ide.ico")
    app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    app.exec()
