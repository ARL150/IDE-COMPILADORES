from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re


class SyntaxHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # =========================
        # KEYWORDS
        # =========================

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = [
            "if", "else", "end", "do", "while",
            "switch", "case",
            "int", "float", "main",
            "cin", "cout"
        ]

        for word in keywords:
            self.rules.append((re.compile(rf"\b{word}\b"), keyword_format))

        # =========================
        # IDENTIFIERS
        # =========================

        identifier_format = QTextCharFormat()
        identifier_format.setForeground(QColor("#9CDCFE"))

        self.rules.append((re.compile(r"\b[a-zA-Z_]\w*\b"), identifier_format))

        # =========================
        # NUMBERS
        # =========================

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))

        self.rules.append((re.compile(r"\b\d+\b"), number_format))
        self.rules.append((re.compile(r"\b\d+\.\d+\b"), number_format))

        # =========================
        # STRINGS
        # =========================

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))

        self.rules.append((re.compile(r'"[^"]*"'), string_format))

        # =========================
        # CHAR
        # =========================

        char_format = QTextCharFormat()
        char_format.setForeground(QColor("#D7BA7D"))

        self.rules.append((re.compile(r"'.'"), char_format))

        # =========================
        # COMMENTS
        # =========================

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)

        self.rules.append((re.compile(r"//.*"), comment_format))
        self.rules.append((re.compile(r"/\*[\s\S]*?\*/"), comment_format))

        # =========================
        # ARITHMETIC OPERATORS
        # =========================

        arithmetic_format = QTextCharFormat()
        arithmetic_format.setForeground(QColor("#D4D4D4"))
        arithmetic_format.setFontWeight(QFont.Weight.Bold)

        arithmetic_ops = [
            r"\+\+",
            r"--",
            r"\+",
            r"-",
            r"\*",
            r"/",
            r"%",
            r"\^"
        ]

        for op in arithmetic_ops:
            self.rules.append((re.compile(op), arithmetic_format))

        # =========================
        # RELATIONAL OPERATORS
        # =========================

        relational_format = QTextCharFormat()
        relational_format.setForeground(QColor("#C586C0"))
        relational_format.setFontWeight(QFont.Weight.Bold)

        relational_ops = [
            r"<=",
            r">=",
            r"==",
            r"!=",
            r"<",
            r">"
        ]

        for op in relational_ops:
            self.rules.append((re.compile(op), relational_format))

        # =========================
        # LOGICAL OPERATORS
        # =========================

        logical_format = QTextCharFormat()
        logical_format.setForeground(QColor("#C586C0"))

        logical_ops = [
            r"&&",
            r"\|\|",
            r"!"
        ]

        for op in logical_ops:
            self.rules.append((re.compile(op), logical_format))

        # =========================
        # ASSIGNMENT
        # =========================

        assign_format = QTextCharFormat()
        assign_format.setForeground(QColor("#FF8C00"))

        self.rules.append((re.compile(r"="), assign_format))

        # =========================
        # PARENTHESES
        # =========================

        paren_format = QTextCharFormat()
        paren_format.setForeground(QColor("#FFD700"))

        self.rules.append((re.compile(r"\("), paren_format))
        self.rules.append((re.compile(r"\)"), paren_format))

        # =========================
        # BRACES
        # =========================

        brace_format = QTextCharFormat()
        brace_format.setForeground(QColor("#DA70D6"))

        self.rules.append((re.compile(r"\{"), brace_format))
        self.rules.append((re.compile(r"\}"), brace_format))

        # =========================
        # SEMICOLON
        # =========================

        semicolon_format = QTextCharFormat()
        semicolon_format.setForeground(QColor("#00FFFF"))

        self.rules.append((re.compile(r";"), semicolon_format))

        # =========================
        # COMMA
        # =========================

        comma_format = QTextCharFormat()
        comma_format.setForeground(QColor("#00CED1"))

        self.rules.append((re.compile(r","), comma_format))

    # ==================================

    def highlightBlock(self, text):

        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)