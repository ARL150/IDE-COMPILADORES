"""
Verificación headless (sin UI) de la Fase 3 — análisis semántico.

Uso (desde cualquier directorio):
    python tests/run_semantic_checks.py

Pipeline: tokenize -> Parser -> SemanticAnalyzer. Termina con código 0 si todo pasa.

Notas sobre los archivos de prueba
----------------------------------
* tests/testsemantica.txt es la PRUEBA PRINCIPAL y trae 6 ERRORES SINTÁCTICOS
  CONOCIDOS: el `while x > 7 ... end` (sin llaves) anidado dentro del cuerpo del
  `do` es tomado por el parser como terminador del do (parser.py, _while_is_loop,
  que solo reconoce `while (cond) {`). Por eso su AST sale deformado (se pierden
  el do-until, el while anidado y el `while y == 0`). Aun así las sentencias
  quedan en SENTENCIAS y los 6 errores semánticos esperados se detectan.
* tests/testsemantica_sintaxis_ok.txt es una copia SUPLEMENTARIA con solo L30 y
  L34 ajustadas (misma numeración de líneas) para que pase el sintáctico.
* tests/prueba_semantica_extra.txt cubre las reglas de tipos una por una.
"""
import contextlib
import io
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from compiler.lexer import tokenize                                  # noqa: E402
from compiler.parser import Parser                                   # noqa: E402
from compiler.semantic import (                                      # noqa: E402
    SemanticAnalyzer, SymbolTable, write_evidence_files,
)


# ─────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────

class Result:
    def __init__(self, src):
        self.src = src
        self.tokens, self.lex_errors = tokenize(src)
        with contextlib.redirect_stdout(io.StringIO()):      # el parser hace print()
            parser = Parser(self.tokens)
            self.ast = parser.parse()
        self.syn_errors = parser.errors
        self.analyzer = SemanticAnalyzer()
        self.root = self.analyzer.analyze(self.ast)
        self.errors = self.analyzer.errors

    def err_pairs(self):
        return [(e.line, e.category) for e in self.errors]

    def err_lines(self):
        return [e.line for e in self.errors]

    def syn_lines(self):
        return [int(re.search(r"línea (\d+)", e).group(1)) for e in self.syn_errors]

    def nodes(self, node_type=None, line=None):
        out = []

        def walk(n):
            if (node_type is None or n.node_type == node_type) and \
               (line is None or n.line == line):
                out.append(n)
            for c in n.children:
                walk(c)
        walk(self.root)
        return out

    def assign(self, line, name=None):
        found = [n for n in self.nodes("ASIGNACION", line)
                 if name is None or n.value == name]
        assert found, f"no hay ASIGNACION en la línea {line}"
        return found[0]


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return Result(f.read())


def run_src(src):
    return Result(src)


def wrap(body):
    """Programa mínimo para pruebas en línea."""
    return "main {\n" + body + "\n}\n"


TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


# ─────────────────────────────────────────────────────────────────
# Datos esperados
# ─────────────────────────────────────────────────────────────────

# (línea, categoría) de testsemantica.txt
EXPECTED_MAIN = [
    (4,  "UNDECLARED"),       # suma
    (5,  "TYPE_MISMATCH"),    # x(int) = 32.32
    (14, "TYPE_MISMATCH"),    # y(int) = 14.54
    (16, "TYPE_MISMATCH"),    # y(int) = a + 3  (float)
    (33, "UNDECLARED"),       # mas
    (37, "UNDECLARED"),       # mas (cin)
]

# (línea, variable, const_value) de testsemantica.txt
EXPECTED_CONST = [
    (7,  "y", 4),
    (10, "a", 61.0),
    (11, "x", 8),
    (12, "y", -2),
    (13, "z", 64),
    (27, "x", 7),
    (31, "x", 6),
]

# Errores sintácticos conocidos de testsemantica.txt (solo línea)
KNOWN_SYNTAX_LINES_MAIN = [34, 35, 35, 36, 36, 39]

EXPECTED_VALIDA = []
EXPECTED_ERRORES = [
    (9,  "DUPLICATE"),
    (11, "TYPE_MISMATCH"),
    (12, "TYPE_MISMATCH"),
    (13, "UNDECLARED"),
    (14, "UNDECLARED"),
]

# prueba_semantica_extra.txt: exactamente un error en cada una de estas líneas
EXPECTED_EXTRA = {
    8:  "DUPLICATE",          # int x; repetida
    9:  "INVALID_CONDITION",  # if x then, x int
    12: "OPERATOR_MISUSE",    # !x con x int
    13: "OPERATOR_MISUSE",    # true + 1
    14: "UNDECLARED",         # cin >> noexiste
    16: "UNDECLARED",         # y = suma + 1  (solo 1: el tipo error se propaga)
    17: "OPERATOR_MISUSE",    # x = 5 / 0
    19: "OPERATOR_MISUSE",    # x < c  (bool en relacional)
    20: "OPERATOR_MISUSE",    # b == x (bool contra int)
    21: "OPERATOR_MISUSE",    # b && x
    22: "OPERATOR_MISUSE",    # f % 2
    23: "TYPE_MISMATCH",      # w = f   (float -> int)
    24: "TYPE_MISMATCH",      # b = 3
    25: "TYPE_MISMATCH",      # w = b
    26: "OPERATOR_MISUSE",    # b++
    27: "OPERATOR_MISUSE",    # -b
    28: "INVALID_CONDITION",  # while y
    33: "INVALID_CONDITION",  # until f
}


# ─────────────────────────────────────────────────────────────────
# 1. testsemantica.txt (principal)
# ─────────────────────────────────────────────────────────────────

@test
def principal_errores_semanticos():
    r = load("testsemantica.txt")
    assert r.lex_errors == [], r.lex_errors
    assert r.err_pairs() == EXPECTED_MAIN, r.err_pairs()


@test
def principal_trae_errores_sintacticos_conocidos():
    # Documenta (no oculta) que el archivo original no pasa el sintáctico.
    r = load("testsemantica.txt")
    assert r.syn_lines() == KNOWN_SYNTAX_LINES_MAIN, r.syn_lines()


@test
def principal_const_values():
    r = load("testsemantica.txt")
    for line, name, expected in EXPECTED_CONST:
        a = r.assign(line, name)
        rhs = a.children[-1]
        assert rhs.const_value == expected and type(rhs.const_value) is type(expected), \
            f"L{line} {name}: rhs.const_value={rhs.const_value!r}, esperado {expected!r}"
        assert a.const_value == expected, \
            f"L{line} {name}: ASIGNACION.const_value={a.const_value!r}, esperado {expected!r}"


@test
def principal_tabla_de_simbolos():
    r = load("testsemantica.txt")
    ents = {e.name: e for e in r.analyzer.symbol_table.all_entries()}
    assert list(ents) == ["x", "y", "z", "a", "b", "c"], list(ents)
    assert [ents[n].dtype for n in ents] == ["int", "int", "int", "float", "float", "float"]
    assert [ents[n].address for n in ents] == [0, 2, 4, 6, 10, 14]
    assert "suma" not in ents and "mas" not in ents


# ─────────────────────────────────────────────────────────────────
# 2. testsemantica_sintaxis_ok.txt (suplementaria, AST completo)
# ─────────────────────────────────────────────────────────────────

@test
def sintaxis_ok_pasa_sintactico():
    r = load("testsemantica_sintaxis_ok.txt")
    assert r.lex_errors == [] and r.syn_errors == [], (r.lex_errors, r.syn_errors)


@test
def sintaxis_ok_mismos_6_errores_que_el_original():
    orig = load("testsemantica.txt")
    ok = load("testsemantica_sintaxis_ok.txt")
    assert ok.err_pairs() == EXPECTED_MAIN, ok.err_pairs()
    assert [(e.line, e.column, e.category) for e in ok.errors] == \
           [(e.line, e.column, e.category) for e in orig.errors]
    # y, por tanto, no aparecen errores semánticos adicionales con el AST completo
    assert len(ok.errors) == len(orig.errors) == 6


@test
def sintaxis_ok_const_values():
    r = load("testsemantica_sintaxis_ok.txt")
    for line, name, expected in EXPECTED_CONST:
        a = r.assign(line, name)
        assert a.children[-1].const_value == expected, (line, name, a.children[-1].const_value)


@test
def sintaxis_ok_condiciones_bool_en_do_until_y_whiles_anidados():
    r = load("testsemantica_sintaxis_ok.txt")
    hm = r.nodes("HACER_MIENTRAS")
    assert len(hm) == 1
    cond_do = [c for c in hm[0].children if c.node_type == "CONDICION"][0]
    assert cond_do.inferred_type == "bool" and cond_do.children[0].line == 35
    whiles = r.nodes("MIENTRAS")
    assert sorted(w.line for w in whiles) == [30, 36], [w.line for w in whiles]   # anidado + y==0
    for w in whiles:
        cond = [c for c in w.children if c.node_type == "CONDICION"][0]
        assert cond.inferred_type == "bool", (w.line, cond.inferred_type)
    for n in r.nodes("CONDICION"):
        assert n.inferred_type == "bool" and not n.sem_errors, (n.line, n.inferred_type)
    # constantes de condiciones: 2>3 es false; (4>2 && true) es true
    c15 = [n for n in r.nodes("CONDICION") if n.line == 15][0].children[0]
    c18 = [n for n in r.nodes("CONDICION") if n.line == 18][0].children[0]
    assert c15.const_value is False and c18.const_value is True


@test
def sintaxis_ok_tabla_de_simbolos_con_lineas():
    r = load("testsemantica_sintaxis_ok.txt")
    ents = {e.name: e for e in r.analyzer.symbol_table.all_entries()}
    assert ents["z"].lines == [2, 8, 13], ents["z"].lines
    assert ents["c"].lines == [3, 26], ents["c"].lines
    assert ents["b"].lines == [3, 19, 21], ents["b"].lines
    for e in ents.values():
        assert e.lines == sorted(set(e.lines)) and e.line in e.lines


# ─────────────────────────────────────────────────────────────────
# 3. Pruebas de la entrega anterior
# ─────────────────────────────────────────────────────────────────

@test
def valida_0_errores():
    r = load("prueba_semantica_valida.txt")
    assert r.syn_errors == [] and r.err_pairs() == EXPECTED_VALIDA, r.err_pairs()


@test
def errores_5_errores():
    r = load("prueba_semantica_errores.txt")
    assert r.syn_errors == []
    assert r.err_pairs() == EXPECTED_ERRORES, r.err_pairs()
    assert len(r.errors) == 5


# ─────────────────────────────────────────────────────────────────
# 4. prueba_semantica_extra.txt (suplementaria de reglas)
# ─────────────────────────────────────────────────────────────────

@test
def extra_un_error_por_linea_esperada():
    r = load("prueba_semantica_extra.txt")
    assert r.lex_errors == [] and r.syn_errors == [], (r.lex_errors, r.syn_errors)
    got = {}
    for e in r.errors:
        got.setdefault(e.line, []).append(e.category)
    assert {k: v for k, v in got.items()} == {k: [v] for k, v in EXPECTED_EXTRA.items()}, got
    assert len(r.errors) == len(EXPECTED_EXTRA)


@test
def extra_expresion_vacia_no_da_error():
    r = load("prueba_semantica_extra.txt")
    assert 15 not in r.err_lines()
    a = r.assign(15, "x")
    assert len(a.children) == 1 and not a.sem_errors


@test
def extra_tipo_error_no_genera_cascada():
    r = load("prueba_semantica_extra.txt")
    assert r.err_lines().count(16) == 1                      # y = suma + 1
    assert r.err_lines().count(22) == 1                      # w = f % 2
    assert r.assign(16, "y").children[-1].inferred_type == "error"
    assert r.assign(22, "w").children[-1].inferred_type == "error"


@test
def extra_division_entre_cero():
    r = load("prueba_semantica_extra.txt")
    e = [e for e in r.errors if e.line == 17][0]
    assert e.category == "OPERATOR_MISUSE" and "división entre cero" in e.message
    assert r.assign(17, "x").children[-1].const_value is None


@test
def extra_conversiones_y_division_entera():
    r = load("prueba_semantica_extra.txt")
    a35 = r.assign(35, "f")                                  # f = w  (int -> float)
    assert a35.conversion == "int_to_float" and a35.children[-1].conversion == "int_to_float"
    a36 = r.assign(36, "f")                                  # f = f + w * 2
    plus = a36.children[-1]
    assert plus.inferred_type == "float"
    assert plus.children[1].inferred_type == "int"           # w * 2
    assert plus.children[1].conversion == "int_to_float"
    a37 = r.assign(37, "f")                                  # f = 7 / 2  -> 3 -> 3.0
    assert a37.children[-1].const_value == 3 and a37.const_value == 3.0
    assert r.assign(38, "w").const_value == -3               # -7 / 2 trunca hacia cero
    assert r.assign(39, "w").const_value == 1                # 7 % 3
    assert r.assign(40, "w").const_value == 8                # 2 ^ 3
    a41 = r.assign(41, "f")                                  # 2 ^ 0.5
    assert a41.children[-1].inferred_type == "float"
    assert abs(a41.const_value - 2 ** 0.5) < 1e-12
    assert a41.children[-1].children[0].conversion == "int_to_float"


@test
def extra_nodos_sinteticos_sin_errores_ni_conversion():
    r = load("prueba_semantica_extra.txt")
    syn = [n for n in r.nodes() if n.synthetic]
    assert len(syn) >= 4, len(syn)           # b++, w=-b, f++, w--, -7
    for n in syn:
        assert not n.sem_errors and n.conversion is None, (n.line, n.value)
    # f++ (float) no marca conversión en el '1' sintético
    plusplus = [n for n in r.nodes("ASIGNACION") if n.line == 45][0]
    assert plusplus.children[-1].children[1].synthetic
    assert plusplus.children[-1].children[1].conversion is None
    # cada línea con ++/-- o menos unario defectuoso produce 1 solo error
    assert r.err_lines().count(26) == 1 and r.err_lines().count(27) == 1


@test
def extra_cout_acepta_cadena_y_expresiones():
    r = load("prueba_semantica_extra.txt")
    sal = r.nodes("SALIDA")[-1]
    assert [c.node_type for c in sal.children] == ["CADENA", "ID", "ID", "ID"]
    assert sal.children[0].inferred_type == "string"
    assert not sal.sem_errors and all(not c.sem_errors for c in sal.children)


# ─────────────────────────────────────────────────────────────────
# 5. Reglas puntuales con programas en línea
# ─────────────────────────────────────────────────────────────────

@test
def undeclared_asignacion_y_uso_dan_un_error_cada_uno():
    r = run_src(wrap("int a;\n suma = 45;\n a = suma + 1;"))
    assert r.err_pairs() == [(3, "UNDECLARED"), (4, "UNDECLARED")], r.err_pairs()
    r = run_src(wrap("suma++;"))          # lhs y operando son el mismo token: 1 solo error
    assert r.err_pairs() == [(2, "UNDECLARED")], r.err_pairs()


@test
def real_equivale_a_float():
    r = run_src(wrap("real r;\n float f;\n r = 1;\n f = r;"))
    assert r.err_pairs() == []
    ents = {e.name: e.dtype for e in r.analyzer.symbol_table.all_entries()}
    assert ents == {"r": "float", "f": "float"}, ents
    assert "real" not in {n.inferred_type for n in r.nodes() if n.inferred_type}
    assert {n.declared_type for n in r.nodes("ID") if n.declared_type} == {"float"}


@test
def declaraciones_en_sentencias_comparten_ambito():
    r = run_src(wrap("int a;\n a = 1;\n int b;\n b = a + 1;\n if true then\n  int c;\n  c = b;\n end"))
    assert r.err_pairs() == [], r.err_pairs()
    names = [e.name for e in r.analyzer.symbol_table.all_entries()]
    assert names == ["a", "b", "c"], names


@test
def tipo_heredado_solo_en_ids_declarados():
    r = run_src(wrap("int a, b;\n float c;\n a = b;"))
    decl_ids = [n for d in r.nodes("DECL_VAR") for n in d.children if n.node_type == "ID"]
    assert [(n.value, n.declared_type) for n in decl_ids] == [("a", "int"), ("b", "int"), ("c", "float")]
    uso = [n for n in r.nodes("ASIGNACION")][0]
    assert all(c.declared_type is None for c in uso.children)       # los usos no heredan dtype
    assert all(c.inferred_type == "int" for c in uso.children)       # sintetizan type


@test
def const_value_solo_si_es_constante():
    r = run_src(wrap("int a, b;\n a = 2 + 3;\n b = a + 1;"))
    assert r.assign(3, "a").children[-1].const_value == 5
    assert r.assign(4, "b").children[-1].const_value is None
    assert r.assign(4, "b").const_value is None


@test
def division_y_modulo_estilo_c():
    r = run_src(wrap("int a;\n a = -7 / 2;\n a = 7 / -2;\n a = -7 % 3;\n a = 7 % -3;\n a = 9 / 2;"))
    assert r.err_pairs() == []
    assert [r.assign(l, "a").const_value for l in (3, 4, 5, 6, 7)] == [-3, -3, -1, 1, 4]


@test
def division_entre_cero_variantes():
    r = run_src(wrap("int a;\n float f;\n a = 1 / 0;\n f = 1.5 / 0.0;\n a = 1 % 0;\n a = 4 / (2 - 2);\n f = 1.0 / a;"))
    assert r.err_pairs() == [(4, "OPERATOR_MISUSE"), (5, "OPERATOR_MISUSE"),
                             (6, "OPERATOR_MISUSE"), (7, "OPERATOR_MISUSE")], r.err_pairs()
    assert all("división entre cero" in e.message for e in r.errors)


@test
def relacionales_y_logicos():
    ok = run_src(wrap("int a;\n float f;\n bool b, c;\n b = a < f;\n b = a == f;\n b = b == c;\n b = b != true;\n"
                      " c = b && c || !b;\n b = (a > 1) && (f <= 2.5);"))
    assert ok.err_pairs() == [], ok.err_pairs()
    assert ok.assign(5, "b").children[-1].children[0].conversion == "int_to_float"
    bad = run_src(wrap("int a;\n bool b;\n b = a && b;\n b = a || a;\n b = !a;\n b = b < b;\n b = b >= true;\n b = a == b;"))
    assert [l for l, _ in bad.err_pairs()] == [4, 5, 6, 7, 8, 9], bad.err_pairs()
    assert all(c == "OPERATOR_MISUSE" for _, c in bad.err_pairs())


@test
def aritmetica_tipos_resultado():
    r = run_src(wrap("int a;\n float f;\n a = 2 ^ 3;\n f = 2 ^ 0.5;\n f = a / 2.0;\n a = a * 2;\n f = a + 1.5;\n"
                     " a = 2 ^ 0.5;\n a = f % 2;\n a = true * 2;"))
    assert [(l, c) for l, c in r.err_pairs()] == [(9, "TYPE_MISMATCH"), (10, "OPERATOR_MISUSE"),
                                                  (11, "OPERATOR_MISUSE")], r.err_pairs()
    assert r.assign(4, "a").children[-1].inferred_type == "int"      # 2 ^ 3
    assert r.assign(5, "f").children[-1].inferred_type == "float"    # 2 ^ 0.5
    assert r.assign(6, "f").children[-1].inferred_type == "float"    # a / 2.0
    assert r.assign(7, "a").children[-1].inferred_type == "int"      # a * 2


@test
def condiciones_solo_bool():
    r = run_src(wrap("int a;\n float f;\n bool b;\n if a then\n  a = 1;\n end\n while f\n  a = 1;\n end\n"
                     " do\n  a = 1;\n until a\n if b then\n  a = 1;\n end\n while a < 3\n  a = a + 1;\n end"))
    assert r.err_pairs() == [(5, "INVALID_CONDITION"), (8, "INVALID_CONDITION"),
                             (13, "INVALID_CONDITION")], r.err_pairs()


@test
def cin_y_cout():
    r = run_src(wrap("int a;\n cin >> a;\n cin >> zz;\n cout << \"x\" << a << a + 1;\n cout << qq;"))
    assert r.err_pairs() == [(4, "UNDECLARED"), (6, "UNDECLARED")], r.err_pairs()


@test
def robustez_ante_hijos_faltantes():
    progs = [
        "int a;\n a = ;",
        "int a;\n a = 1 + ;",
        "int a;\n a = * 3;",
        "int a;\n if then\n a = 1;\n end",
        "int a;\n while\n a = 1;\n end",
        "int a;\n do\n a = 1;\n until",
        "int a; bool b;\n b = ! ;",
        "int a;\n a = (1 + );",
        "int a;\n cin >> ;",
        "int a;\n cout << ;",
        "int a;\n a = 1 ^ ;",
        "int a;\n a = 1 < ;",
        "int a;\n a = 1 && ;",
        "int ;\n a = 1;",
        "x = 1 +;\n y++",
    ]
    for p in progs:
        r = run_src(wrap(p))                      # no debe lanzar excepción
        assert isinstance(r.err_pairs(), list)


@test
def robustez_fuzz_borrando_y_duplicando_tokens():
    for fname in ("testsemantica_sintaxis_ok.txt", "prueba_semantica_extra.txt", "prueba_maestra.txt"):
        with open(os.path.join(HERE, fname), encoding="utf-8") as f:
            toks, _ = tokenize(f.read())
        parser_crashes = 0
        for i in range(len(toks)):
            for variant in (toks[:i] + toks[i + 1:], toks[:i + 1] + toks[i:]):
                with contextlib.redirect_stdout(io.StringIO()):
                    try:
                        ast = Parser(variant).parse()
                    except Exception:             # fallo del PARSER (fuera de alcance), no del semántico
                        parser_crashes += 1
                        continue
                SemanticAnalyzer().analyze(ast)   # esto jamás debe lanzar
        print(f"      fuzz {fname}: {len(toks)} tokens, fallos del parser (no del semántico): {parser_crashes}")


@test
def simbolos_lines_delete_y_scope():
    t = SymbolTable()
    assert t.insert("x", "int", 3, 5) is None
    assert t.insert("f", "float", 3, 8) is None
    assert t.insert("b", "bool", 4, 5) is None
    assert [e.address for e in t.all_entries()] == [0, 2, 6]       # int/bool: 2 bytes, float: 4
    t.lookup("x", 9); t.lookup("x", 7); t.lookup("x", 9); t.lookup("x")
    assert t.lookup("x").lines == [3, 7, 9]
    assert "ya" not in (t.insert("x", "int", 5, 1) or "ya")
    assert t.lookup("x").lines == [3, 5, 7, 9]                      # la redeclaración también aparece
    assert t.delete("f") is True and t.delete("f") is False
    assert t.lookup("f") is None and [e.name for e in t.all_entries()] == ["x", "b"]
    assert "UN SOLO ámbito" in (SymbolTable.__doc__ or "")
    assert "4 bytes" in (SymbolTable.__doc__ or "")


@test
def traza_tiene_todos_los_eventos():
    r = load("prueba_semantica_extra.txt")
    kinds = {e.kind for e in r.analyzer.trace}
    assert {"INSERT", "LOOKUP", "TYPE", "CONV", "ASSIGN_CHECK", "ERROR"} <= kinds, kinds
    assert sum(1 for e in r.analyzer.trace if e.kind == "ERROR") == len(r.errors)
    texts = [str(e) for e in r.analyzer.trace]
    assert any("NO ENCONTRADO" in t for t in texts)
    assert any(t.endswith("→ OK") for t in texts) and any(t.endswith("→ ERROR") for t in texts)
    assert any("INSERT" in t and "dir=0x0000" in t for t in texts)
    # el analizador se puede reutilizar: la traza se reinicia
    n = len(r.analyzer.trace)
    r.analyzer.analyze(r.ast)
    assert len(r.analyzer.trace) == n


@test
def archivos_de_evidencia():
    r = load("testsemantica_sintaxis_ok.txt")
    with tempfile.TemporaryDirectory() as d:
        paths = write_evidence_files(r.analyzer, "línea de árbol\n", d)
        assert sorted(os.path.basename(p) for p in paths) == \
            ["arbol_anotado.txt", "errores_semanticos.txt", "tabla_simbolos.txt"]
        with open(os.path.join(d, "errores_semanticos.txt"), encoding="utf-8") as f:
            lines = f.read().splitlines()
        assert len(lines) == 6
        for ln in lines:
            assert re.fullmatch(r"\[línea \d+, col \d+\] [A-Z_]+: .+", ln), ln
        assert lines[0].startswith("[línea 4, col 5] UNDECLARED:")
        with open(os.path.join(d, "tabla_simbolos.txt"), encoding="utf-8") as f:
            tabla = f.read()
        assert "LINEAS" in tabla and "2, 8, 13" in tabla
        with open(os.path.join(d, "arbol_anotado.txt"), encoding="utf-8") as f:
            assert f.read() == "línea de árbol\n"
        # sin errores: una línea que lo indique
        ok = load("prueba_semantica_valida.txt")
        write_evidence_files(ok.analyzer, "x", d)
        with open(os.path.join(d, "errores_semanticos.txt"), encoding="utf-8") as f:
            assert f.read().strip() == "Sin errores semánticos"


# ─────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────

def main():
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as ex:
            failed += 1
            print(f"  FAIL  {fn.__name__}: {ex}")
        except Exception as ex:                    # excepción inesperada = fallo
            failed += 1
            print(f"  ERROR {fn.__name__}: {type(ex).__name__}: {ex}")
    total = len(TESTS)
    print(f"\n{total - failed}/{total} pruebas OK" + ("" if not failed else f" — {failed} FALLARON"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
