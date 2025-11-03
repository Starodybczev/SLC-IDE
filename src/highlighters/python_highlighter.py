from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#ff79c6"))
        keyword_fmt.setFontWeight(QFont.Weight.Bold)

        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("#f1fa8c"))

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6272a4"))
        comment_fmt.setFontItalic(True)

        function_fmt = QTextCharFormat()
        function_fmt.setForeground(QColor("#50fa7b"))

        keywords = [
            "def", "class", "import", "from", "as", "if", "elif", "else",
            "for", "while", "try", "except", "finally", "return", "with",
            "lambda", "yield", "True", "False", "None", "and", "or", "not", "in"
        ]

        self.rules += [(QRegularExpression(rf"\b{kw}\b"), keyword_fmt) for kw in keywords]
        self.rules += [
            (QRegularExpression(r"#.*"), comment_fmt),
            (QRegularExpression(r"\".*\"|'.*'"), string_fmt),
            (QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9_]*(?=\()"), function_fmt),
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
