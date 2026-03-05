# compiler/parser.py
import sys

def parse(code):
    lines = code.splitlines()
    output = []
    for i, line in enumerate(lines, 1):
        output.append(f"Línea {i}: {line}")
    return output

if __name__ == "__main__":
    file = sys.argv[1]
    with open(file) as f:
        code = f.read()
    tree = parse(code)
    for l in tree:
        print(l)