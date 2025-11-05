from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QPainter
from PyQt6.QtCore import Qt, QRect
import re
from src.highlighters.python_highlighter import PythonHighlighter
from src.highlighters.gfx_highlighter import GFXHighlighter
from src.line_number_area import LineNumberArea


class CodeEditor(QPlainTextEdit):
    TAB_WIDTH = 4

    def __init__(self):
        super().__init__()
        self.setFont(QFont("Consolas", 12))
        self.setStyleSheet("background-color:#282a36;color:#f8f8f2;border:none;")
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * self.TAB_WIDTH)

        # линия слева (нумерация)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)

        # состояние
        self.highlighter = None
        self.current_language = None
        self._err_selection = []
        self._diagnostics = []

    # ======= Линии =======
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
        num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        diag_lines = {d["line"] for d in self._diagnostics}
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                n = str(num + 1)
                if (num + 1) in diag_lines:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor("#ff5555"))
                    painter.drawEllipse(self.line_number_area.width() - 8, top + 6, 6, 6)
                painter.setPen(QColor("#888"))
                painter.drawText(0, top, self.line_number_area.width() - 4,
                                 self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, n)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            num += 1

    def highlight_current_line(self):
        extra = []
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor("#3b3e4a"))
        sel.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        extra.append(sel)
        self.setExtraSelections(extra + self._err_selection)

    # ======= Подсветка =======
    def set_language(self, ext: str):
        ext = ext.lower().strip()
        if self.highlighter:
            self.highlighter.setDocument(None)
        if ext == ".py":
            self.highlighter = PythonHighlighter(self.document())
            self.current_language = "Python"
        elif ext in [".gfx", ".slc"]:
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

    # ======= Проверка синтаксиса SLC =======
    def check_syntax(self, code: str):
        """Простая проверка синтаксиса для SLC"""
        if getattr(self, "current_language", None) != "SLC":
            return True, None, None, None

        self.clear_diagnostics()

        lines = code.splitlines()
        required_keywords = ["Create", "Style", "{", "}"]
        errors = []

        for i, line in enumerate(lines, start=1):
            text = line.strip()

            if not text:
                continue

            # Ошибка: нет фигурной скобки
            if re.search(r"Create\s+\w+", text) and not text.endswith("{"):
                errors.append((i, len(text), "❌ Ожидается '{' после команды Create"))

            # Ошибка: Style без фигурных скобок
            if text.startswith("Style") and "{" not in text:
                errors.append((i, len(text), "❌ Пропущена '{' после Style"))

            # Ошибка: неизвестная команда
            if not any(text.startswith(k) for k in ["Create", "Style", "}", "{"]) and not text.startswith("//"):
                if ":" not in text and not text.endswith("}"):
                    errors.append((i, 1, f"⚠ Неизвестная инструкция: {text}"))

        if errors:
            for line, col, msg in errors:
                self.show_diagnostic(line, col, msg)
            return False, errors[0][2], errors[0][0], errors[0][1]

        return True, None, None, None

    # ======= Отрисовка ошибки =======
    def show_diagnostic(self, line: int, col: int, message: str, length: int = 1):
        block = self.document().findBlockByNumber(line - 1)
        if not block.isValid():
            return
        start = block.position() + col - 1
        end = start + length

        fmt = QTextCharFormat()
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        fmt.setUnderlineColor(QColor("#ff5555"))

        sel = QTextEdit.ExtraSelection()
        cur = self.textCursor()
        cur.setPosition(start)
        cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        sel.cursor = cur
        sel.format = fmt

        self._err_selection.append(sel)
        self.setExtraSelections(self._err_selection)
        rect = self.cursorRect(cur)
        self._diagnostics.append({"line": line, "y": rect.top(), "message": message})
        self.viewport().update()

    def clear_diagnostics(self):
        self._err_selection = []
        self._diagnostics = []
        self.setExtraSelections([])
        self.viewport().update()

    # ======= Отрисовка текста ошибки =======
    def paintEvent(self, e):
        super().paintEvent(e)
        if not self._diagnostics:
            return
        p = QPainter(self.viewport())
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for d in self._diagnostics:
            msg = d["message"]
            y = d["y"]
            p.setFont(QFont("Consolas", 10))
            fm = p.fontMetrics()
            w = fm.horizontalAdvance(msg)
            h = fm.height()
            pad = 6
            bg = QRect(12 + self.line_number_area_width(), y - h, w + pad * 2, h + pad)
            p.setPen(QColor("#ff5555"))
            p.setBrush(QColor(255, 0, 0, 40))
            p.drawRoundedRect(bg, 6, 6)
            p.setPen(QColor("#ffaaaa"))
            p.drawText(bg.adjusted(pad, 0, -pad, 0), Qt.AlignmentFlag.AlignVCenter, msg)



    def highlight_error(self, line: int, col: int = 0, msg: str = ""):
        
        try:
            from PyQt6.QtGui import QTextCharFormat

            fmt = QTextCharFormat()
            fmt.setUnderlineColor(QColor("#ff4d4d"))
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
            fmt.setBackground(QColor(40, 0, 0))

            sel = QTextEdit.ExtraSelection()
            sel.format = fmt
            sel.cursor = self.textCursor()

            sel.cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(line - 1):
                sel.cursor.movePosition(QTextCursor.MoveOperation.Down)
            self._err_selection = [sel]

            self.setExtraSelections(self._err_selection)
            print(f"🔴 Ошибка подсвечена на строке {line}")

        except Exception as e:
            print(f"⚠️ Ошибка в highlight_error: {e}")

    def clear_error_highlight(self):   
        """Убирает подсветку ошибок"""
        self._err_selection = []
        self.setExtraSelections([])
        
