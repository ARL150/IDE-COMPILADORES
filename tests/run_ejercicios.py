"""
Pruebas end-to-end: fuente → compilador → .tm → simulador TM → salida esperada.

Uso:
    python tests/run_ejercicios.py                 # todos los programas
    python tests/run_ejercicios.py -v              # además muestra el .tm de los que fallan
    python tests/run_ejercicios.py g04_e1 ulam     # sólo los archivos cuyo nombre contenga eso

Carpetas:
    tests/ejercicios_pdf/   un .txt por ejercicio de EjerciciosFinalesCompisII.pdf
                            (los ejercicios repetidos entre grupos se prueban una sola vez)
    tests/codegen_extra/    programas propios para operadores y casos límite del generador

Cada .txt declara en su cabecera (comentarios //) los casos de prueba:

    // CASO: <entradas> => <línea 1>|<línea 2>|...
    // CASO: <entradas> => ERROR: <texto que debe aparecer en el error de ejecución>
    // CASO: <entradas> =>                       (programa sin salida)

  · Las entradas se separan con espacios; los reales llevan punto (1.5).
  · [a b]*n repite el bloque "a b" n veces  (p. ej. [3 5]*52).
  · Cada OUT/cout produce una línea; se comparan las líneas de salida del
    programa (se ignoran los ecos "[Entrada] → ...").

Para cada programa se exige además: sin errores léxicos/sintácticos/semánticos,
.ci no vacío y un .tm bien formado (direcciones consecutivas, sólo opcodes de la
TM + las extensiones INF/OUTF/OUTC/OUTNL, terminado en HALT).
Segunda pasada (tm.c de Louden): los programas que NO usan extensiones (enteros, sin
cadenas ni reales) se ejecutan además en el simulador de referencia, compilado con
gcc, y su salida ("Resultado del programa (OUT): N") se compara con lo esperado.
  · tm.c se busca en la variable de entorno TM_C, en tests/tm_ref/tm.c y en la ruta
    de la carpeta del curso (TM_C_DEFAULT).
  · Si falta gcc o tm.c la pasada se OMITE con un aviso (no cuenta como fallo).
  · Un programa que no usa extensiones nunca debe emitir MOD/OUTNL/INF/OUTF/OUTC
    ni exceder las 1024 instrucciones de tm.c.
Termina con código 1 si algo falla.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from compiler.pipeline import compile_source, run_tm

DIRS = [os.path.join(ROOT, "tests", "ejercicios_pdf"),
        os.path.join(ROOT, "tests", "codegen_extra")]

LOUDEN_OPS = {"HALT", "IN", "OUT", "ADD", "SUB", "MUL", "DIV",
              "LD", "ST", "LDA", "LDC", "JLT", "JLE", "JGT", "JGE", "JEQ", "JNE"}
EXT_OPS = {"MOD", "INF", "OUTF", "OUTC", "OUTNL"}      # sólo en el simulador del IDE
TM_OPS = LOUDEN_OPS | EXT_OPS
IADDR_SIZE = 1024                                       # límite de instrucciones de tm.c
TM_C_DEFAULT = (r"C:\Users\exede\OneDrive\Documentos\Escuela\9_NOVENO\1. COMPILADORES II"
                r"\Tiny_Con_Codigo_Intermedio_Menu\Tiny_Intermedio_TM\tm.c")
TM_LINE = re.compile(r"^\s*(\d+):\s+([A-Z]+)\s+(\d+),(-?\d+)(?:,(\d+)|\((\d+)\))")


def expand(inputs: str) -> list:
    """'[3 5]*2 0' → ['3','5','3','5','0']"""
    inputs = re.sub(r"\[([^\]]*)\]\*(\d+)",
                    lambda m: " ".join([m.group(1)] * int(m.group(2))), inputs)
    return inputs.split()


def read_cases(code: str) -> list:
    cases = []
    for line in code.splitlines():
        m = re.match(r"//\s*CASO:\s*(.*?)\s*=>(.*)$", line)
        if m:
            rhs = m.group(2).strip()
            if rhs.startswith("ERROR:"):
                expected = ("error", rhs[len("ERROR:"):].strip())
            else:
                expected = ("out", rhs.split("|") if rhs else [])
                expected = ("out", [e.strip() for e in expected[1]])
            cases.append((m.group(1), expand(m.group(1)), expected))
    return cases


def check_tm(tm_lines: list) -> list:
    """Problemas de formato del .tm (lista vacía = correcto)."""
    problems = []
    if not tm_lines:
        return ["el .tm está vacío"]
    for i, line in enumerate(tm_lines):
        m = TM_LINE.match(line)
        if not m:
            problems.append(f"línea {i} no es una instrucción TM: {line!r}")
            continue
        if int(m.group(1)) != i:
            problems.append(f"dirección {m.group(1)} en la posición {i}")
        if m.group(2) not in TM_OPS:
            problems.append(f"opcode desconocido {m.group(2)}")
    if tm_lines and " HALT " not in tm_lines[-1] + " ":
        problems.append("el .tm no termina en HALT")
    return problems


class LoudenTM:
    """tm.c de Louden compilado con gcc (o `available == False` con el motivo)."""

    def __init__(self):
        self.exe = None
        self.reason = ""
        self.ran = 0
        self.skipped = 0
        gcc = shutil.which("gcc")
        candidates = [os.environ.get("TM_C", ""),
                      os.path.join(ROOT, "tests", "tm_ref", "tm.c"), TM_C_DEFAULT]
        tm_c = next((c for c in candidates if c and os.path.isfile(c)), None)
        if not gcc:
            self.reason = "no se encontró gcc en el PATH"
        elif not tm_c:
            self.reason = "no se encontró tm.c (defina TM_C o use tests/tm_ref/tm.c)"
        else:
            self.workdir = tempfile.mkdtemp(prefix="ide_tm_louden_")
            exe = os.path.join(self.workdir, "tm.exe" if os.name == "nt" else "tm")
            proc = subprocess.run([gcc, "-std=c11", tm_c, "-o", exe],
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                self.reason = "gcc no pudo compilar tm.c: " + proc.stderr.strip()[:200]
            else:
                self.exe = exe

    @property
    def available(self) -> bool:
        return self.exe is not None

    def run(self, tm_text: str, inputs: list) -> tuple:
        """(líneas OUT, texto completo de stdout)"""
        path = os.path.join(self.workdir, "programa.tm")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(tm_text + "\n")
        stdin = "g\n" + "".join(f"{v}\n" for v in inputs) + "q\n"
        proc = subprocess.run([self.exe, path], input=stdin, capture_output=True,
                              text=True, timeout=60)
        outs = re.findall(r"Resultado del programa \(OUT\): (-?\d+)", proc.stdout)
        return outs, proc.stdout


def run_louden(loud: LoudenTM, comp, cases: list) -> list:
    """Segunda pasada: ejecuta el .tm en tm.c. Devuelve mensajes de fallo."""
    msgs = []
    for raw, inputs, (kind, want) in cases:
        outs, text = loud.run(comp.tm_text, inputs)
        bad = [l for l in text.splitlines()
               if re.search(r"Illegal opcode|Bad |Missing |Location too large", l)]
        if bad:
            msgs.append(f"tm.c [{raw}]: no cargó el programa: {bad[0]}")
        elif kind == "error":
            if "division" not in text:
                msgs.append(f"tm.c [{raw}]: se esperaba división entre cero; salida {outs}")
        elif outs != want:
            msgs.append(f"tm.c [{raw}]:\n      esperado {want}\n      obtenido {outs}")
    return msgs


def run_file(path: str, verbose: bool, loud: "LoudenTM | None" = None) -> tuple:
    """(ok, [mensajes])"""
    with open(path, encoding="utf-8") as f:
        code = f.read()
    cases = read_cases(code)
    msgs = []
    if not cases:
        return False, ["sin líneas // CASO:"]

    comp = compile_source(code)
    if not comp.ok:
        return False, ["errores de compilación: " + "; ".join(comp.errors()[:3])]
    if not comp.ci_lines:
        msgs.append("el .ci salió vacío")
    msgs += check_tm(comp.tm_lines)
    standard = not comp.extensions_used
    if standard:
        used = {TM_LINE.match(l).group(2) for l in comp.tm_lines if TM_LINE.match(l)}
        if used & EXT_OPS:
            msgs.append(f"modo estándar con instrucciones no estándar: {sorted(used & EXT_OPS)}")
        if len(comp.tm_lines) > IADDR_SIZE:
            msgs.append(f"{len(comp.tm_lines)} instrucciones: excede las {IADDR_SIZE} de tm.c")

    for raw, inputs, (kind, want) in cases:
        res = run_tm(comp.tm_text, inputs)
        got = [ln for ln in res.output if not ln.startswith("[Entrada]")]
        if kind == "error":
            if not res.error or want not in res.error:
                msgs.append(f"entradas [{raw}]: se esperaba error '{want}', "
                            f"se obtuvo error={res.error!r} salida={got}")
        else:
            if res.error:
                msgs.append(f"entradas [{raw}]: error de ejecución: {res.error}")
            elif not res.halted:
                msgs.append(f"entradas [{raw}]: el programa no llegó a HALT")
            elif got != want:
                msgs.append(f"entradas [{raw}]:\n      esperado {want}\n      obtenido {got}")
    if standard:
        # el modo extendido (MOD/OUTNL) debe dar exactamente los mismos resultados
        ext = compile_source(code, standard=False)
        for raw, inputs, _ in cases:
            a, b = run_tm(comp.tm_text, inputs), run_tm(ext.tm_text, inputs)
            if (a.output, a.error) != (b.output, b.error):
                msgs.append(f"entradas [{raw}]: modo estándar y extendido difieren: "
                            f"{a.output} vs {b.output}")
    if loud is not None and loud.available:
        if standard:
            loud.ran += 1
            msgs += run_louden(loud, comp, cases)
        else:
            loud.skipped += 1                  # usa extensiones: sólo corre en el IDE
    if msgs and verbose:
        msgs.append("--- .tm ---\n" + comp.tm_text)
    return not msgs, msgs


def main(argv):
    verbose = "-v" in argv
    filters = [a for a in argv if not a.startswith("-")]
    files = []
    for d in DIRS:
        files += sorted(glob.glob(os.path.join(d, "*.txt")))
    if filters:
        files = [f for f in files if any(s in os.path.basename(f) for s in filters)]

    loud = LoudenTM()
    if not loud.available:
        print(f"AVISO: segunda pasada con tm.c de Louden omitida ({loud.reason}).\n")
    passed = failed = 0
    failures = []
    for path in files:
        name = os.path.relpath(path, os.path.join(ROOT, "tests")).replace("\\", "/")
        try:
            ok, msgs = run_file(path, verbose, loud)
        except Exception as ex:           # el compilador nunca debe tronar
            ok, msgs = False, [f"excepción {type(ex).__name__}: {ex}"]
        if ok:
            passed += 1
            print(f"PASS  {name}")
        else:
            failed += 1
            failures.append(name)
            print(f"FAIL  {name}")
            for m in msgs:
                print(f"      {m}")

    print(f"\n{passed} PASS, {failed} FAIL, {passed + failed} programas")
    if loud.available:
        print(f"tm.c de Louden: {loud.ran} programas ejecutados, "
              f"{loud.skipped} omitidos por usar extensiones")
    else:
        print("tm.c de Louden: pasada OMITIDA (ver aviso arriba)")
    if failures:
        print("Fallaron: " + ", ".join(failures))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
