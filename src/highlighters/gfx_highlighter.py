from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression


class GFXHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        print("🟢 GFXHighlighter init started")

        self.rules = []

        # === Форматы ===
        create_fmt = QTextCharFormat()
        create_fmt.setForeground(QColor("#FF79C6"))  # розово-фиолетовый
        create_fmt.setFontWeight(QFont.Weight.Bold)

        list_fmt = QTextCharFormat()
        list_fmt.setForeground(QColor("#8BE9FD"))  # голубой
        list_fmt.setFontWeight(QFont.Weight.Bold)

        style_fmt = QTextCharFormat()
        style_fmt.setForeground(QColor("#50FA7B"))  # салатовый
        style_fmt.setFontWeight(QFont.Weight.Bold)

        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#BD93F9"))  # сиреневый

        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#F1FA8C"))  # жёлтый

        color_fmt = QTextCharFormat()
        color_fmt.setForeground(QColor("#FFB86C"))  # оранжевый

        param_fmt = QTextCharFormat()
        param_fmt.setForeground(QColor("#8BE9FD"))  # голубой

        braces_fmt = QTextCharFormat()
        braces_fmt.setForeground(QColor("#6272A4"))  # серый скобки

        # === Правила ===
        self.rules += [
            # Ключевые слова языка
            (QRegularExpression(r"\bCreate\b"), create_fmt),
            (QRegularExpression(r"\bList\b"), list_fmt),
            (QRegularExpression(r"\bStyle\b"), style_fmt),
            (QRegularExpression(r"\b(Square|Circle|Join|Package)\b"), keyword_fmt),

            # Параметры (x:, y:, width:, height:, color:)
            (QRegularExpression(r"\b[a-zA-Z_]+\s*:"), param_fmt),

            # Цвета #FFFFFF / #FF5733
            (QRegularExpression(r"#(?:[0-9A-Fa-f]{3,6})\b"), color_fmt),

            # Числа
            (QRegularExpression(r"\b\d+(\.\d+)?\b"), number_fmt),

            # Фигурные скобки
            (QRegularExpression(r"[{}()]"), braces_fmt)
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
