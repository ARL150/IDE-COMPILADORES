"""
Prueba de la ventana real (MainWindow, Qt offscreen): con errores léxicos, sintácticos
o semánticos NO se genera ni se ejecuta código y no se muestra nada del programa anterior.

    python tests/test_ui_errores.py

Secuencia: programa válido → programa con error → válido otra vez, para cada tipo de error.
Por caso se exige: el simulador no corre; las pestañas Cód. Intermedio / Cód. TM /
Ejecución TM muestran "No se generó código: corrija los errores" (sin instrucciones ni
datos del programa anterior); el pipeline 4-5-6 queda en error; no se escribe .ci/.tm.
"""
import os
import shutil
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox

app = QApplication.instance() or QApplication([])

import ui.main_window as mw

CODE_TABS = {9: "Cód. Intermedio", 10: "Cód. TM", 11: "Ejecución TM"}
MENSAJE = "No se generó código: corrija los errores"
VALIDO = "main{ int marcaUnica; cin marcaUnica; cout marcaUnica; }"
CON_ERROR = {
    "léxico":                "main{ int a; a = 5 @; cout a; }",
    "léxico+sintáctico":     "main{ int a; a = 5 $ 3; cout a; }",
    "sintáctico":            "main{ int a; a = 3 cout a; }",
    "semántico (no decl.)":  "main{ int a; b = 5; cout a; }",
    "semántico (tipos)":     "main{ int a; bool f; a = f; cout a; }",
}

sim_runs = []                                     # una entrada por cada ejecución del simulador
_Sim = mw.TMSimulator
class _CountingSim(_Sim):
    def run(self, *a, **k):
        sim_runs.append(1)
        return super().run(*a, **k)
mw.TMSimulator = _CountingSim
QInputDialog.getText = staticmethod(lambda *a, **k: ("7", True))
QMessageBox.warning = QMessageBox.information = QMessageBox.critical = staticmethod(
    lambda *a, **k: QMessageBox.StandardButton.Ok)


def pipeline(win, step):
    css = getattr(win, step).styleSheet()
    return "err" if "#f28b82" in css else "ok" if "#81c784" in css else "idle"


def code_text(win):
    return {i: win._result_tabs.widget(i).toPlainText() for i in CODE_TABS}


def check(win, path, source, error_kind):
    """Devuelve la lista de problemas al compilar `source` (guardado en `path`)."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(source)
    win._open_single_file(path)
    sim_runs.clear()
    win.run_all()
    texts = code_text(win)
    problems = []
    if error_kind is None:                         # programa válido: sí hay código y ejecución
        if not sim_runs:
            problems.append("el programa válido no se ejecutó")
        for step in ("_pp_ci", "_pp_tm", "_pp_run"):
            if pipeline(win, step) != "ok":
                problems.append(f"{step} debería estar en ok tras un programa válido")
        if MENSAJE in texts[10] or "HALT" not in texts[10]:
            problems.append("el .tm válido no se muestra")
        return problems
    if sim_runs:
        problems.append("el simulador se ejecutó con errores")
    for i, name in CODE_TABS.items():
        if MENSAJE not in texts[i]:
            problems.append(f"'{name}' no muestra el aviso '{MENSAJE}'")
        if "marcaUnica" in texts[i] or "HALT" in texts[i] or "LDC" in texts[i]:
            problems.append(f"'{name}' muestra código/datos de un programa")
        if win._result_tabs.tabText(i) != name:
            problems.append(f"título de pestaña obsoleto: {win._result_tabs.tabText(i)!r}")
    for step in ("_pp_ci", "_pp_tm", "_pp_run"):
        if pipeline(win, step) != "err":
            problems.append(f"{step} debería quedar en error y está en {pipeline(win, step)}")
    base = os.path.splitext(path)[0]
    for ext in (".tm", ".ci"):
        if os.path.exists(base + ext):
            problems.append(f"se escribió {os.path.basename(base)}{ext} con errores")
    return problems


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="ide_ui_err_")
    cwd = os.getcwd()
    os.chdir(tmp)                                  # tokens.txt / errores_*.txt caen aquí
    failures = 0
    try:
        win = mw.MainWindow()
        win._autosave.stop()
        for k, (kind, src) in enumerate(CON_ERROR.items()):
            for label, code, err in (("válido previo", VALIDO, None), (kind, src, kind)):
                p = os.path.join(tmp, f"caso{k}_{'v' if err is None else 'e'}.txt")
                problems = check(win, p, code, err)
                ok = not problems
                failures += not ok
                print(f"{'PASS' if ok else 'FAIL'}  {kind:<22} -> {label}")
                for m in problems:
                    print("      ", m)
        # recuperación: después de los errores, un programa válido vuelve a compilar y ejecutar
        problems = check(win, os.path.join(tmp, "final.txt"), VALIDO, None)
        failures += bool(problems)
        print(f"{'PASS' if not problems else 'FAIL'}  recuperación tras errores", *problems)
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'OK' if not failures else str(failures) + ' FALLO(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
