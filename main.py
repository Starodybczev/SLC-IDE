import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QInputDialog,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer
import re
import subprocess

from src.file_tree import FileTree
from src.note_pade import CodeEditor


from src.gfx_parser import GFXParser
from src.gfx_canvas import GFXCanvas
from PyQt6.QtWidgets import QDialog, QVBoxLayout


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SLC IDE 🧩")
        self.resize(1000, 600)

        # === Горизонтальный сплиттер: FileTree | Editor
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

        # === Вертикальный сплиттер: Editor + Problems
        outer_split = QSplitter(Qt.Orientation.Vertical, self)
        outer_split.addWidget(main_split)
        outer_split.addWidget(self.problems)
        outer_split.setSizes([520, 120])
        self.setCentralWidget(outer_split)

        # --- Сигналы
        self.file_tree.folderDropped.connect(self.on_folder_dropped)
        self.file_tree.fileOpened.connect(self.open_file_in_editor)

        # --- Меню
        self._create_menu()

        # --- Таймер автопроверки Python
        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.setInterval(500)
        self.lint_timer.timeout.connect(self.run_syntax_check)
        self.editor.textChanged.connect(lambda: self.lint_timer.start())

        self.current_file = None

    # === Верхнее меню ===
    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        open_action = QAction("Открыть папку…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_folder_dialog)

        new_file_action = QAction("Создать файл", self)
        new_file_action.setShortcut("Ctrl+N")
        new_file_action.triggered.connect(lambda: self.create_item(is_folder=False))

        new_folder_action = QAction("Создать папку", self)
        new_folder_action.setShortcut("Ctrl+Shift+N")
        new_folder_action.triggered.connect(lambda: self.create_item(is_folder=True))

        save_action = QAction("Сохранить", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)

        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        file_menu.addActions([open_action, new_file_action, new_folder_action, save_action])
        file_menu.addSeparator()
        file_menu.addAction(exit_action)


        run_action = QAction("▶️ Запустить", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_code)
        file_menu.addAction(run_action)

        run_action = QAction("▶️ Запуск", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_gfx_code)

        menubar.addAction(run_action)

    # === Открыть папку ===
    def open_folder_dialog(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку проекта")
        if path:
            self.file_tree.load_folder(path)
            self.setWindowTitle(f"SLC IDE — {os.path.basename(path)}")

    # === Создать файл или папку ===
    def create_item(self, is_folder=False):
        if not self.file_tree.root_path:
            QMessageBox.warning(self, "Нет проекта", "Сначала открой папку проекта!")
            return

        title = "Создать папку" if is_folder else "Создать файл"
        placeholder = "Имя папки:" if is_folder else "Имя файла:"

        name, ok = QInputDialog.getText(self, title, placeholder)
        if not ok or not name.strip():
            return

        name = name.strip()

        reserved = {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}
        if name.upper() in reserved:
            QMessageBox.warning(self, "Ошибка", "Это зарезервированное имя в Windows!")
            return

        if is_folder:
            pattern = r"^[A-Za-z0-9_\-]+$"
        else:
            pattern = r"^[A-Za-z0-9_\-]+\.[A-Za-z0-9]+$"

        if not re.match(pattern, name):
            msg = (
                "Имя файла должно содержать расширение (например main.py)"
                if not is_folder
                else "Имя папки может содержать только латиницу, цифры, -, _"
            )
            QMessageBox.warning(self, "Ошибка", msg)
            return

        new_path = os.path.join(self.file_tree.root_path, name)
        if os.path.exists(new_path):
            QMessageBox.warning(self, "Ошибка", "Такое имя уже существует!")
            return

        try:
            if is_folder:
                os.makedirs(new_path, exist_ok=True)
            else:
                open(new_path, "w", encoding="utf-8").close()
            self.file_tree.load_folder(self.file_tree.root_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    # === Событие дропа ===
    def on_folder_dropped(self, path: str):
        self.setWindowTitle(f"SLC IDE — {os.path.basename(path)}")
        print("🪶 Папка подгружена:", path)

    # === Открыть файл ===
    def open_file_in_editor(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            self.editor.blockSignals(True)
            self.editor.setPlainText(text)
            self.editor.blockSignals(False)
            self.editor.setReadOnly(False)
            self.current_file = path

            ext = os.path.splitext(path)[1]
            self.editor.set_language(ext)

            if ext == ".slc":
                from gfx_parser import GFXParser
                parser = GFXParser(self.editor.toPlainText())
                result = parser.parse()
                print("📦 SLC структура:", result)

            self.setWindowTitle(f"SLC IDE — {os.path.basename(path)}")

            # Проверить синтаксис сразу
            self.run_syntax_check()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    # === Автопроверка синтаксиса ===
    def run_syntax_check(self):
        if getattr(self.editor, "current_language", None) != "Python":
            self.editor.clear_error_highlight()
            self.problems.clear()
            return

        code = self.editor.toPlainText()
        ok, msg, line, col = self.editor.check_syntax(code)
        if ok:
            self.editor.clear_error_highlight()
            self.problems.setPlainText("✔ Syntax OK")
        else:
            self.editor.highlight_error(line, col)
            self.problems.setPlainText(f"✖ {msg}  (line {line}, col {col})")

    # === Сохранить ===
    def save_file(self):
        if not self.current_file:
            QMessageBox.warning(self, "Нет файла", "Сначала открой файл!")
            return

        # проверка перед сохранением
        if getattr(self.editor, "current_language", None) == "Python":
            ok, msg, line, col = self.editor.check_syntax(self.editor.toPlainText())
            if not ok:
                self.editor.highlight_error(line, col)
                self.problems.setPlainText(f"✖ {msg}  (line {line}, col {col})")
                QMessageBox.warning(self, "Ошибка синтаксиса", f"{msg}\n(line {line}, col {col})")
                return

        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.problems.setPlainText("💾 Saved OK")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")



    def run_code(self):
        """Запускает текущий файл, если это .py"""
        if not self.current_file:
            QMessageBox.warning(self, "Нет файла", "Сначала открой Python-файл!")
            return

        if not self.current_file.endswith(".py"):
            QMessageBox.information(self, "Запуск", "Поддерживается только Python.")
            return

        self.save_file()  # сохранить перед запуском

        self.problems.clear()
        self.problems.setPlainText("▶️ Запуск кода...\n")

        try:
            result = subprocess.run(
                ["python", self.current_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout.strip()
            errors = result.stderr.strip()

            if errors:
                self.problems.setPlainText(f"❌ Ошибка:\n{errors}")
            else:
                self.problems.setPlainText(f"✅ Результат:\n{output if output else '— (без вывода) —'}")
        except Exception as e:
            self.problems.setPlainText(f"⚠️ Ошибка запуска: {e}") 




    def run_gfx_code(self):
        if not hasattr(self, "current_file") or not self.current_file.endswith(".slc"):
            QMessageBox.warning(self, "Ошибка", "Можно запускать только .slc файлы")
            return

        code = self.editor.toPlainText()
        parser = GFXParser(code)
        objects = parser.parse()

        win = QDialog(self)
        win.setWindowTitle("🧱 SLC Preview")
        layout = QVBoxLayout(win)
        layout.addWidget(GFXCanvas(objects))
        win.resize(600, 500)
        win.exec()               


if __name__ == "__main__":
    app = QApplication([])
    window = Main()
    window.show()
    app.exec()
    