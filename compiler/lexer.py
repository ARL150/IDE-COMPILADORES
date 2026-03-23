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

        match = None

        for token_type, regex in TOKEN_REGEX:

            match = regex.match(code, position)

            if match:

                lexeme = match.group(0)

                # ERRORES
                if token_type in ["UNKNOWN", "INVALID_REAL"]:
                    errors.append((lexeme, line, column))
                else:
                    tokens.append((token_type, lexeme, line, column))

                position = match.end()
                column += len(lexeme)

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

    with open(file, "r") as f:
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
    with open("tokens.txt", "w") as f:
        for t in tokens:
            f.write(f"{t[0]}\t{t[1]}\t{t[2]}\t{t[3]}\n")

    # GUARDAR ERRORES
    with open("errors.txt", "w") as f:
        for e in errors:
            f.write(f"{e[0]}\tline:{e[1]}\tcolumn:{e[2]}\n")

    # ESTADISTICAS
    print("\nESTADISTICAS\n")
    print("Total tokens:", len(tokens))
    print("Total errores:", len(errors))

    print("\nANALISIS LEXICO COMPLETADO\n")