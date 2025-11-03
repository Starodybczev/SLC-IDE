from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit 
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QPainter
from PyQt6.QtCore import Qt, QRect
import ast
from src.highlighters.python_highlighter import PythonHighlighter
from src.highlighters.gfx_highlighter import GFXHighlighter
from src.line_number_area import LineNumberArea

class CodeEditor(QPlainTextEdit):
    TAB_WIDTH = 4

    def __init__(self):
        super().__init__()
        print("🧠 Тип документа в CodeEditor:", type(self.document()))

        self.setFont(QFont("Consolas", 12))
        self.setStyleSheet("background-color:#282a36;color:#f8f8f2;border:none;")
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * self.TAB_WIDTH)

        # === line numbers ===
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)

        self.highlighter = None
        self.current_language = None
        self._err_selection = None

    # === ширина полосы ===
    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2c2c34"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#888"))
                painter.drawText(0, top, self.line_number_area.width() - 4,
                                 self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra = []
        sel = QTextEdit.ExtraSelection()  
        sel.format.setBackground(QColor("#3b3e4a"))
        sel.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        extra.append(sel)
        self.setExtraSelections(extra + (self._err_selection or []))




    def set_language(self, ext: str):
        print(f"🧩 set_language called with ext={ext}")
        print(f"🎨 highlighter assigned: {type(self.highlighter)}")

        """Автоматически выбирает подсветку по расширению файла"""
        ext = ext.lower().strip()  # нормализуем

        if hasattr(self, "highlighter") and self.highlighter:
            self.highlighter.setDocument(None)

        if ext == ".py":
            self.highlighter = PythonHighlighter(self.document())
            self.current_language = "Python"
        elif ext == ".slc":
            self.highlighter = GFXHighlighter(self.document())
            self.current_language = "SLC"
        else:
            self.highlighter = None
            self.current_language = None

        if self.highlighter:
            self.highlighter.rehighlight()
            print(f"🎨 Подсветка активна: {self.current_language}")
        else:
            print("🎨 Подсветка отключена") 





    def check_syntax(self, code: str):
        """Проверяет Python-код на синтаксические ошибки и выделяет строку ошибки"""
        if getattr(self, "current_language", None) != "Python":
            return True, None, None, None

        # 🧹 сбрасываем старое выделение ошибок
        self._err_selection = []
        self.setExtraSelections([])

        try:
            ast.parse(code)
            return True, None, None, None
        except SyntaxError as e:
            # создаём визуальное выделение строки с ошибкой
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(80, 0, 0))  # тёмно-красная подсветка
            sel = QTextEdit.ExtraSelection()
            sel.format = fmt
            sel.cursor = self.textCursor()
            sel.cursor.movePosition(QTextCursor.MoveOperation.Start)
            sel.cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, e.lineno - 1)
            self._err_selection = [sel]
            self.setExtraSelections(self._err_selection)
            return False, e.msg, e.lineno, e.offset   




    def highlight_error(self, line: int, col: int):
        """Подсвечивает строку с ошибкой красным фоном"""
        try:
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(100, 30, 30))  # тёмно-красный оттенок
            sel = QTextEdit.ExtraSelection()
            sel.format = fmt
            sel.cursor = self.textCursor()

            # перемещаем курсор в нужную строку
            sel.cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(line - 1):
                sel.cursor.movePosition(QTextCursor.MoveOperation.Down)

            self._err_selection = [sel]
            self.setExtraSelections(self._err_selection)

        except Exception as e:
            print(f"⚠️ Не удалось подсветить ошибку: {e}")  



    def clear_error_highlight(self):
        """Убирает подсветку ошибок"""
        self._err_selection = []
        self.setExtraSelections([]) 
             


    # === подсветка ошибок и отступы остаются как в прошлой версии ===
