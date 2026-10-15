# compiler/semantic_report.py — Reportes de texto de la Fase 3
"""
Genera en texto plano (UTF-8) el árbol (original o anotado), la tabla de
símbolos y el reporte de errores semánticos, y los exporta a archivo:

  arbol_anotado.txt · tabla_simbolos.txt · errores_semanticos.txt
"""
from __future__ import annotations
import os
import sys
from collections import Counter
from datetime import datetime

from compiler import semantic_errors as E

ANNOTATED_FILE = "arbol_anotado.txt"
SYMBOLS_FILE   = "tabla_simbolos.txt"
ERRORS_FILE    = "errores_semanticos.txt"

_BAR = "=" * 72


def _header(title: str, source: str | None) -> list[str]:
    lines = [_BAR, f"  {title}"]
    if source:
        lines.append(f"  Archivo fuente: {source}")
    lines.append(f"  Generado: {datetime.now():%Y-%m-%d %H:%M:%S}")
    lines += [_BAR, ""]
    return lines


def _fmt_const(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return repr(v)


# ── Árboles ───────────────────────────────────────────────────────
def _tree_lines(node, prefix: str, is_last: bool, annotated: bool, out: list):
    branch = "└── " if is_last else "├── "
    label = node.node_type
    if node.value is not None:
        label += f' "{node.value}"'
    if annotated:
        if getattr(node, "inferred_type", None):
            label += f"  [tipo: {node.inferred_type}]"
        if getattr(node, "declared_type", None) and node.node_type in ("DECL_VAR", "ID"):
            label += f" [dtype: {node.declared_type}]"
        if getattr(node, "const_value", None) is not None:
            label += f"  [valor: {_fmt_const(node.const_value)}]"
        if getattr(node, "conversion", None):
            label += f"  [conv: {node.conversion}]"
    if node.line is not None:
        label += f"  @{node.line}:{node.column}"
    if annotated and getattr(node, "sem_errors", None):
        label += "  <-- ERROR"
    out.append(prefix + branch + label)
    kids = [c for c in node.children if c is not None]
    child_prefix = prefix + ("    " if is_last else "│   ")
    for i, ch in enumerate(kids):
        _tree_lines(ch, child_prefix, i == len(kids) - 1, annotated, out)


def format_tree(root, annotated: bool) -> str:
    out: list[str] = []
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 20000))      # árboles muy profundos
    try:
        _tree_lines(root, "", True, annotated, out)
    finally:
        sys.setrecursionlimit(old)
    return "\n".join(out)


def format_original_tree(root, source: str | None = None) -> str:
    return "\n".join(_header("ÁRBOL SINTÁCTICO ABSTRACTO (AST ORIGINAL)", source)) \
        + format_tree(root, annotated=False) + "\n"


def format_annotated_tree(root, source: str | None = None) -> str:
    legend = [
        "Leyenda: [tipo] sintetizado · [dtype] heredado de la declaración ·",
        "         [valor] constante calculada en compilación · [conv] conversión implícita",
        "         <-- ERROR: el nodo tiene errores semánticos (ver errores_semanticos.txt)",
        "",
    ]
    return "\n".join(_header("ÁRBOL ANOTADO (ANÁLISIS SEMÁNTICO)", source) + legend) \
        + format_tree(root, annotated=True) + "\n"


# ── Tabla de símbolos ─────────────────────────────────────────────
SYMBOL_COLUMNS = ("Lexema", "Tipo", "Ámbito", "Líneas", "Dirección")


def symbol_rows(entries) -> list:
    """Una fila por identificador (por ámbito): lexema, tipo, ámbito, líneas, dirección."""
    return [(e.name, e.dtype, e.scope, e.lines_display(), f"0x{e.address:04X}")
            for e in entries]


def format_symbol_table(entries, source: str | None = None) -> str:
    rows = symbol_rows(entries)
    cols = SYMBOL_COLUMNS
    widths = [max([len(cols[i])] + [len(r[i]) for r in rows]) for i in range(len(cols))]

    def line(cells):
        return "  ".join(c.ljust(w) for c, w in zip(cells, widths)).rstrip()

    title = "TABLA DE SÍMBOLOS"
    if source:
        title += f"  ·  {source}"
    title += f"  ·  {datetime.now():%Y-%m-%d %H:%M:%S}"
    out = [title, "-" * max(len(title), sum(widths) + 2 * (len(widths) - 1)), line(cols),
           "  ".join("-" * w for w in widths)]
    if rows:
        out += [line(r) for r in rows]
    else:
        out.append("(no se declararon variables)")
    out += ["",
            f"{len(rows)} símbolo(s). Líneas: 'n (xk)' = k apariciones en la línea n "
            f"(declaración y usos).",
            "Dirección = desplazamiento en bytes por orden de declaración "
            "(int=2, float=4, bool=1)."]
    return "\n".join(out) + "\n"


# ── Errores ───────────────────────────────────────────────────────
def format_error_report(errors, source: str | None = None) -> str:
    out = _header("REPORTE DE ERRORES SEMÁNTICOS", source)
    if not errors:
        out.append("Sin errores semánticos.")
        return "\n".join(out) + "\n"
    out.append(f"Total: {len(errors)} error(es) semántico(s)")
    counts = Counter(e.category for e in errors)
    for cat in E.ALL_CATEGORIES:
        if counts.get(cat):
            out.append(f"  - {cat}: {counts[cat]}")
    out.append("")
    for i, e in enumerate(errors, 1):
        loc = e.location()
        out.append(f"{i:02d}. [{e.category}]" + (f" ({loc})" if loc else ""))
        out.append(f"    {e.message}")
    return "\n".join(out) + "\n"


# ── Exportación ───────────────────────────────────────────────────
def export_reports(directory: str, analyzer, source: str | None = None) -> list[str]:
    """Escribe los tres archivos de evidencia en `directory`. Retorna las rutas."""
    os.makedirs(directory, exist_ok=True)
    files = {
        ANNOTATED_FILE: format_annotated_tree(analyzer.annotated_root, source),
        SYMBOLS_FILE:   format_symbol_table(analyzer.symbol_table.all_entries(), source),
        ERRORS_FILE:    format_error_report(analyzer.errors, source),
    }
    paths = []
    for name, text in files.items():
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        paths.append(path)
    return paths
