# compiler/intermediate.py
import sys

def generate_intermediate(code):
    lines = code.splitlines()
    result = []
    for i, line in enumerate(lines, 1):
        tname = f"t{i}"
        result.append(f"{tname} = {line}")
    return result

if __name__ == "__main__":
    file = sys.argv[1]
    with open(file) as f:
        code = f.read()
    inter = generate_intermediate(code)
    for l in inter:
        print(l)