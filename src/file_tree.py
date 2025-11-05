from PyQt6.QtWidgets import QWidget, QTreeView, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QFileSystemModel, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QDir, QPoint
from PyQt6.QtWidgets import QMenu, QMessageBox, QFileIconProvider  # ← добавь сюда
import os
import shutil
import tempfile

class FileTree(QWidget):
    folderDropped = pyqtSignal(str)
    fileOpened = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        base = os.path.join(os.path.dirname(__file__), "assets", "icons")
        self.slc_icon = QIcon(os.path.join(base, "slc_icon.png"))
        self.setObjectName("FileTree")

        # ✅ Разрешаем drag'n'drop только на контейнере
        self.setAcceptDrops(True)

        # QFileSystemModel — модель файлов
        self.model = QFileSystemModel(self)
        self.model.setIconProvider(CustomIconProvider())
        self.model.setReadOnly(False)
        self.model.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )

        # QTreeView — дерево файлов
        self.tree = QTreeView()
        self.tree.setModel(None)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.setHeaderHidden(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragEnabled(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.doubleClicked.connect(self.on_item_double_click)

        self.tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        # 🌙 Фиксируем стиль, чтобы на всех Windows он был одинаковым
        self.tree.setStyleSheet("""
            QTreeView {
                background-color: #1e1f22;
                color: #f8f8f2;
                border: none;
                outline: 0;
                selection-background-color: #44475a;
                selection-color: #ffffff;
            }
            QTreeView::item:hover {
                background-color: #333;
            }
            QTreeView::item:selected {
                background-color: #44475a;
                color: #ffffff;
            }
            QScrollBar:vertical {
                background: #1e1f22;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)


        # Label — баннер-заглушка
        self.banner = QLabel("🪶 Перетащи сюда папку проекта")
        self.banner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.banner)
        layout.addWidget(self.tree)

        self.root_path = None
        self._update_visibility()

    # --- DnD на уровне контейнера ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        print("🎯 DropEvent path:", path)
        if os.path.isdir(path):
            self.load_folder(path)
            self.folderDropped.emit(path)

    # --- Загрузка папки ---
    def load_folder(self, path: str):
        if not os.path.isdir(path):
            print("❌ Неверный путь:", path)
            return

        print("📂 Загружаю:", path)

    # 🧹 сброс предыдущей модели
        self.tree.setModel(None)
        QApplication.processEvents()

    # перезадаём модель и путь
        self.model.setRootPath("")
        self.model.setRootPath(path)
        self.tree.setModel(self.model)

    # ⚡️ получаем индекс и ставим его как корень
        root_index = self.model.index(path)
        print("📁 Всего элементов:", self.model.rowCount(root_index))
        print("   • индекс валиден:", root_index.isValid())

    # 💥 просто показываем саму папку как корень
        self.tree.setRootIndex(root_index)
        self.tree.expand(root_index)
        self.tree.setCurrentIndex(root_index)
        self.tree.setRootIsDecorated(True)
        self.tree.repaint()

    # скрываем лишние колонки
        for col in (1, 2, 3):
            self.tree.setColumnHidden(col, True)

        self.root_path = path
        self._update_visibility()
        print("✅ Папка отображена в дереве:", path)





    def open_context_menu(self, position: QPoint):
        """Контекстное меню по ПКМ"""
        index = self.tree.indexAt(position)
        menu = QMenu(self)

    # Определяем, на что кликнули — файл или папку
        rename_item = None
        delete_item = None
        path = None
        is_folder = False

        if index.isValid():
            path = self.model.filePath(index)
            is_folder = os.path.isdir(path)

    # --- Действия
        create_file = menu.addAction("📝 Создать файл")
        create_folder = menu.addAction("📁 Создать папку")

        if index.isValid():
            menu.addSeparator()
            rename_item = menu.addAction("✏️ Переименовать")
            delete_item = menu.addAction("🗑️ Удалить")

        action = menu.exec(self.tree.viewport().mapToGlobal(position))

    # --- Реакции
        if action == create_file:
            self.window().create_item(is_folder=False)
        elif action == create_folder:
            self.window().create_item(is_folder=True)
        elif action == rename_item and path:
            self.rename_item(path)
        elif action == delete_item and path:
            self.delete_item(path)



    def delete_item(self, path: str):
        reply = QMessageBox.question(
            self,
            "Удалить",
            f"Точно удалить '{os.path.basename(path)}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.load_folder(self.root_path)
                print(f"🗑️ Удалено: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def rename_item(self, path: str):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self, "Переименовать", "Новое имя:", text=os.path.basename(path)
        )
        if ok and name.strip():
            new_path = os.path.join(os.path.dirname(path), name.strip())
            os.rename(path, new_path)
            self.load_folder(self.root_path)
            print(f"✏️ Переименовано: {path} → {new_path}")



    # --- Вспомогательное ---
    def clear_tree(self):
        self.tree.setModel(None)
        self.root_path = None
        self._update_visibility()

    def _update_visibility(self):
        empty = self.tree.model() is None
        self.banner.setVisible(empty)
        self.tree.setVisible(not empty)


    def on_item_double_click(self, index):
        """Открытие файла по двойному клику"""
        path = self.model.filePath(index)
        if os.path.isfile(path):
            print(f"📝 Открываю файл: {path}")
            self.fileOpened.emit(path)



from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileIconProvider

class CustomIconProvider(QFileIconProvider):
    def __init__(self):
        super().__init__()
        base = os.path.join(os.path.dirname(__file__), "assets", "icons")
        self.slc_icon = QIcon(os.path.join(base, "slc_icon.png"))

    def icon(self, info):
        from PyQt6.QtWidgets import QFileIconProvider

        # Если Qt передаёт тип (enum)
        if isinstance(info, QFileIconProvider.IconType):
            return super().icon(info)

        # Если это папка → стандартная системная
        try:
            if info.isDir():
                return super().icon(QFileIconProvider.IconType.Folder)
            if info.suffix().lower() == "slc":
                return self.slc_icon
        except Exception as e:
            print(f"⚠️ Ошибка в IconProvider: {e}")
        return super().icon(info)
      