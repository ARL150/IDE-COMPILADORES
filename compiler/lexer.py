# compiler/lexer.py

import re

# DEFINICION DE TOKENS
TOKEN_TYPES = {

    # numeros
    "REAL": r"\d+\.\d+",
    "INVALID_REAL": r"\d+\.(?!\d)",
    "NUMBER": r"\d+",

    # palabras reservadas
    "IF": r"\bif\b",
    "ELSE": r"\belse\b",
    "END": r"\bend\b",
    "DO": r"\bdo\b",
    "WHILE": r"\bwhile\b",
    "SWITCH": r"\bswitch\b",
    "CASE": r"\bcase\b",
    "INT": r"\bint\b",
    "FLOAT": r"\bfloat\b",
    "MAIN": r"\bmain\b",
    "CIN": r"\bcin\b",
    "COUT": r"\bcout\b",

    # identificadores
    "ID": r"[a-zA-Z_]\w*",

    # operadores aritmeticos
    "INCREMENT": r"\+\+",
    "DECREMENT": r"--",
    "PLUS": r"\+",
    "MINUS": r"-",
    "MULT": r"\*",
    "DIV": r"/",
    "MOD": r"%",
    "POWER": r"\^",

    # operadores relacionales
    "LE": r"<=",
    "GE": r">=",
    "EQ": r"==",
    "NE": r"!=",
    "LT": r"<",
    "GT": r">",

    # operadores logicos
    "AND": r"&&",
    "OR": r"\|\|",
    "NOT": r"!",

    # asignacion
    "EQUAL": r"=",

    # simbolos
    "LPAREN": r"\(",
    "RPAREN": r"\)",
    "LBRACE": r"\{",
    "RBRACE": r"\}",
    "COMMA": r",",
    "SEMICOLON": r";",

    # cadenas
    "STRING": r"\".*?\"",

    # caracteres
    "CHAR": r"\'.\'",

    # comentarios
    "COMMENT_LINE": r"//.*",
    "COMMENT_MULTI": r"/\*[\s\S]*?\*/",

    # caracter desconocido
    "UNKNOWN": r"."
}

# COMPILAR REGEX (mantiene el orden)
TOKEN_REGEX = [
    (token, re.compile(pattern))
    for token, pattern in TOKEN_TYPES.items()
]

# Operadores dobles que pueden venir separados por espacios o saltos de línea
COMPOUND_OPERATORS = {
    "++": "INCREMENT",
    "--": "DECREMENT",
    "<=": "LE",
    ">=": "GE",
    "==": "EQ",
    "!=": "NE",
    "&&": "AND",
    "||": "OR"
}


def advance_position(text, line, column):
    """
    Avanza line/column recorriendo exactamente el texto consumido.
    """
    for ch in text:
        if ch == "\n":
            line += 1
            column = 1
        else:
            column += 1
    return line, column


def match_compound_operator(code, position):
    """
    Intenta reconocer operadores compuestos aunque estén separados
    por espacios o saltos de línea.
    """
    if position >= len(code):
        return None

    first = code[position]
    candidates = [op for op in COMPOUND_OPERATORS if op[0] == first]

    for op in candidates:
        second = op[1]
        i = position + 1

        while i < len(code) and code[i].isspace():
            i += 1

        if i < len(code) and code[i] == second:
            consumed = code[position:i + 1]
            return COMPOUND_OPERATORS[op], consumed, op

    return None


# FUNCION PRINCIPAL DEL LEXER
def tokenize(code):

    tokens = []
    errors = []

    position = 0
    line = 1
    column = 1

    while position < len(code):

        # manejar espacios
        if code[position].isspace():

            if code[position] == "\n":
                line += 1
                column = 1
            else:
                column += 1

            position += 1
            continue

        # =========================
        # IGNORAR COMENTARIOS
        # =========================

        # comentario de linea: // ...
        if code.startswith("//", position):
            end = code.find("\n", position)
            if end == -1:
                comment_text = code[position:]
                position = len(code)
            else:
                comment_text = code[position:end]
                position = end

            line, column = advance_position(comment_text, line, column)
            continue

        # comentario de bloque: /* ... */
        if code.startswith("/*", position):
            end = code.find("*/", position + 2)

            if end == -1:
                # si no cierra, consume hasta el final
                comment_text = code[position:]
                position = len(code)
                line, column = advance_position(comment_text, line, column)
            else:
                comment_text = code[position:end + 2]
                position = end + 2
                line, column = advance_position(comment_text, line, column)

            continue

        # 1) Primero intentar operadores compuestos aunque estén separados
        compound = match_compound_operator(code, position)
        if compound:
            token_type, consumed_text, final_lexeme = compound
            tokens.append((token_type, final_lexeme, line, column))

            position += len(consumed_text)
            line, column = advance_position(consumed_text, line, column)
            continue

        # 2) Si no, aplicar regex normal
        match = None

        for token_type, regex in TOKEN_REGEX:

            match = regex.match(code, position)

            if match:

                lexeme = match.group(0)

                # ERRORES
                if token_type in ["UNKNOWN", "INVALID_REAL"]:
                    errors.append((lexeme, line, column))
                elif token_type not in ["COMMENT_LINE", "COMMENT_MULTI"]:
                    tokens.append((token_type, lexeme, line, column))

                position = match.end()
                line, column = advance_position(lexeme, line, column)

                break

        if not match:
            errors.append((code[position], line, column))
            position += 1
            column += 1

    return tokens, errors


# EJECUCION DESDE TERMINAL
if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:
        print("Uso: python lexer.py archivo.txt")
        exit()

    file = sys.argv[1]

    with open(file, "r", encoding="utf-8") as f:
        code = f.read()

    tokens, errors = tokenize(code)

    # MOSTRAR TOKENS
    print("\nTOKENS\n")
    for t in tokens:
        print(t)

    # MOSTRAR ERRORES
    print("\nERRORES\n")
    for e in errors:
        print(f"Error: {e}")

    # GUARDAR TOKENS EN ARCHIVO
    with open("tokens.txt", "w", encoding="utf-8") as f:
        for t in tokens:
            f.write(f"{t[0]}\t{t[1]}\t{t[2]}\t{t[3]}\n")

    # GUARDAR ERRORES
    with open("errors.txt", "w", encoding="utf-8") as f:
        for e in errors:
            f.write(f"{e[0]}\tline:{e[1]}\tcolumn:{e[2]}\n")

    # ESTADISTICAS
    print("\nESTADISTICAS\n")
    print("Total tokens:", len(tokens))
    print("Total errores:", len(errors))

    print("\nANALISIS LEXICO COMPLETADO\n")