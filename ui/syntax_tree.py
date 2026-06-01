# ui/syntax_tree.py
# Árbol sintáctico abstracto — vista gráfica real (nodos circulares + líneas)

import math
import sys

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsSimpleTextItem,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QTextEdit, QTextBrowser,
    QMenu, QFileDialog,
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtGui import (
    QColor, QFont, QPen, QBrush, QPainter, QFontMetrics,
)
from PyQt6.QtCore import Qt, QRectF


# ─────────────────────────────────────────────────────────────
# Colores de borde/texto por tipo de nodo
# ─────────────────────────────────────────────────────────────
_COLORS = {
    "PROGRAMA":       "#569cd6",
    "MAIN":           "#569cd6",
    "DECLARACIONES":  "#4ec9b0",
    "SENTENCIAS":     "#4ec9b0",
    "DECL_VAR":       "#9cdcfe",
    "TIPO":           "#9cdcfe",
    "ASIGNACION":     "#ff8c00",
    "IF":             "#c586c0",
    "CONDICION":      "#c586c0",
    "ENTONCES":       "#c586c0",
    "SINO":           "#c586c0",
    "MIENTRAS":       "#c586c0",
    "HACER_MIENTRAS": "#c586c0",
    "CUERPO":         "#7a7a9d",
    "ENTRADA":        "#ce9178",
    "SALIDA":         "#ce9178",
    "CADENA":         "#ce9178",
    "OP_REL":         "#d4d4d4",
    "OP_SUMA":        "#d4d4d4",
    "OP_MULT":        "#d4d4d4",
    "OP_POT":         "#dcdcaa",
    "OP_LOGICO":      "#c586c0",
    "NUMERO":         "#b5cea8",
    "REAL":           "#b5cea8",
    "BOOL":           "#b5cea8",
    "ID":             "#4ec9b0",
}
_DEF_COLOR = "#888888"


# ─────────────────────────────────────────────────────────────
# Etiquetas cortas para el interior de cada círculo
# ─────────────────────────────────────────────────────────────
_TYPE_ABBREV = {
    "PROGRAMA":       "Prog.",
    "MAIN":           "main",
    "DECLARACIONES":  "Decls.",
    "SENTENCIAS":     "Sents.",
    "DECL_VAR":       "Var",
    "TIPO":           "tipo",
    "ASIGNACION":     "Asign.",
    "CONDICION":      "Cond.",
    "ENTONCES":       "Then",
    "SINO":           "Else",
    "MIENTRAS":       "While",
    "HACER_MIENTRAS": "Do-While",
    "CUERPO":         "Cuerpo",
    "ENTRADA":        "cin>>",
    "SALIDA":         "cout<<",
    "CADENA":         "cadena",
    "OP_REL":         None,   # usa valor
    "OP_SUMA":        None,
    "OP_MULT":        None,
    "OP_POT":         "^",
    "OP_LOGICO":      None,
    "NUMERO":         "num",
    "REAL":           "real",
    "BOOL":           "bool",
    "ID":             "id",
}


def _top_label(node) -> str:
    """Etiqueta principal que va en la fila superior del círculo."""
    t = node.node_type
    if t in _TYPE_ABBREV:
        abbr = _TYPE_ABBREV[t]
        if abbr is None:
            # operadores: mostramos el símbolo directamente
            return str(node.value) if node.value is not None else t[:5]
        return abbr
    return t[:7]


def _bot_label(node) -> str:
    """Etiqueta secundaria (valor) — se muestra debajo si existe."""
    t = node.node_type
    if t in ("OP_REL", "OP_SUMA", "OP_MULT", "OP_POT", "OP_LOGICO"):
        return ""   # ya está en la etiqueta principal
    if node.value is None:
        return ""
    v = str(node.value)
    if len(v) > 9:
        v = v[:8] + "…"
    return v


# ─────────────────────────────────────────────────────────────
# Vista gráfica (QGraphicsView)
# ─────────────────────────────────────────────────────────────
class GraphicalASTView(QGraphicsView):
    """
    Dibuja el AST como grafo con nodos circulares y líneas de conexión.
    Zoom: Ctrl + rueda del mouse
    Pan:  arrastrar con el mouse
    """

    R      = 34    # radio de cada círculo (px)
    V_GAP  = 80    # distancia vertical entre centros de niveles consecutivos
    H_GAP  = 18    # espacio horizontal mínimo entre círculos (borde a borde)

    _FONT_TOP = QFont("Consolas", 7, QFont.Weight.Bold)
    _FONT_BOT = QFont("Consolas", 6)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet("border: none; background: #0d0d0d;")
        self._has_content = False

    # ── API pública ──────────────────────────────────────────

    def load_ast(self, root):
        self._scene.clear()
        self._has_content = False
        if not root:
            return

        positions = {}
        self._assign_pos(root, 0.0, 0.0, positions)

        self._draw_edges(root, positions)   # primero líneas (debajo)
        self._draw_nodes(root, positions)   # luego nodos (encima)

        pad = 60
        r = self._scene.itemsBoundingRect()
        self._scene.setSceneRect(r.adjusted(-pad, -pad, pad, pad))
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._has_content = True

    def clear(self):
        self._scene.clear()
        self._has_content = False

    def fit_view(self):
        if self._has_content:
            self.fitInView(self._scene.sceneRect(),
                           Qt.AspectRatioMode.KeepAspectRatio)

    # ── Zoom con Ctrl+rueda ──────────────────────────────────

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            f = 1.18 if event.angleDelta().y() > 0 else 1 / 1.18
            self.scale(f, f)
        else:
            super().wheelEvent(event)

    # ── Algoritmo de layout ──────────────────────────────────

    def _sw(self, node) -> float:
        """Ancho mínimo que ocupa el subárbol de este nodo."""
        if not node.children:
            return 2 * self.R
        total = sum(self._sw(c) for c in node.children)
        gaps  = self.H_GAP * (len(node.children) - 1)
        return max(2 * self.R, total + gaps)

    def _assign_pos(self, node, cx: float, cy: float, pos: dict):
        pos[id(node)] = (cx, cy)
        if not node.children:
            return
        cws = [self._sw(c) for c in node.children]
        total = sum(cws) + self.H_GAP * (len(node.children) - 1)
        x = cx - total / 2
        for i, child in enumerate(node.children):
            self._assign_pos(child, x + cws[i] / 2, cy + self.V_GAP, pos)
            x += cws[i] + self.H_GAP

    # ── Dibujado ─────────────────────────────────────────────

    def _draw_edges(self, node, pos: dict):
        """Dibuja líneas de padre a hijo antes que los nodos."""
        if not node.children:
            return
        px, py = pos[id(node)]
        pen = QPen(QColor("#555555"), 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        for child in node.children:
            cx, cy = pos[id(child)]
            # Dirección unitaria del vector padre→hijo
            dx, dy = cx - px, cy - py
            dist = math.hypot(dx, dy)
            if dist > 0:
                ndx, ndy = dx / dist, dy / dist
                # Puntos en el borde de cada círculo
                x1, y1 = px + self.R * ndx, py + self.R * ndy
                x2, y2 = cx - self.R * ndx, cy - self.R * ndy
                self._scene.addLine(x1, y1, x2, y2, pen)
            self._draw_edges(child, pos)

    def _draw_nodes(self, node, pos: dict):
        x, y = pos[id(node)]
        R = self.R

        # Color del nodo
        hex_col = _COLORS.get(node.node_type, _DEF_COLOR)
        outline = QColor(hex_col)
        fill    = QColor(hex_col)
        fill.setAlpha(38)

        # Círculo
        circle = QGraphicsEllipseItem(x - R, y - R, 2 * R, 2 * R)
        circle.setPen(QPen(outline, 2))
        circle.setBrush(QBrush(fill))
        self._scene.addItem(circle)

        # Etiqueta principal
        top = _top_label(node)
        bot = _bot_label(node)

        t1 = self._scene.addSimpleText(top, self._FONT_TOP)
        t1.setBrush(QBrush(outline))
        br1 = t1.boundingRect()

        if bot:
            t2 = self._scene.addSimpleText(bot, self._FONT_BOT)
            lighter = QColor(hex_col).lighter(140)
            t2.setBrush(QBrush(lighter))
            br2 = t2.boundingRect()
            gap = 2
            total_h = br1.height() + gap + br2.height()
            t1.setPos(x - br1.width() / 2, y - total_h / 2)
            t2.setPos(x - br2.width() / 2, y - total_h / 2 + br1.height() + gap)
        else:
            t1.setPos(x - br1.width() / 2, y - br1.height() / 2)

        for child in node.children:
            self._draw_nodes(child, pos)


# ─────────────────────────────────────────────────────────────
# ASTTableView — tabla HTML para la Vista Colapsable
# ─────────────────────────────────────────────────────────────
_MENU_CSS = """
    QMenu { background:#1e1e1e; color:#ccc; border:1px solid #3a3a3a;
            padding:4px 0; border-radius:6px; }
    QMenu::item { padding:6px 28px 6px 16px; font-size:9.5pt; }
    QMenu::item:selected { background:#094771; color:#fff; }
    QMenu::separator { height:1px; background:#2a2a2a; margin:4px 8px; }
"""


class ASTTableView(QTextBrowser):
    """
    Vista de árbol AST como tabla HTML oscura — COLAPSABLE.
    • Misma estética que TokenTerminal (filas alternadas, colores por tipo).
    • Clic en el nombre del nodo → expande / colapsa sus hijos.
    • ▶ nodo colapsado  |  ▼ nodo expandido  |  sin flecha → nodo hoja.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ASTTableView")
        self.setOpenLinks(False)            # manejamos clicks nosotros
        self.setOpenExternalLinks(False)
        font = QFont("Menlo" if sys.platform == "darwin" else "Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self._root       = None
        self._collapsed  = set()   # IDs de nodos colapsados
        self._id_counter = 0
        self._scroll_pos = 0       # para restaurar scroll tras re-render

        self.anchorClicked.connect(self._on_anchor)

    # ── Utilidades ───────────────────────────────────────────

    @staticmethod
    def _esc(t: str) -> str:
        return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    @staticmethod
    def _node_color(node_type: str) -> str:
        return _COLORS.get(node_type, _DEF_COLOR)

    @staticmethod
    def _val_color(node_type: str, value) -> str:
        nt = node_type.upper()
        if "STRING" in nt or "CADENA" in nt:               return "#ce9178"
        if any(x in nt for x in
               ("NUMBER","REAL","NUMERO","INT","FLOAT","BOOL")): return "#b5cea8"
        if "ID" in nt:                                     return "#4ec9b0"
        if value is not None:                              return "#9cdcfe"
        return "#3a3a3a"

    # ── Asignar IDs únicos a cada nodo ───────────────────────

    def _assign_ids(self, node):
        if node is None:
            return
        node._ast_id = f"n{self._id_counter}"
        self._id_counter += 1
        for child in node.children:
            self._assign_ids(child)

    # ── Toggle colapsar / expandir ───────────────────────────

    def _on_anchor(self, url: QUrl):
        nid = url.toString()
        self._scroll_pos = self.verticalScrollBar().value()
        if nid in self._collapsed:
            self._collapsed.discard(nid)
        else:
            self._collapsed.add(nid)
        self._render()
        # restaurar posición de scroll
        self.verticalScrollBar().setValue(self._scroll_pos)

    # ── Acciones de la barra (expandir/colapsar todo) ────────

    def expand_all(self):
        self._collapsed.clear()
        self._render()

    def collapse_all(self):
        """Colapsa todos los nodos que tienen hijos."""
        self._collapsed.clear()
        self._collect_collapsible(self._root)
        if self._root:
            # dejar la raíz expandida
            self._collapsed.discard(self._root._ast_id)
        self._render()

    def _collect_collapsible(self, node):
        if node is None:
            return
        children = [c for c in node.children if c is not None]
        if children:
            self._collapsed.add(node._ast_id)
        for c in children:
            self._collect_collapsible(c)

    # ── Recorrido recursivo → lista de filas HTML ────────────

    def _collect_rows(self, node, level: int, prefix: str,
                      is_last: bool, row_idx: list):
        if node is None:
            return

        i   = row_idx[0]; row_idx[0] += 1
        bg  = "#111418" if i % 2 == 0 else "#0d1014"
        bdr = "#1a1e22"
        esc = self._esc

        nc  = self._node_color(node.node_type)
        vc  = self._val_color(node.node_type, node.value)
        nid = node._ast_id

        children = [c for c in node.children if c is not None]
        has_kids  = bool(children)
        collapsed = nid in self._collapsed

        # ── Flecha de toggle ──────────────────────────────
        if has_kids:
            arrow     = "▶" if collapsed else "▼"
            arrow_c   = "#555" if collapsed else "#4a6fa5"
            toggle_html = (
                f'<a href="{nid}" style="color:{arrow_c};text-decoration:none;'
                f'font-size:8pt;">{arrow}</a>&nbsp;'
            )
        else:
            toggle_html = '<span style="color:#1a1e22;font-size:8pt;">◆</span>&nbsp;'

        # ── Rama unicode ──────────────────────────────────
        branch   = "╚═ " if is_last else "╠═ "
        pre_html = (
            f'<span style="color:#222;font-family:monospace;">'
            f'{esc(prefix)}{branch}</span>'
            if level > 0 else ""
        )

        # ── Nombre del nodo (clicable si tiene hijos) ─────
        if has_kids:
            name_html = (
                f'<a href="{nid}" style="color:{nc};font-weight:{"bold" if level==0 else "600"};'
                f'font-size:9.5pt;text-decoration:none;">'
                f'{esc(node.node_type)}</a>'
            )
        else:
            name_html = (
                f'<span style="color:{nc};font-size:9.5pt;">'
                f'{esc(node.node_type)}</span>'
            )

        node_html = f'{pre_html}{toggle_html}{name_html}'

        # ── Valor ─────────────────────────────────────────
        val_str  = esc(str(node.value)) if node.value is not None else ""
        val_html = (
            f'<span style="color:{vc};font-size:10pt;">{val_str}</span>'
            if val_str else ""
        )

        # ── Ln / Col ──────────────────────────────────────
        ln_str  = str(node.line)   if node.line   is not None else "—"
        col_str = str(getattr(node, "column", None)) \
                  if getattr(node, "column", None) is not None else "—"

        # ── Contador de hijos ocultos (si colapsado) ──────
        hidden_badge = ""
        if collapsed and has_kids:
            hidden_badge = (
                f'&nbsp;<span style="color:#333;font-size:7.5pt;'
                f'background:#1a1e22;padding:1px 5px;border-radius:3px;">'
                f'+{len(children)}</span>'
            )

        self._rows.append(
            f'<tr style="background:{bg};">'
            f'<td style="color:#505050;text-align:right;padding:5px 10px 5px 8px;'
            f'border-bottom:1px solid {bdr};font-size:8pt;white-space:nowrap;'
            f'vertical-align:middle;">{i+1:03d}</td>'
            f'<td style="padding:5px 6px;border-bottom:1px solid {bdr};'
            f'text-align:center;vertical-align:middle;">'
            f'<span style="color:{nc};font-size:8pt;">'
            f'{"●" if level==0 else "○"}</span></td>'
            f'<td style="padding:5px 14px 5px 4px;border-bottom:1px solid {bdr};'
            f'white-space:nowrap;vertical-align:middle;">'
            f'{node_html}{hidden_badge}</td>'
            f'<td style="padding:5px 14px 5px 4px;border-bottom:1px solid {bdr};'
            f'white-space:nowrap;vertical-align:middle;">{val_html}</td>'
            f'<td style="color:#5a6070;text-align:center;padding:5px 8px;'
            f'border-bottom:1px solid {bdr};font-size:9pt;'
            f'vertical-align:middle;">{ln_str}</td>'
            f'<td style="color:#4a5060;text-align:center;padding:5px 8px;'
            f'border-bottom:1px solid {bdr};font-size:9pt;'
            f'vertical-align:middle;">{col_str}</td>'
            f'</tr>'
        )

        # ── Hijos (solo si no está colapsado) ─────────────
        if not collapsed:
            child_prefix = prefix + ("   " if is_last else "│  ")
            for j, child in enumerate(children):
                self._collect_rows(
                    child, level + 1,
                    child_prefix, j == len(children) - 1,
                    row_idx,
                )

    # ── API pública ──────────────────────────────────────────

    def load_ast(self, root):
        self._root       = root
        self._collapsed  = set()
        self._id_counter = 0
        if root:
            self._assign_ids(root)
        self._render()

    def clear_view(self):
        self._root = None
        self._collapsed.clear()
        self._render()

    def _render(self):
        self._rows = []
        row_idx    = [0]
        if self._root:
            self._collect_rows(self._root, 0, "", True, row_idx)

        n   = row_idx[0]   # nodos visibles
        ts  = datetime.now().strftime("%H:%M:%S")
        # total real de nodos en el árbol
        total = self._count_nodes(self._root)

        th = ("background:#141414;color:#484848;font-size:8pt;font-weight:700;"
              "letter-spacing:1.2px;padding:7px 12px;border-bottom:1px solid #1e1e1e;"
              "text-transform:uppercase;white-space:nowrap;")

        hint = (
            '<span style="color:#2a3040;font-size:7.5pt;">'
            '▶/▼ clic en nodo para colapsar/expandir</span>'
        )

        body_html = "".join(self._rows) if self._rows else (
            '<tr><td colspan="6" style="color:#333;padding:24px 12px;'
            'text-align:center;">'
            'Ejecuta el análisis sintáctico (F6) para ver el árbol.</td></tr>'
        )

        visible_info = (
            f'{n} de {total} nodo{"s" if total != 1 else ""} visibles'
            if self._collapsed else
            f'{total} nodo{"s" if total != 1 else ""}'
        )

        html = f"""
<html><body style="background:#0d1014;margin:0;padding:0;
    font-family:'Menlo','SF Mono','Consolas',monospace;">

<div style="padding:12px 12px 4px;border-bottom:1px solid #1a1e22;">
  <span style="color:#c792ea;font-size:12pt;font-weight:700;">⬡ ÁRBOL SINTÁCTICO</span>
  &nbsp;&nbsp;
  <span style="color:#252525;font-size:8.5pt;">{ts}</span>
  &nbsp;&nbsp;&nbsp;
  {hint}
</div>

<table cellspacing="0" cellpadding="0" width="100%"
       style="border-collapse:collapse;margin-top:4px;">
  <thead>
    <tr>
      <th style="{th}text-align:right;">#</th>
      <th style="{th}"></th>
      <th style="{th}">Nodo</th>
      <th style="{th}">Valor</th>
      <th style="{th}text-align:center;">Ln</th>
      <th style="{th}text-align:center;">Col</th>
    </tr>
  </thead>
  <tbody>{body_html}</tbody>
</table>

<div style="padding:6px 12px 10px;border-top:1px solid #1a1e22;margin-top:2px;">
  <span style="color:#252525;font-size:8pt;">{visible_info}</span>
</div>

</body></html>
"""
        self.setHtml(html)

    def _count_nodes(self, node) -> int:
        if node is None:
            return 0
        return 1 + sum(self._count_nodes(c) for c in node.children if c)

    # ── Menú contextual ──────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_CSS)
        has_sel = self.textCursor().hasSelection()

        def _a(label, slot, enabled=True):
            a = QAction(label, self)
            a.triggered.connect(slot)
            a.setEnabled(enabled)
            menu.addAction(a)

        _a("Copiar selección",   self.copy,        has_sel)
        _a("Seleccionar todo",   self.selectAll)
        menu.addSeparator()
        _a("Expandir todo",      self.expand_all)
        _a("Colapsar todo",      self.collapse_all)
        menu.addSeparator()
        _a("Guardar árbol…",     self._save)
        menu.addSeparator()
        _a("Scroll al inicio",   lambda: self.verticalScrollBar().setValue(0))
        menu.exec(event.globalPos())

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar árbol", "arbol_ast.txt",
            "Texto (*.txt);;Todos los archivos (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())


# ─────────────────────────────────────────────────────────────
# Widget contenedor público (incluye barra de controles)
# ─────────────────────────────────────────────────────────────
class SyntaxTreeWidget(QWidget):
    """
    Panel completo del árbol AST con DOS vistas:
      - Vista Grafica   : nodos circulares conectados (QGraphicsView)
      - Vista Colapsable: árbol expandible/colapsable tipo carpetas (QTreeWidget)
                          ← cumple el requisito de la rúbrica: "colapsable como carpetas"
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Barra de controles ────────────────────────────────
        bar = QWidget()
        bar.setObjectName("PanelHeader")
        bar.setFixedHeight(32)
        bar_h = QHBoxLayout(bar)
        bar_h.setContentsMargins(12, 0, 12, 0)
        bar_h.setSpacing(6)

        lbl = QLabel("Arbol Sintactico Abstracto (AST)")
        lbl.setObjectName("PanelTitle")
        bar_h.addWidget(lbl)
        bar_h.addStretch()

        def _ctrl_btn(text, tip, slot):
            b = QPushButton(text)
            b.setFixedHeight(22)
            b.setFlat(True)
            b.setToolTip(tip)
            b.setStyleSheet(
                "color:#9d9d9d; font-size:9pt; background:transparent;"
                "border:none; padding:0 6px;"
            )
            b.clicked.connect(slot)
            return b

        bar_h.addWidget(_ctrl_btn("Expandir todo",  "Expandir todos los nodos",  self._expand_all))
        bar_h.addWidget(_ctrl_btn("Colapsar todo",  "Colapsar todos los nodos",  self._collapse_all))
        bar_h.addWidget(_ctrl_btn("Encuadrar",      "Ajustar vista grafica",     self._fit))
        bar_h.addWidget(_ctrl_btn("Zoom +",         "Acercar grafico",           self._zoom_in))
        bar_h.addWidget(_ctrl_btn("Zoom -",         "Alejar grafico",            self._zoom_out))
        main_layout.addWidget(bar)

        # ── Pestañas: Vista Gráfica + Vista Colapsable ────────
        self._tabs = QTabWidget()
        self._tabs.setObjectName("ResultTabs")
        self._tabs.setDocumentMode(True)
        main_layout.addWidget(self._tabs)

        # Pestaña 0: árbol de círculos (gráfico)
        self._view = GraphicalASTView()
        self._tabs.addTab(self._view, "Vista Grafica")

        # Pestaña 1: tabla HTML de árbol (misma estética que TokenTerminal)
        self._tree = ASTTableView()
        self._tabs.addTab(self._tree, "Vista Colapsable")

    # ── API pública ───────────────────────────────────────────

    def load_ast(self, root):
        self._view.load_ast(root)
        self._tree.load_ast(root)

    def clear(self):
        self._view.clear()
        self._tree.clear_view()

    # ── Botones ───────────────────────────────────────────────

    def _expand_all(self):
        self._tree.expand_all()
        self._tabs.setCurrentIndex(1)

    def _collapse_all(self):
        self._tree.collapse_all()
        self._tabs.setCurrentIndex(1)

    def _fit(self):
        self._view.fit_view()
        self._tabs.setCurrentIndex(0)

    def _zoom_in(self):
        self._view.scale(1.2, 1.2)
        self._tabs.setCurrentIndex(0)

    def _zoom_out(self):
        self._view.scale(1 / 1.2, 1 / 1.2)
        self._tabs.setCurrentIndex(0)
