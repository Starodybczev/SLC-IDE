import os, subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from src.file_tree import FileTree
from src.note_pade import CodeEditor

from ui.menu_actions import create_menu
from ui.file_actions import FileActions
from ui.run_actions import RunActions


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        icon_path = os.path.join(os.path.dirname(__file__), "..", "src", "assets", "icons", "goose_ide.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("SLC IDE 🧩")
        self.resize(1000, 600)

        # === Горизонтальный сплиттер
        main_split = QSplitter(self)
        main_split.setHandleWidth(2)
        self.file_tree = FileTree()
        self.editor = CodeEditor()
        main_split.addWidget(self.file_tree)
        main_split.addWidget(self.editor)
        main_split.setSizes([250, 750])

        # === Панель “Проблемы” снизу
        self.problems = QTextEdit()
        self.problems.setReadOnly(True)
        self.problems.setFixedHeight(120)
        self.problems.setStyleSheet("background:#1e1f29;color:#ffd2d2;border:none;")

        # === Вертикальный сплиттер
        outer_split = QSplitter(Qt.Orientation.Vertical, self)
        outer_split.addWidget(main_split)
        outer_split.addWidget(self.problems)
        outer_split.setSizes([520, 120])
        self.setCentralWidget(outer_split)

        # --- Подключение модулей действий
        self.file_actions = FileActions(self)
        self.run_actions = RunActions(self)

        # --- Сигналы
        self.file_tree.folderDropped.connect(self.file_actions.on_folder_dropped)
        self.file_tree.fileOpened.connect(self.file_actions.open_file_in_editor)

        # --- Меню
        create_menu(self)

        # --- Таймер проверки
        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.setInterval(500)
        self.lint_timer.timeout.connect(self.run_actions.run_syntax_check)
        self.editor.textChanged.connect(lambda: self.lint_timer.start())

        self.current_file = None
