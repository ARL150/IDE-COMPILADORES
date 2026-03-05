# Tipos de tokens del lenguaje

TOKEN_TYPES = {
    "KEYWORD": r"\b(if|else|while|int|float|main)\b",
    "IDENTIFIER": r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
    "NUMBER": r"\b\d+(\.\d+)?\b",
    "ASSIGN": r"=",
    "OPERATOR": r"[+\-*/]",
    "SEMICOLON": r";",
    "LPAREN": r"\(",
    "RPAREN": r"\)",
}