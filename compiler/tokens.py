# compiler/tokens.py
# Tipos de tokens del lenguaje — sincronizado con lexer.py

TOKEN_TYPES = {
    # Palabras reservadas
    "MAIN":     r"\bmain\b",
    "IF":       r"\bif\b",
    "THEN":     r"\bthen\b",
    "ELSE":     r"\belse\b",
    "END":      r"\bend\b",
    "WHILE":    r"\bwhile\b",
    "DO":       r"\bdo\b",
    "CIN":      r"\bcin\b",
    "COUT":     r"\bcout\b",
    "INT":      r"\bint\b",
    "FLOAT":    r"\bfloat\b",
    "BOOL":     r"\bbool\b",
    "TRUE":     r"\btrue\b",
    "FALSE":    r"\bfalse\b",

    # Operadores compuestos (deben ir antes que los simples)
    "INCREMENT":    r"\+\+",
    "DECREMENT":    r"--",
    "AND":          r"&&",
    "OR":           r"\|\|",
    "SHIFT_RIGHT":  r">>",
    "SHIFT_LEFT":   r"<<",
    "POWER":        r"\^",
    "LE":           r"<=",
    "GE":           r">=",
    "EQ":           r"==",
    "NE":           r"!=",

    # Operadores relacionales simples
    "LT":       r"<",
    "GT":       r">",

    # Operadores aritméticos
    "PLUS":     r"\+",
    "MINUS":    r"-",
    "MULT":     r"\*",
    "DIV":      r"/",
    "MOD":      r"%",

    # Lógico unario
    "NOT":      r"!",

    # Asignación
    "EQUAL":    r"=",

    # Símbolos
    "LPAREN":   r"\(",
    "RPAREN":   r"\)",
    "LBRACE":   r"\{",
    "RBRACE":   r"\}",
    "SEMICOLON": r";",
    "COMMA":    r",",

    # Literales
    "STRING":   r'"[^"]*"',
    "REAL":     r"\d+\.\d+",
    "NUMBER":   r"\d+",

    # Identificadores (al final para no capturar palabras reservadas)
    "ID":       r"[a-zA-Z_][a-zA-Z0-9_]*",
}
