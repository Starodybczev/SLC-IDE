import subprocess
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout
from src.gfx_parser import GFXParser
from src.gfx_canvas import GFXCanvas

class RunActions:
    def __init__(self, main):
        self.main = main

    def run_current_file(self):
        path = self.main.current_file
        if not path:
            QMessageBox.warning(self.main, "Нет файла", "Сначала открой файл!")
            return
        if path.endswith(".py"):
            self.run_python()
        elif path.endswith(".slc"):
            self.run_slc()
        else:
            QMessageBox.warning(self.main, "Ошибка", "Можно запускать только .py и .slc файлы")

    def run_python(self):
        self.main.save_file()
        try:
            result = subprocess.run(["python", self.main.current_file],
                                    capture_output=True, text=True, timeout=10)
            if result.stderr:
                self.main.problems.setPlainText(result.stderr)
            else:
                output = result.stdout.strip() or "— (без вывода) —"
                self.main.problems.setPlainText(output)
        except Exception as e:
            self.main.problems.setPlainText(f"Ошибка: {e}")

    def run_slc(self):
        code = self.main.editor.toPlainText()
        try:
            parser = GFXParser(code)
            objects = parser.parse()
            dialog = QDialog(self.main)
            dialog.setWindowTitle("🧱 SLC Preview")
            layout = QVBoxLayout(dialog)
            canvas = GFXCanvas(objects)
            layout.addWidget(canvas)
            self.main.last_canvas = canvas
            dialog.show()
        except Exception as e:
            self.main.problems.setPlainText(f"⚠️ Ошибка: {e}")

    def run_syntax_check(self):
        if getattr(self.main.editor, "current_language", None) != "Python":
            self.main.problems.clear()
            return
        code = self.main.editor.toPlainText()
        ok, msg, line, col = self.main.editor.check_syntax(code)
        if ok:
            self.main.problems.setPlainText("✔ Syntax OK")
        else:
            self.main.problems.setPlainText(f"✖ {msg} (строка {line}, символ {col})")
