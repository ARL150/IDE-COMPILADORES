from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re


class SyntaxHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # ===== KEYWORDS =====
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = [
            "if", "else", "while", "for",
            "return", "int", "float",
            "string", "print"
        ]

        for word in keywords:
            pattern = rf"\b{word}\b"
            self.rules.append((re.compile(pattern), keyword_format))

        # ===== NUMBERS =====
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#008f39"))

        self.rules.append((re.compile(r"\b\d+\b"), number_format))

        # ===== STRINGS =====
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))

        self.rules.append((re.compile(r'"[^"]*"'), string_format))

        # ===== COMMENTS =====
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)

        self.rules.append((re.compile(r"//.*"), comment_format))

    # ------------------------

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)