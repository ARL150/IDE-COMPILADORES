"""
Pruebas de generalidad del analizador semántico (Fase 3).

Uso:   python tests/test_semantica_extra.py [archivo.txt ...]
Sin argumentos corre todos los tests/semantica_extra/*.txt más los casos
incorporados (programa vacío, cadena en operadores, árbol muy profundo).

Cada archivo declara en sus primeras líneas lo esperado:
    // ESPERADO: UNDECLARED=4 TYPE_MISMATCH=1 SIMBOLOS=3     (lo no listado = 0)
    // ESPERADO: LIBRE                                        (solo que no truene)
    // TABLA: y=5, 6 (x3), 7 (x4)                             (líneas del símbolo)
Nunca debe lanzarse una excepción, ni siquiera con AST parcial.
"""
import glob
import io
import os
import re
import sys
import tempfile
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from compiler.ast_nodes import ASTNode
from compiler.lexer import tokenize
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer
from compiler import semantic_report as R
from compiler import semantic_errors as E


def analyze_source(code: str):
    tokens, lex_errors = tokenize(code)
    parser = Parser(tokens)
    old, sys.stdout = sys.stdout, io.StringIO()      # el parser imprime sus errores
    try:
        ast = parser.parse()
    finally:
        sys.stdout = old
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    # los reportes también deben poder generarse siempre
    with tempfile.TemporaryDirectory() as d:
        R.export_reports(d, analyzer, "test")
    R.format_original_tree(ast)
    return analyzer, ast, lex_errors, parser.errors


def parse_header(code: str):
    exp, tabla = None, {}
    for line in code.splitlines()[:6]:
        m = re.match(r"//\s*ESPERADO:\s*(.*)", line)
        if m:
            exp = m.group(1).strip()
        m = re.match(r"//\s*TABLA:\s*(\w+)=(.*)", line)
        if m:
            tabla[m.group(1)] = m.group(2).strip()
    return exp, tabla


def check_file(path: str):
    code = open(path, encoding="utf-8").read()
    analyzer, ast, lex_err, syn_err = analyze_source(code)
    exp, tabla = parse_header(code)
    problems = []
    got = Counter(e.category for e in analyzer.errors)
    n_syms = len(analyzer.symbol_table.all_entries())
    if exp is None:
        problems.append("falta la cabecera // ESPERADO")
    elif exp.upper() != "LIBRE":
        want = {k: int(v) for k, v in re.findall(r"([A-Z_]+)=(\d+)", exp)}
        want_syms = want.pop("SIMBOLOS", None)
        for cat in E.ALL_CATEGORIES:
            if got.get(cat, 0) != want.get(cat, 0):
                problems.append(f"{cat}: esperado {want.get(cat, 0)}, obtenido {got.get(cat, 0)}")
        if want_syms is not None and want_syms != n_syms:
            problems.append(f"SIMBOLOS: esperado {want_syms}, obtenido {n_syms}")
    for name, lines in tabla.items():
        sym = next((s for s in analyzer.symbol_table.all_entries() if s.name == name), None)
        if sym is None or sym.lines_display() != lines:
            problems.append(f"TABLA {name}: esperado '{lines}', "
                            f"obtenido '{sym.lines_display() if sym else None}'")
    extra = f"léx={len(lex_err)} sint={len(syn_err)} sem={len(analyzer.errors)} símbolos={n_syms}"
    return problems, extra


# ── Casos incorporados ────────────────────────────────────────────
def _node(t, v=None, *children, l=1, c=1):
    n = ASTNode(t, v, l, c)
    for x in children:
        n.add_child(x)
    return n


def builtin_cases():
    out = []

    def case(name, fn):
        try:
            problems = fn() or []
        except Exception as ex:                      # noqa: BLE001
            problems = [f"EXCEPCIÓN {type(ex).__name__}: {ex}"]
        out.append((name, problems, ""))

    def vacio():
        a, *_ = analyze_source("")
        if a.symbol_table.all_entries():
            return ["un programa vacío no debe tener símbolos"]

    def solo_espacios():
        analyze_source("   \n\n  ")

    def cadena_en_operadores():
        N = _node
        prog = N("PROGRAMA", None, N("MAIN", "main"),
                 N("DECLARACIONES", None,
                   N("DECL_VAR", None, N("TIPO", "int"), N("ID", "n", l=2, c=5), l=2)),
                 N("SENTENCIAS", None,
                   N("ASIGNACION", "n", N("ID", "n", l=3),
                     N("OP_SUMA", "+", N("CADENA", '"a"'), N("NUMERO", "1"), l=3), l=3),
                   N("SALIDA", None, N("CADENA", '"ok"'), N("ID", "n"), l=4),
                   N("SALIDA", None, N("OP_LOGICO", "&&", N("CADENA", '"a"'),
                                       N("BOOL", "true"), l=5), l=5),
                   N("SALIDA", None, N("OP_REL", "<", N("CADENA", '"a"'),
                                       N("NUMERO", "2"), l=6), l=6)))
        a = SemanticAnalyzer()
        a.analyze(prog)
        cats = [e.category for e in a.errors]
        if cats != [E.OPERATOR_MISUSE] * 3:
            return [f"se esperaban 3 OPERATOR_MISUSE por cadena, se obtuvo {cats}"]

    def original_intacto():
        code = "main { int a; float f; a = 1; f = a + 2.5; }"
        tokens, _ = tokenize(code)
        ast = Parser(tokens).parse()
        before = R.format_tree(ast, annotated=False)
        SemanticAnalyzer().analyze(ast)
        if R.format_tree(ast, annotated=False) != before:
            return ["el AST original fue modificado"]
        if any(hasattr(n, "inferred_type") for n in [ast] + ast.children):
            return ["el AST original recibió atributos semánticos"]

    def cadena_larga():
        n = 3000
        code = "main { int a; a = " + " + ".join(["1"] * n) + "; }"
        a, *_ = analyze_source(code)
        if a.errors:
            return [f"suma de {n} términos dio errores: {a.errors[:1]}"]
        asg = a.annotated_root.children[2].children[0]
        if asg.children[-1].const_value != n:
            return [f"const_value esperado {n}, obtenido {asg.children[-1].const_value}"]

    def constantes_sin_tronar():
        code = ("main { int a; float f; a = 2 ^ -1; a = 2 ^ 5000; f = 0.0 ^ -1.0; "
                "a = 7 / 2; a = 0 - 7 % 3; f = 2.5 ^ 2; }")
        a, *_ = analyze_source(code)
        asg = a.annotated_root.children[2].children
        got = [x.children[-1].const_value for x in asg]
        want = [None, None, None, 3, -1, 6.25]
        if got != want:
            return [f"const_value {got} != {want}"]

    case("programa vacío (sin tokens)", vacio)
    case("solo espacios", solo_espacios)
    case("cadena en operadores (AST a mano)", cadena_en_operadores)
    case("AST original intacto", original_intacto)
    case("expresión de 3000 términos", cadena_larga)
    case("constantes: exponentes/divisiones sin tronar", constantes_sin_tronar)
    return out


def main(argv):
    files = argv or sorted(glob.glob(os.path.join(ROOT, "tests", "semantica_extra", "*.txt")))
    results = []
    for f in files:
        try:
            problems, extra = check_file(f)
        except Exception as ex:                      # noqa: BLE001
            problems, extra = [f"EXCEPCIÓN {type(ex).__name__}: {ex}"], ""
        results.append((os.path.basename(f), problems, extra))
    if not argv:
        results += builtin_cases()
    failed = 0
    for name, problems, extra in results:
        if problems:
            failed += 1
            print(f"FAIL  {name}")
            for p in problems:
                print(f"        - {p}")
        else:
            print(f"ok    {name}   {extra}")
    print(f"\n{len(results) - failed}/{len(results)} casos correctos")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
