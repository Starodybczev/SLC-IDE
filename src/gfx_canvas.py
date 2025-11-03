from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import QRect

class GFXCanvas(QWidget):
    def __init__(self, gfx_objects):
        super().__init__()
        self.objects = gfx_objects
        self.setMinimumSize(400, 400)
        self.setStyleSheet("background-color:#1E1E1E; border:1px solid #333;")

    def paintEvent(self, event):
        painter = QPainter(self)
        for obj in self.objects:
            style = obj.get("style", {})
            params = obj.get("params", {})
            color = QColor(style.get("color", "#FFFFFF"))
            width = int(style.get("width", 50))
            height = int(style.get("height", 50))
            x = params.get("x", 0)
            y = params.get("y", 0)

            painter.setBrush(QBrush(color))
            painter.setPen(QColor("#00000000"))

            if obj["type"].lower() == "square":
                painter.drawRect(QRect(x, y, width, height))
            elif obj["type"].lower() == "circle":
                painter.drawEllipse(x, y, width, height)
