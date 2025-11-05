import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QInputDialog
from PyQt6.QtCore import QTimer
from src.gfx_parser import GFXParser

class FileActions:
    def __init__(self, main):
        self.main = main

    def open_folder_dialog(self):
        path = QFileDialog.getExistingDirectory(self.main, "Выберите папку проекта")
        if path:
            self.main.file_tree.load_folder(path)
            self.main.setWindowTitle(f"SLC IDE — {os.path.basename(path)}")

    def create_item(self, is_folder=False):
        root = self.main.file_tree.root_path
        if not root:
            QMessageBox.warning(self.main, "Нет проекта", "Сначала открой папку проекта!")
            return

        if is_folder:
            name, ok = QInputDialog.getText(self.main, "Создать папку", "Имя папки:")
            if not ok or not name.strip():
                return
            new_path = os.path.join(root, name.strip())
            if os.path.exists(new_path):
                QMessageBox.warning(self.main, "Ошибка", "Такая папка уже существует!")
                return
            os.makedirs(new_path, exist_ok=True)
            QTimer.singleShot(100, lambda: self.main.file_tree.load_folder(root))
            return

        # создание файла
        dialog = QDialog(self.main)
        dialog.setWindowTitle("Создать файл")
        layout = QVBoxLayout(dialog)
        lbl = QLabel("Имя файла:")
        layout.addWidget(lbl)
        name_input = QInputDialog()
        name_input.setInputMode(QInputDialog.InputMode.TextInput)
        layout.addWidget(name_input)
        lbl2 = QLabel("Тип:")
        layout.addWidget(lbl2)
        combo = QComboBox()
        combo.addItems([".slc", ".py", ".txt"])
        layout.addWidget(combo)
        btn = QPushButton("Создать")
        layout.addWidget(btn)
        btn.clicked.connect(dialog.accept)
        dialog.exec()
        name = name_input.textValue().strip()
        if not name:
            return
        ext = combo.currentText()
        new_path = os.path.join(root, name + ext)
        with open(new_path, "w", encoding="utf-8") as f:
            if ext == ".slc":
                f.write(
                    f"Create List {name}() {{\n\n"
                    f"    Create Square Sq1(x:100, y:100) {{\n"
                    f"        Style {{ color:red; }}\n"
                    f"    }}\n"
                    f"}}"
                )
            elif ext == ".py":
                f.write(f"# {name}.py\nprint('Hello from {name}')")
            else:
                f.write(f"{name} file created.")
        self.main.file_tree.load_folder(root)

    def open_file_in_editor(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            self.main.editor.blockSignals(True)
            self.main.editor.setPlainText(text)
            self.main.editor.blockSignals(False)
            self.main.editor.setReadOnly(False)
            self.main.current_file = path

            ext = os.path.splitext(path)[1]
            self.main.editor.set_language(ext)

        # Проверим синтаксис сразу (только для .py)
            if ext == ".py":
                self.main.run_actions.run_syntax_check()

            self.main.setWindowTitle(f"SLC IDE — {os.path.basename(path)}")

        except Exception as e:
            QMessageBox.critical(self.main, "Ошибка", f"Не удалось открыть файл:\n{e}")


    def save_file(self):
        if not self.main.current_file:
            QMessageBox.warning(self.main, "Нет файла", "Сначала открой файл!")
            return
        with open(self.main.current_file, "w", encoding="utf-8") as f:
            f.write(self.main.editor.toPlainText())
        self.main.problems.setPlainText("💾 Saved OK")

    def export_gfx_canvas(self):
        if hasattr(self.main, "last_canvas") and self.main.last_canvas:
            self.main.last_canvas.export_image(self.main)
        else:
            QMessageBox.information(self.main, "Нет Canvas", "Сначала запусти .slc файл (F5).")

    def on_folder_dropped(self, path):
        self.main.setWindowTitle(f"SLC IDE — {os.path.basename(path)}")
