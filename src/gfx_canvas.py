from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPixmap
from PyQt6.QtCore import QRect
import os
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtSvg import QSvgGenerator



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




    def export_image(self, parent=None):
        """Сохраняет содержимое Canvas в PNG / JPG / SVG"""
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Сохранить как изображение",
            "",
            "PNG (*.png);;JPEG (*.jpg);;SVG (*.svg)"
        )
        if not file_path:
            return

        # Определяем формат
        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".png", ".jpg", ".jpeg"]:
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            pixmap.save(file_path)
            print(f"🖼 Сохранено как {file_path}")

        elif ext == ".svg":
            generator = QSvgGenerator()
            generator.setFileName(file_path)
            generator.setSize(self.size())
            generator.setViewBox(QRect(0, 0, self.width(), self.height()))
            generator.setTitle("SLC Export")
            generator.setDescription("Generated from SLC Canvas")

            painter = QPainter(generator)
            self.render(painter)
            painter.end()
            print(f"📐 Сохранено как SVG: {file_path}")            
