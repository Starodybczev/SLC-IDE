from PyQt6.QtGui import QAction

def create_menu(window):
    menubar = window.menuBar()
    file_menu = menubar.addMenu("Файл")

    open_action = QAction("Открыть папку…", window)
    open_action.setShortcut("Ctrl+O")
    open_action.triggered.connect(window.file_actions.open_folder_dialog)

    new_file_action = QAction("Создать файл", window)
    new_file_action.setShortcut("Ctrl+N")
    new_file_action.triggered.connect(lambda: window.file_actions.create_item(is_folder=False))

    new_folder_action = QAction("Создать папку", window)
    new_folder_action.setShortcut("Ctrl+Shift+N")
    new_folder_action.triggered.connect(lambda: window.file_actions.create_item(is_folder=True))

    save_action = QAction("Сохранить", window)
    save_action.setShortcut("Ctrl+S")
    save_action.triggered.connect(window.file_actions.save_file)

    export_action = QAction("Экспортировать как изображение…", window)
    export_action.setShortcut("Ctrl+Shift+S")
    export_action.triggered.connect(window.file_actions.export_gfx_canvas)

    exit_action = QAction("Выход", window)
    exit_action.setShortcut("Ctrl+Q")
    exit_action.triggered.connect(window.close)

    run_action = QAction("▶️ Запустить", window)
    run_action.setShortcut("F5")
    run_action.triggered.connect(window.run_actions.run_current_file)

    file_menu.addActions([
        open_action, new_file_action, new_folder_action, save_action, export_action
    ])
    file_menu.addSeparator()
    file_menu.addAction(exit_action)
    menubar.addAction(run_action)
