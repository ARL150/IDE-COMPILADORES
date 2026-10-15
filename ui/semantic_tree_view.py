# ui/semantic_tree_view.py
# Árbol anotado / AST original colapsables (mismo comportamiento y estilo que
# ASTTableView de syntax_tree.py): clic en el nodo → colapsa/expande,
# ▶ colapsado · ▼ expandido · ◆ hoja, badge "+N" con los hijos ocultos,
# estado inicial todo expandido, "Expandir todo" / "Colapsar todo".
import re
import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget,
    QSplitter, QLabel, QButtonGroup, QTextBrowser, QMenu, QTextEdit,
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from ui.syntax_tree import _COLORS, _DEF_COLOR, _MENU_CSS

_TYPE_COLORS = {"int": "#b5cea8", "float": "#ffcb6b", "bool": "#4fc1ff",
                "string": "#ce9178", "error": "#f28b82"}
_CAT_RE = re.compile(r"^\[([A-Z_]+)\]")


def _esc(t) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt_const(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return repr(v)


def _kids(node) -> list:
    return [c for c in node.children if c is not None]


def preorder(root):
    """Recorrido en preorden SIN recursión (soporta árboles muy profundos)."""
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(reversed(_kids(node)))


class SemanticTreeView(QTextBrowser):
    """
    Árbol colapsable en tabla HTML oscura, una línea por nodo.
    annotated=False → AST original (Nodo · Valor · Ln · Col)
    annotated=True  → además una celda "Anotaciones" con tipo, dtype heredado,
                      valor constante, conversión y error, todo en la misma línea.
    El estado colapsado lo maneja el panel (se comparte entre vistas); la vista
    solo emite `toggled(idx)` y muestra el conjunto que se le asigne.
    """

    toggled = pyqtSignal(int)
    expand_requested = pyqtSignal()
    collapse_requested = pyqtSignal()

    def __init__(self, title: str, annotated: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("SemanticTreeView")
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        font = QFont("Menlo" if sys.platform == "darwin" else "Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self._title = title
        self._annotated = annotated
        self._root = None
        self._ids: dict = {}          # id(nodo) -> índice en preorden
        self._total = 0
        self._collapsed: set = set()
        self.anchorClicked.connect(self._on_anchor)
        self.show_empty()

    # ── API ───────────────────────────────────────────────────────
    def load(self, root):
        self._root = root
        self._ids = {}
        for i, node in enumerate(preorder(root)):
            self._ids[id(node)] = i
        self._total = len(self._ids)
        self._collapsed = set()
        self._render()
        self.verticalScrollBar().setValue(0)

    def collapsible_ids(self) -> set:
        """Índices de los nodos con hijos, salvo la raíz (que queda expandida)."""
        if self._root is None:
            return set()
        return {self._ids[id(n)] for n in preorder(self._root)
                if _kids(n) and n is not self._root}

    def set_collapsed(self, collapsed: set):
        self._collapsed = set(collapsed)
        pos = self.verticalScrollBar().value()
        self._render()
        self.verticalScrollBar().setValue(pos)

    def show_empty(self):
        self._root = None
        self._ids = {}
        self._total = 0
        self.setHtml(
            '<html><body style="background:#0d1014;"><div style="padding:28px 14px;'
            'text-align:center;"><span style="color:#2a2a2a;font-size:10pt;">'
            'Ejecuta el análisis semántico para ver el árbol.</span></div></body></html>')

    # ── Interacción ───────────────────────────────────────────────
    def _on_anchor(self, url: QUrl):
        s = url.toString()
        if s.startswith("n") and s[1:].isdigit():
            self.toggled.emit(int(s[1:]))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_CSS)

        def _a(label, slot, enabled=True):
            a = QAction(label, self)
            a.triggered.connect(slot)
            a.setEnabled(enabled)
            menu.addAction(a)

        _a("Copiar selección", self.copy, self.textCursor().hasSelection())
        _a("Seleccionar todo", self.selectAll)
        menu.addSeparator()
        _a("Expandir todo", self.expand_requested.emit)
        _a("Colapsar todo", self.collapse_requested.emit)
        menu.exec(event.globalPos())

    # ── Render ────────────────────────────────────────────────────
    def _row(self, node, level, prefix, is_last, row_i) -> str:
        idx = self._ids[id(node)]
        kids = _kids(node)
        collapsed = idx in self._collapsed
        nc = _COLORS.get(node.node_type, _DEF_COLOR)
        errs = getattr(node, "sem_errors", None) if self._annotated else None
        if errs:
            nc = "#f28b82"
        bg = "#1a1013" if errs else ("#111418" if row_i % 2 == 0 else "#0d1014")
        bdr = "#1a1e22"

        if kids:
            arrow, arrow_c = ("▶", "#555") if collapsed else ("▼", "#4a6fa5")
            toggle = (f'<a href="n{idx}" style="color:{arrow_c};text-decoration:none;'
                      f'font-size:8pt;">{arrow}</a>&nbsp;')
            name = (f'<a href="n{idx}" style="color:{nc};font-weight:'
                    f'{"bold" if level == 0 else "600"};font-size:9.5pt;'
                    f'text-decoration:none;">{_esc(node.node_type)}</a>')
        else:
            toggle = '<span style="color:#1a1e22;font-size:8pt;">◆</span>&nbsp;'
            name = f'<span style="color:{nc};font-size:9.5pt;">{_esc(node.node_type)}</span>'
        pre = (f'<span style="color:#222;">{_esc(prefix)}{"╚═ " if is_last else "╠═ "}</span>'
               if level > 0 else "")
        badge = (f'&nbsp;<span style="color:#333;font-size:7.5pt;background:#1a1e22;'
                 f'padding:1px 5px;">+{len(kids)}</span>' if collapsed and kids else "")

        nt = node.node_type.upper()
        vc = ("#ce9178" if "CADENA" in nt else
              "#b5cea8" if any(x in nt for x in ("NUMERO", "REAL", "BOOL")) else
              "#4ec9b0" if nt == "ID" else "#9cdcfe")
        val = (f'<span style="color:{vc};font-size:10pt;">{_esc(node.value)}</span>'
               if node.value is not None else "")

        ann = ""
        if self._annotated:
            chips = []
            t = getattr(node, "inferred_type", None)
            if t:
                chips.append(f'<span style="color:{_TYPE_COLORS.get(t, "#9d9d9d")};">'
                             f'[{_esc(t)}]</span>')
            d = getattr(node, "declared_type", None)
            if d and node.node_type in ("DECL_VAR", "ID"):
                chips.append(f'<span style="color:#7a8aa0;font-size:8.5pt;">'
                             f'dtype:{_esc(d)}</span>')
            if getattr(node, "const_value", None) is not None:
                chips.append(f'<span style="color:#7fbf7f;font-size:8.5pt;">'
                             f'= {_esc(_fmt_const(node.const_value))}</span>')
            if getattr(node, "conversion", None):
                chips.append(f'<span style="color:#ffb74d;font-size:8.5pt;">'
                             f'↑{_esc(node.conversion)}</span>')
            if errs:
                m = _CAT_RE.match(errs[0])
                chips.append(f'<span style="color:#f28b82;font-size:8.5pt;">'
                             f'⚠ {_esc(m.group(1) if m else "ERROR")}</span>')
            ann = (f'<td style="padding:3px 14px 3px 4px;border-bottom:1px solid {bdr};'
                   f'white-space:nowrap;">{"&nbsp;&nbsp;".join(chips)}</td>')

        ln = str(node.line) if node.line is not None else "—"
        col = str(node.column) if node.column is not None else "—"
        cell = f'border-bottom:1px solid {bdr};white-space:nowrap;vertical-align:middle;'
        return (
            f'<tr style="background:{bg};">'
            f'<td style="{cell}color:#505050;text-align:right;padding:3px 10px 3px 8px;'
            f'font-size:8pt;">{row_i + 1:03d}</td>'
            f'<td style="{cell}padding:3px 6px;text-align:center;">'
            f'<span style="color:{nc};font-size:8pt;">{"●" if level == 0 else "○"}</span></td>'
            f'<td style="{cell}padding:3px 14px 3px 4px;">{pre}{toggle}{name}{badge}</td>'
            f'<td style="{cell}padding:3px 14px 3px 4px;">{val}</td>'
            f'{ann}'
            f'<td style="{cell}color:#5a6070;text-align:center;padding:3px 8px;'
            f'font-size:9pt;">{ln}</td>'
            f'<td style="{cell}color:#4a5060;text-align:center;padding:3px 8px;'
            f'font-size:9pt;">{col}</td></tr>')

    def _render(self):
        if self._root is None:
            return
        rows = []
        # recorrido iterativo en preorden, saltando los hijos de los colapsados
        stack = [(self._root, 0, "", True)]
        while stack:
            node, level, prefix, is_last = stack.pop()
            rows.append(self._row(node, level, prefix, is_last, len(rows)))
            if self._ids[id(node)] in self._collapsed:
                continue
            kids = _kids(node)
            child_prefix = prefix + ("   " if is_last else "│  ")
            for j in range(len(kids) - 1, -1, -1):
                stack.append((kids[j], level + 1, child_prefix, j == len(kids) - 1))

        th = ("background:#141414;color:#484848;font-size:8pt;font-weight:700;"
              "padding:5px 12px;border-bottom:1px solid #1e1e1e;white-space:nowrap;")
        ann_th = f'<th style="{th}text-align:left;">Anotaciones</th>' if self._annotated else ""
        visible = len(rows)
        info = (f"{visible} de {self._total} nodos visibles" if self._collapsed
                else f"{self._total} nodos")
        html = f"""
<html><body style="background:#0d1014;margin:0;padding:0;
    font-family:'Menlo','SF Mono','Consolas',monospace;">
<div style="padding:8px 12px 4px;border-bottom:1px solid #1a1e22;">
  <span style="color:#c792ea;font-size:11pt;font-weight:700;">◈ {_esc(self._title)}</span>
  &nbsp;&nbsp;<span style="color:#252525;font-size:8.5pt;">{datetime.now():%H:%M:%S}</span>
  &nbsp;&nbsp;<span style="color:#2a3040;font-size:7.5pt;">▶/▼ clic en nodo para colapsar/expandir</span>
</div>
<table cellspacing="0" cellpadding="0" width="100%" style="border-collapse:collapse;margin-top:2px;">
<tr><th style="{th}text-align:right;">#</th><th style="{th}"></th>
<th style="{th}text-align:left;">Nodo</th><th style="{th}text-align:left;">Valor</th>
{ann_th}<th style="{th}text-align:center;">Ln</th><th style="{th}text-align:center;">Col</th></tr>
{"".join(rows)}
</table>
<div style="padding:5px 12px 8px;"><span style="color:#252525;font-size:8pt;">{info}</span></div>
</body></html>"""
        self.setHtml(html)


class SemanticTreePanel(QWidget):
    """
    Pestaña "Árbol Anotado": tres vistas (Anotado · AST original · Lado a lado)
    con el mismo estado de colapso compartido, y botones Expandir/Colapsar todo.
    """

    _MODE_CSS = (
        "QPushButton{background:#161a20;color:#7a7a7a;border:1px solid #232830;"
        "padding:3px 12px;font-size:8.5pt;}"
        "QPushButton:checked{background:#2a1f33;color:#ce93d8;border-color:#ce93d8;}"
        "QPushButton:hover{color:#d0d0d0;}")
    _CTRL_CSS = ("color:#9d9d9d;font-size:9pt;background:transparent;"
                 "border:none;padding:0 6px;")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SemanticTreePanel")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        bar = QWidget()
        bar.setStyleSheet("background:#0d1014;")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(10, 5, 10, 5)
        bl.setSpacing(0)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = []
        for i, label in enumerate(("Anotado", "AST original", "Lado a lado")):
            b = QPushButton(label)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(self._MODE_CSS)
            self._group.addButton(b, i)
            self._buttons.append(b)
            bl.addWidget(b)
        self._buttons[0].setChecked(True)
        bl.addStretch()
        for text, tip, slot in (
            ("Expandir todo", "Expandir todos los nodos", self.expand_all),
            ("Colapsar todo", "Colapsar todos los nodos", self.collapse_all),
        ):
            b = QPushButton(text)
            b.setFlat(True)
            b.setToolTip(tip)
            b.setStyleSheet(self._CTRL_CSS)
            b.clicked.connect(slot)
            bl.addWidget(b)
        self._info = QLabel("")
        self._info.setStyleSheet("color:#444;font-size:8pt;padding-left:8px;")
        bl.addWidget(self._info)
        root.addWidget(bar)

        self._ann = SemanticTreeView("ÁRBOL ANOTADO SEMÁNTICO", True)
        self._orig = SemanticTreeView("AST ORIGINAL (PARSER)", False)
        self._sbs_orig = SemanticTreeView("AST ORIGINAL", False)
        self._sbs_ann = SemanticTreeView("ÁRBOL ANOTADO", True)
        self._views = (self._ann, self._orig, self._sbs_orig, self._sbs_ann)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._sbs_orig)
        split.addWidget(self._sbs_ann)
        split.setSizes([1, 1])
        # desplazamiento sincronizado entre los dos lados
        a, b_ = self._sbs_orig.verticalScrollBar(), self._sbs_ann.verticalScrollBar()
        a.valueChanged.connect(b_.setValue)
        b_.valueChanged.connect(a.setValue)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._ann)
        self._stack.addWidget(self._orig)
        self._stack.addWidget(split)
        root.addWidget(self._stack)
        self._group.idClicked.connect(self._stack.setCurrentIndex)

        self._collapsed: set = set()
        for v in self._views:
            v.toggled.connect(self._on_toggled)
            v.expand_requested.connect(self.expand_all)
            v.collapse_requested.connect(self.collapse_all)

    # ── Estado de colapso compartido ──────────────────────────────
    def _apply(self):
        for v in self._views:
            v.set_collapsed(self._collapsed)

    def _on_toggled(self, idx: int):
        self._collapsed ^= {idx}
        self._apply()

    def expand_all(self):
        self._collapsed = set()
        self._apply()

    def collapse_all(self):
        self._collapsed = self._ann.collapsible_ids()
        self._apply()

    # ── API ───────────────────────────────────────────────────────
    def set_mode(self, index: int):
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)
            self._stack.setCurrentIndex(index)

    def show_empty(self):
        self._collapsed = set()
        self._info.setText("")
        for v in self._views:
            v.show_empty()

    def load(self, original_root, annotated_root, n_errors: int = 0):
        """Renderiza las vistas a partir del AST original y su copia anotada."""
        self._collapsed = set()
        self._ann.load(annotated_root)
        self._sbs_ann.load(annotated_root)
        self._orig.load(original_root)
        self._sbs_orig.load(original_root)
        err = f" · {n_errors} error(es)" if n_errors else ""
        self._info.setText(f"{self._ann._total} nodos{err}")
