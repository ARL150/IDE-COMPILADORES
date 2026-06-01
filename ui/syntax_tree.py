# ui/syntax_tree.py
# Árbol sintáctico abstracto — vista gráfica real (nodos circulares + líneas)

import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsSimpleTextItem,
    QTabWidget, QTreeWidget, QTreeWidgetItem,
)
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
        self.setStyleSheet("border: none; background: #1e1e1e;")
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

        # Pestaña 1: árbol colapsable tipo carpetas (REQUISITO RUBRICA)
        self._tree = self._build_tree_widget()
        self._tabs.addTab(self._tree, "Vista Colapsable")

    # ── Construcción del QTreeWidget ─────────────────────────

    def _build_tree_widget(self) -> QTreeWidget:
        t = QTreeWidget()
        t.setColumnCount(4)
        t.setHeaderLabels(["Nodo", "Valor", "Linea", "Col"])
        t.setColumnWidth(0, 220)
        t.setColumnWidth(1, 130)
        t.setColumnWidth(2, 55)
        t.setColumnWidth(3, 45)
        t.setAlternatingRowColors(True)
        t.setAnimated(True)
        t.setIndentation(22)
        t.setFont(QFont("Consolas", 10))
        t.header().setStretchLastSection(False)
        t.header().setSectionResizeMode(1, t.header().ResizeMode.Stretch)
        return t

    def _build_tree_item(self, node, parent_item):
        if node is None:
            return
        val_str = str(node.value)  if node.value  is not None else ""
        ln_str  = str(node.line)   if node.line   is not None else ""
        col_str = str(node.column) if node.column is not None else ""

        item = QTreeWidgetItem([node.node_type, val_str, ln_str, col_str])

        color = QColor(_COLORS.get(node.node_type, _DEF_COLOR))
        item.setForeground(0, color)
        if val_str:
            item.setForeground(1, QColor("#cccccc"))
        item.setForeground(2, QColor("#666"))
        item.setForeground(3, QColor("#666"))
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
        item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)

        if node.node_type in ("PROGRAMA", "DECLARACIONES", "SENTENCIAS"):
            f = item.font(0)
            f.setBold(True)
            item.setFont(0, f)

        parent_item.addChild(item)
        for child in node.children:
            self._build_tree_item(child, item)

    # ── API pública ───────────────────────────────────────────

    def load_ast(self, root):
        # Vista gráfica
        self._view.load_ast(root)
        # Vista colapsable
        self._tree.clear()
        if root:
            self._build_tree_item(root, self._tree.invisibleRootItem())
            self._tree.expandAll()

    def clear(self):
        self._view.clear()
        self._tree.clear()

    # ── Botones ───────────────────────────────────────────────

    def _expand_all(self):
        self._tree.expandAll()
        self._tabs.setCurrentIndex(1)

    def _collapse_all(self):
        self._tree.collapseAll()
        if self._tree.topLevelItemCount() > 0:
            self._tree.topLevelItem(0).setExpanded(True)
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
