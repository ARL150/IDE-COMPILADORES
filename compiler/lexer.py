# compiler/lexer.py
import re

TOKEN_TYPES = {
    "NUMBER": r"\d+",
    "ID": r"[a-zA-Z_]\w*",
    "PLUS": r"\+",
    "EQUAL": r"=",
    "LPAREN": r"\(",
    "RPAREN": r"\)",
    "PRINT": r"print",
    "UNKNOWN": r"."
}

def tokenize(code):
    tokens = []
    position = 0
    while position < len(code):
        if code[position].isspace():
            position += 1
            continue

        match = None
        for token_type, pattern in TOKEN_TYPES.items():
            regex = re.compile(pattern)
            match = regex.match(code, position)
            if match:
                lexeme = match.group(0)
                if token_type != "UNKNOWN":  # ignorar chars desconocidos
                    tokens.append((token_type, lexeme))
                position = match.end()
                break

        if not match:
            raise SyntaxError(f"Token desconocido: {code[position]}")

    return tokens

if __name__ == "__main__":
    import sys
    file = sys.argv[1]
    with open(file, "r") as f:
        code = f.read()
    tokens = tokenize(code)
    for t in tokens:
        print(t)