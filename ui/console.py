import re
import sys
from datetime import datetime
from PyQt6.QtWidgets import QTextEdit, QMenu, QFileDialog
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtCore import Qt

# ── Colores por tipo de token léxico ─────────────────────────────────────────
_TOKEN_COLORS = {
    # Palabras clave
    "MAIN":"#569cd6","IF":"#569cd6","THEN":"#569cd6","ELSE":"#569cd6",
    "END":"#569cd6","WHILE":"#569cd6","DO":"#569cd6","FOR":"#569cd6",
    "CIN":"#569cd6","COUT":"#569cd6","RETURN":"#569cd6",
    "INT":"#9cdcfe","FLOAT":"#9cdcfe","BOOL":"#9cdcfe",
    "TRUE":"#4fc1ff","FALSE":"#4fc1ff",
    # Identificadores y literales
    "ID":"#4ec9b0",
    "NUMBER":"#b5cea8","INTEGER":"#b5cea8","REAL":"#b5cea8",
    "STRING":"#ce9178",
    # Operadores aritméticos
    "PLUS":"#d4d4d4","MINUS":"#d4d4d4","MULT":"#d4d4d4","DIV":"#d4d4d4",
    "MOD":"#d4d4d4","POWER":"#dcdcaa",
    "INCREMENT":"#f78c6c","DECREMENT":"#f78c6c",
    # Operadores lógicos / relacionales
    "AND":"#c586c0","OR":"#c586c0","NOT":"#c586c0",
    "LT":"#82aaff","LE":"#82aaff","GT":"#82aaff","GE":"#82aaff",
    "EQ":"#82aaff","NE":"#82aaff",
    # Asignación y puntuación
    "EQUAL":"#d7ba7d","ASSIGN":"#d7ba7d",
    "LPAREN":"#ffd700","RPAREN":"#ffd700",
    "LBRACE":"#ffd700","RBRACE":"#ffd700",
    "SEMICOLON":"#666","COMMA":"#666","COLON":"#666",
    # Bits
    "SHIFT_LEFT":"#d4d4d4","SHIFT_RIGHT":"#d4d4d4",
}
_TOKEN_CATEGORIES = {
    "keyword": {"#569cd6", "#9cdcfe", "#4fc1ff"},
}
def _token_color(tipo: str) -> str:
    return _TOKEN_COLORS.get(tipo.upper(), "#9d9d9d")

# ── Colores por categoría de nodo AST ────────────────────────────────────────
_NODE_COLORS = {
    # Raíz / estructura
    "Program":          "#7dd3fc",
    "Block":            "#7dd3fc",
    "Body":             "#7dd3fc",
    # Declaraciones
    "VarDecl":          "#c792ea",
    "FuncDecl":         "#c792ea",
    "Declaration":      "#c792ea",
    "Param":            "#c792ea",
    # Control de flujo
    "If":               "#82aaff",
    "IfStatement":      "#82aaff",
    "Else":             "#82aaff",
    "While":            "#82aaff",
    "WhileLoop":        "#82aaff",
    "For":              "#82aaff",
    "ForLoop":          "#82aaff",
    "Return":           "#82aaff",
    # Expresiones
    "Assign":           "#ffcb6b",
    "Assignment":       "#ffcb6b",
    "BinaryOp":         "#f78c6c",
    "UnaryOp":          "#f78c6c",
    "Call":             "#80cbc4",
    "FuncCall":         "#80cbc4",
    # Hojas
    "ID":               "#4ec9b0",
    "Identifier":       "#4ec9b0",
    "Number":           "#b5cea8",
    "Integer":          "#b5cea8",
    "Float":            "#b5cea8",
    "Real":             "#b5cea8",
    "String":           "#ce9178",
    "Bool":             "#569cd6",
    "True":             "#569cd6",
    "False":            "#569cd6",
    # I/O
    "Print":            "#ce93d8",
    "Read":             "#ce93d8",
    "Cout":             "#ce93d8",
    "Cin":              "#ce93d8",
}

_MENU_CSS = """
    QMenu { background:#1e1e1e; color:#ccc; border:1px solid #3a3a3a;
            padding:4px 0; border-radius:6px; }
    QMenu::item { padding:6px 28px 6px 16px; font-size:9.5pt; }
    QMenu::item:selected { background:#094771; color:#fff; }
    QMenu::separator { height:1px; background:#2a2a2a; margin:4px 8px; }
"""


# ═══════════════════════════════════════════════════════════════
# CompilerConsole — terminal de salida principal
# ═══════════════════════════════════════════════════════════════
class CompilerConsole(QTextEdit):

    _BADGES = {
        "info":    ("▸", "#64b5f6"),
        "ok":      ("✔", "#81c784"),
        "warning": ("⚠", "#ffb74d"),
        "error":   ("✖", "#f28b82"),
        "step":    ("◆", "#ce93d8"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompilerConsole")
        self.setReadOnly(True)
        font = QFont("Menlo" if sys.platform == "darwin" else "Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

    @staticmethod
    def _ts():
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _esc(t):
        return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def _append(self, ts_color, ts, sym, badge_color, msg_color, msg):
        html = (
            f'<span style="color:{ts_color};font-size:8.5pt;">{ts}</span>'
            f'&nbsp;&nbsp;'
            f'<span style="color:{badge_color};font-weight:600;">{sym}</span>'
            f'&nbsp;'
            f'<span style="color:{msg_color};">{self._esc(msg)}</span>'
        )
        self.append(html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def info(self, msg):
        s, c = self._BADGES["info"]
        self._append("#3a3a3a", self._ts(), s, c, "#9d9d9d", msg)

    def ok(self, msg):
        s, c = self._BADGES["ok"]
        self._append("#3a3a3a", self._ts(), s, c, "#cccccc", msg)

    def warning(self, msg):
        s, c = self._BADGES["warning"]
        self._append("#3a3a3a", self._ts(), s, c, "#e0c080", msg)

    def error(self, msg):
        s, c = self._BADGES["error"]
        self._append("#3a3a3a", self._ts(), s, c, c, msg)

    def step(self, num, msg):
        s, c = self._BADGES["step"]
        self._append("#3a3a3a", self._ts(), f"{s} {num}", c, "#cccccc", msg)

    def heading(self, text):
        self.append(
            f'<span style="color:#7dd3fc;font-weight:700;font-size:10pt;">'
            f'{self._esc(text)}</span>'
        )
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def separator(self, label: str = ""):
        w = 52
        if label:
            pad  = max(2, (w - len(label) - 2) // 2)
            line = "─" * pad + f" {label} " + "─" * pad
        else:
            line = "─" * w
        self.append(f'<span style="color:#2a2a2a;">{line}</span>')
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear_log(self):
        self.clear()

    def welcome(self):
        in_venv = sys.prefix != sys.base_prefix
        venv_txt = (
            '<span style="color:#22c55e;font-size:8.5pt;"> ● venv</span>'
            if in_venv else ""
        )
        self.append(f'<span style="color:#1e2a1e;font-size:8pt;">{"─"*52}</span>')
        self.append(
            f'<span style="color:#7dd3fc;font-weight:700;font-size:11pt;">  IDE Compilador</span>'
            f'<span style="color:#3a3a3a;font-size:9pt;"> v2.1</span>'
            f'{venv_txt}'
        )
        self.append(
            f'<span style="color:#333;font-size:8.5pt;">'
            f'  Análisis léxico &amp; sintáctico — Fase 2</span>'
        )
        self.append(f'<span style="color:#1e2a1e;font-size:8pt;">{"─"*52}</span>')
        self.append("")
        self.info("Listo. Escribe código o arrastra un archivo al editor.")
        self.info("F5 léxico · F6 sintáctico · F7 compilar · Ctrl+Shift+P comandos")
        self.append("")

    # ── Menú contextual ──────────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_CSS)

        has_sel = self.textCursor().hasSelection()

        def _a(label, slot, enabled=True):
            a = QAction(label, self)
            a.triggered.connect(slot)
            a.setEnabled(enabled)
            menu.addAction(a)

        _a("Copiar selección",   self.copy,          has_sel)
        _a("Seleccionar todo",   self.selectAll)
        menu.addSeparator()
        _a("Limpiar consola",    self.clear_log)
        _a("Guardar salida…",    self._save_output)
        menu.addSeparator()
        _a("Scroll al inicio",   lambda: self.verticalScrollBar().setValue(0))
        _a("Scroll al final",
           lambda: self.verticalScrollBar().setValue(
               self.verticalScrollBar().maximum()))

        menu.exec(event.globalPos())

    def _save_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar salida de consola", "consola.txt",
            "Texto (*.txt);;Todos los archivos (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())


# ═══════════════════════════════════════════════════════════════
# ErrorTerminal — terminal de errores con fondo negro
# ═══════════════════════════════════════════════════════════════
class ErrorTerminal(QTextEdit):

    def __init__(self, accent="#f28b82", label="ERRORES", parent=None):
        super().__init__(parent)
        self.setObjectName("ErrorTerminal")
        self.setReadOnly(True)
        self._accent = accent
        self._label  = label
        font = QFont("Menlo" if sys.platform == "darwin" else "Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

    @staticmethod
    def _esc(t):
        return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def _scroll_top(self):
        self.verticalScrollBar().setValue(0)

    def show_ok(self, msg="Sin errores"):
        """Pantalla de 'sin errores' con header completo y banner verde estilizado."""
        ts = datetime.now().strftime("%H:%M:%S")
        icon = "◈" if "léxico" in msg.lower() else "⬡"
        title = self._label
        html = f"""
<html><body style="background:#0d1014;margin:0;padding:0;
    font-family:'Menlo','SF Mono','Consolas',monospace;">

<!-- HEADER -->
<div style="padding:10px 14px 6px;">
  <span style="color:#1e1e1e;font-size:7pt;">{'─' * 60}</span>
</div>
<div style="padding:2px 14px 8px;">
  <span style="color:{self._accent};font-size:12pt;font-weight:700;">
    {icon} {title}</span>
  &nbsp;&nbsp;&nbsp;
  <span style="color:#333;font-size:8.5pt;">{ts}</span>
</div>
<div style="padding:0 14px 10px;">
  <span style="color:#1e1e1e;font-size:7pt;">{'─' * 60}</span>
</div>

<!-- BANNER OK -->
<div style="margin:14px 14px 8px;padding:10px 16px;
  background:#0a1a0a;border-left:3px solid #22c55e;
  border-radius:0 4px 4px 0;">
  <span style="color:#22c55e;font-size:11pt;font-weight:700;">✔</span>
  &nbsp;&nbsp;
  <span style="color:#81c784;font-size:10pt;">{self._esc(msg)}</span>
</div>

</body></html>
"""
        self.setHtml(html)
        self.verticalScrollBar().setValue(0)

    def show_lex_errors(self, lex_errors):
        self.clear()
        if not lex_errors:
            self.show_ok("Sin errores léxicos detectados"); return
        ts = datetime.now().strftime("%H:%M:%S")
        self.append(
            f'<div style="padding:10px 14px 6px;">'
            f'<span style="color:#1e1e1e;font-size:7pt;">{"─" * 60}</span>'
            f'</div>'
        )
        self.append(
            f'<div style="padding:2px 14px 8px;">'
            f'<span style="color:{self._accent};font-size:12pt;font-weight:700;">'
            f'◈ {self._label}</span>'
            f'&nbsp;&nbsp;&nbsp;'
            f'<span style="color:#333;font-size:8.5pt;">{ts}</span>'
            f'&nbsp;&nbsp;'
            f'<span style="color:#3a3a3a;font-size:8pt;">{len(lex_errors)} error(es)</span>'
            f'</div>'
        )
        self.append(
            f'<div style="padding:0 14px 10px;">'
            f'<span style="color:#1e1e1e;font-size:7pt;">{"─" * 60}</span>'
            f'</div>'
        )
        for i, (sym, line, col) in enumerate(lex_errors):
            self.append(
                f'<div style="margin:3px 8px;padding:7px 14px;'
                f'background:#160000;border-left:3px solid {self._accent};border-radius:0 3px 3px 0;">'
                f'<span style="color:#444;font-size:8pt;">#{i+1:02d}</span>'
                f'&nbsp;&nbsp;'
                f'<span style="color:{self._accent};font-weight:700;">Símbolo no reconocido</span>'
                f'&nbsp;&nbsp;'
                f'<span style="color:#ffaaaa;font-family:monospace;font-size:11pt;">"{self._esc(sym)}"</span>'
                f'<br/>'
                f'<span style="color:#444;font-size:8.5pt;">'
                f'&nbsp;&nbsp;&nbsp;&nbsp;Línea&nbsp;{line}&nbsp;&nbsp;·&nbsp;&nbsp;Columna&nbsp;{col}</span>'
                f'</div>'
            )
        self._scroll_top()

    def show_syn_errors(self, syn_errors):
        self.clear()
        if not syn_errors:
            self.show_ok("Sin errores sintácticos detectados"); return
        ts = datetime.now().strftime("%H:%M:%S")
        self.append(
            f'<div style="padding:10px 14px 6px;">'
            f'<span style="color:#1e1e1e;font-size:7pt;">{"─" * 60}</span>'
            f'</div>'
        )
        self.append(
            f'<div style="padding:2px 14px 8px;">'
            f'<span style="color:{self._accent};font-size:12pt;font-weight:700;">'
            f'⬡ {self._label}</span>'
            f'&nbsp;&nbsp;&nbsp;'
            f'<span style="color:#333;font-size:8.5pt;">{ts}</span>'
            f'&nbsp;&nbsp;'
            f'<span style="color:#3a3a3a;font-size:8pt;">{len(syn_errors)} error(es)</span>'
            f'</div>'
        )
        self.append(
            f'<div style="padding:0 14px 10px;">'
            f'<span style="color:#1e1e1e;font-size:7pt;">{"─" * 60}</span>'
            f'</div>'
        )
        for i, err in enumerate(syn_errors):
            m_ln  = re.search(r'línea\s+(\d+)', err)
            m_cl  = re.search(r'columna\s+(\d+)', err)
            desc  = re.sub(r'\(línea.*?\)', '', err).strip()
            pos   = ""
            if m_ln:
                pos = f"Línea&nbsp;{m_ln.group(1)}"
                if m_cl:
                    pos += f"&nbsp;&nbsp;·&nbsp;&nbsp;Columna&nbsp;{m_cl.group(1)}"
            self.append(
                f'<div style="margin:3px 8px;padding:7px 14px;'
                f'background:#120800;border-left:3px solid {self._accent};border-radius:0 3px 3px 0;">'
                f'<span style="color:#444;font-size:8pt;">#{i+1:02d}</span>'
                f'&nbsp;&nbsp;'
                f'<span style="color:{self._accent};font-weight:700;">Error sintáctico</span>'
                f'<br/>'
                f'<span style="color:#e0b060;font-size:9.5pt;">'
                f'&nbsp;&nbsp;&nbsp;&nbsp;{self._esc(desc)}</span>'
                + (f'<br/><span style="color:#444;font-size:8.5pt;">'
                   f'&nbsp;&nbsp;&nbsp;&nbsp;{pos}</span>' if pos else '')
                + f'</div>'
            )
        self._scroll_top()

    # ── Menú contextual ──────────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_CSS)
        has_sel = self.textCursor().hasSelection()

        def _a(label, slot, enabled=True):
            a = QAction(label, self)
            a.triggered.connect(slot)
            a.setEnabled(enabled)
            menu.addAction(a)

        _a("Copiar selección",  self.copy,   has_sel)
        _a("Seleccionar todo",  self.selectAll)
        menu.addSeparator()
        _a("Limpiar",           self.clear)
        _a("Guardar errores…",  self._save_output)
        menu.addSeparator()
        _a("Scroll al inicio",  lambda: self.verticalScrollBar().setValue(0))

        menu.exec(event.globalPos())

    def _save_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar errores", "errores.txt",
            "Texto (*.txt);;Todos los archivos (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())


# ═══════════════════════════════════════════════════════════════
# TokenTerminal — tabla HTML mínima para tokens léxicos
# ═══════════════════════════════════════════════════════════════
class TokenTerminal(QTextEdit):
    """
    Tabla HTML oscura para mostrar tokens.
    Columnas fijas: #  |  TIPO  |  LEXEMA  |  LN  |  COL
    Una sola llamada setHtml() → alineación perfecta, sin ruido visual.
    """

    # Categorías para el dot indicador de color de fila
    _KW  = {"MAIN","IF","THEN","ELSE","END","WHILE","DO","FOR","CIN","COUT","RETURN",
            "INT","FLOAT","BOOL","TRUE","FALSE"}
    _LIT = {"NUMBER","INTEGER","REAL","STRING"}
    _OP  = {"PLUS","MINUS","MULT","DIV","MOD","POWER","INCREMENT","DECREMENT",
            "AND","OR","NOT","LT","LE","GT","GE","EQ","NE","EQUAL","ASSIGN",
            "SHIFT_LEFT","SHIFT_RIGHT"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TokenTerminal")
        self.setReadOnly(True)
        font = QFont("Menlo" if sys.platform == "darwin" else "Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

    @staticmethod
    def _esc(t: str) -> str:
        return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    @staticmethod
    def _lex_color(tipo: str) -> str:
        t = tipo.upper()
        if t == "ID":               return "#4ec9b0"
        if t in ("NUMBER","INTEGER","REAL"): return "#b5cea8"
        if t == "STRING":           return "#ce9178"
        if t in ("TRUE","FALSE"):   return "#4fc1ff"
        return "#d4d4d4"

    @staticmethod
    def _build_stats(tokens: list) -> str:
        """Mini-tabla de estadísticas por categoría de token."""
        kw   = sum(1 for t in tokens if t[0].upper() in TokenTerminal._KW)
        ids  = sum(1 for t in tokens if t[0].upper() == "ID")
        lits = sum(1 for t in tokens if t[0].upper() in TokenTerminal._LIT)
        ops  = sum(1 for t in tokens if t[0].upper() in TokenTerminal._OP)
        rest = len(tokens) - kw - ids - lits - ops

        cats = [
            ("#569cd6", "Keywords",     kw),
            ("#4ec9b0", "Identificadores", ids),
            ("#b5cea8", "Literales",    lits),
            ("#c586c0", "Operadores",   ops),
            ("#666",    "Otros",        rest),
        ]
        bars = ""
        total = len(tokens) or 1
        for color, label, count in cats:
            if count == 0:
                continue
            pct  = count / total * 100
            w_px = max(2, int(pct * 1.2))   # max ~120px
            bars += (
                f'<tr>'
                f'<td style="color:{color};font-size:8pt;padding:2px 8px 2px 0;'
                f'white-space:nowrap;">{label}</td>'
                f'<td style="padding:2px 6px;vertical-align:middle;">'
                f'<span style="display:inline-block;width:{w_px}px;height:6px;'
                f'background:{color};border-radius:3px;opacity:0.8;"></span></td>'
                f'<td style="color:#505050;font-size:8pt;padding:2px 0;'
                f'text-align:right;">{count}</td>'
                f'</tr>'
            )
        return (
            f'<div style="margin:6px 12px 2px;padding:8px 14px;'
            f'background:#0a0d10;border:1px solid #1a1e22;border-radius:5px;">'
            f'<div style="color:#2a2a2a;font-size:7.5pt;letter-spacing:1px;'
            f'margin-bottom:6px;">DISTRIBUCIÓN DE TOKENS</div>'
            f'<table cellspacing="0" cellpadding="0">{bars}</table>'
            f'</div>'
        )

    def show_tokens(self, tokens: list):
        """tokens: [(tipo, lexema, linea, col), ...]"""
        ts  = datetime.now().strftime("%H:%M:%S")
        n   = len(tokens)
        esc = self._esc

        # ── HTML completo como un solo bloque ────────────────
        rows = []
        for i, (tipo, lexema, linea, col) in enumerate(tokens):
            tc   = _token_color(tipo)
            lc   = self._lex_color(tipo)
            bg   = "#111418" if i % 2 == 0 else "#0d1014"
            bdr  = "#1a1e22"

            # Dot de categoría
            tu = tipo.upper()
            if tu in self._KW:   dot_c = "#569cd6"
            elif tu in self._LIT: dot_c = "#b5cea8"
            elif tu == "ID":      dot_c = "#4ec9b0"
            elif tu in self._OP:  dot_c = "#c586c0"
            else:                 dot_c = "#3a3a3a"

            rows.append(
                f'<tr style="background:{bg};">'
                # #
                f'<td style="color:#505050;text-align:right;padding:5px 10px 5px 8px;'
                f'border-bottom:1px solid {bdr};font-size:8pt;white-space:nowrap;">'
                f'{i+1:03d}</td>'
                # dot
                f'<td style="padding:5px 6px;border-bottom:1px solid {bdr};'
                f'text-align:center;">'
                f'<span style="color:{dot_c};font-size:9pt;">●</span></td>'
                # TIPO
                f'<td style="padding:5px 14px 5px 4px;border-bottom:1px solid {bdr};'
                f'white-space:nowrap;">'
                f'<span style="color:{tc};font-weight:700;font-size:9.5pt;">'
                f'{esc(tipo)}</span></td>'
                # LEXEMA
                f'<td style="padding:5px 14px 5px 4px;border-bottom:1px solid {bdr};'
                f'white-space:nowrap;">'
                f'<span style="color:{lc};font-size:10pt;">'
                f'{esc(str(lexema))}</span></td>'
                # LN
                f'<td style="color:#5a6070;text-align:center;padding:5px 8px;'
                f'border-bottom:1px solid {bdr};font-size:9pt;">{linea}</td>'
                # COL
                f'<td style="color:#4a5060;text-align:center;padding:5px 8px;'
                f'border-bottom:1px solid {bdr};font-size:9pt;">{col}</td>'
                f'</tr>'
            )

        th_style = (
            "background:#141414;color:#484848;font-size:8pt;font-weight:700;"
            "letter-spacing:1.2px;padding:7px 12px;border-bottom:1px solid #1e1e1e;"
            "text-transform:uppercase;white-space:nowrap;"
        )

        stats_html = self._build_stats(tokens)

        html = f"""
<html><body style="background:#0d1014;margin:0;padding:0;
    font-family:'Menlo','SF Mono','Consolas',monospace;">

<!-- HEADER -->
<div style="padding:12px 12px 6px;border-bottom:1px solid #1a1e22;">
  <span style="color:#64b5f6;font-size:12pt;font-weight:700;">◈ ANÁLISIS LÉXICO</span>
  &nbsp;&nbsp;
  <span style="color:#252525;font-size:8.5pt;">{ts}</span>
  &nbsp;&nbsp;
  <span style="color:#2a2a2a;font-size:8pt;">{n} token{'s' if n != 1 else ''}</span>
</div>

<!-- ESTADÍSTICAS -->
{stats_html}

<!-- TABLA -->
<table cellspacing="0" cellpadding="0" width="100%"
       style="border-collapse:collapse;margin-top:4px;">
  <thead>
    <tr>
      <th style="{th_style}text-align:right;">#</th>
      <th style="{th_style}"></th>
      <th style="{th_style}">Tipo</th>
      <th style="{th_style}">Lexema</th>
      <th style="{th_style}text-align:center;">Ln</th>
      <th style="{th_style}text-align:center;">Col</th>
    </tr>
  </thead>
  <tbody>
    {''.join(rows) if rows else
     f'<tr><td colspan="6" style="color:#333;padding:20px 12px;text-align:center;">'
     f'No se encontraron tokens.</td></tr>'}
  </tbody>
</table>

<!-- FOOTER -->
<div style="padding:6px 12px 10px;border-top:1px solid #1a1e22;margin-top:2px;">
  <span style="color:#252525;font-size:8pt;">{n} token{'s' if n != 1 else ''} reconocido{'s' if n != 1 else ''}</span>
</div>

</body></html>
"""
        self.setHtml(html)
        self.verticalScrollBar().setValue(0)

    def show_empty(self):
        self.setHtml("""
<html><body style="background:#0d1014;margin:0;padding:0;
    font-family:'Menlo','SF Mono','Consolas',monospace;">
<div style="padding:12px 12px 6px;border-bottom:1px solid #1a1e22;">
  <span style="color:#64b5f6;font-size:12pt;font-weight:700;">◈ ANÁLISIS LÉXICO</span>
</div>
<div style="padding:28px 14px;text-align:center;">
  <span style="color:#2a2a2a;font-size:10pt;">
    Ejecuta el análisis léxico (F5) para ver los tokens.
  </span>
</div>
</body></html>
""")

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

        _a("Copiar selección",  self.copy,      has_sel)
        _a("Seleccionar todo",  self.selectAll)
        menu.addSeparator()
        _a("Limpiar",           self.clear)
        _a("Guardar tokens…",   self._save_output)
        menu.addSeparator()
        _a("Scroll al inicio",  lambda: self.verticalScrollBar().setValue(0))
        _a("Scroll al final",
           lambda: self.verticalScrollBar().setValue(
               self.verticalScrollBar().maximum()))

        menu.exec(event.globalPos())

    def _save_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar tokens", "tokens.txt",
            "Texto (*.txt);;Todos los archivos (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())


# ═══════════════════════════════════════════════════════════════
# SyntaxTerminal — visor del árbol sintáctico con HTML rico
# ═══════════════════════════════════════════════════════════════
class SyntaxTerminal(QTextEdit):
    """
    Terminal estilo dark que muestra el AST con:
    - Indentación visual con caracteres unicode (╠═ ╚═ │)
    - Nodos coloreados por categoría
    - Valores y posiciones con tipografía diferenciada
    - Menú contextual rico
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SyntaxTerminal")
        self.setReadOnly(True)
        font = QFont("Menlo" if sys.platform == "darwin" else "Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self._node_count = 0

    @staticmethod
    def _esc(t):
        return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _node_color(node_type: str) -> str:
        """Devuelve el color hex del tipo de nodo, con fallback inteligente."""
        if node_type in _NODE_COLORS:
            return _NODE_COLORS[node_type]
        # Búsqueda parcial (p.ej. "IfStatement" → "If")
        nt_lower = node_type.lower()
        for key, color in _NODE_COLORS.items():
            if key.lower() in nt_lower or nt_lower in key.lower():
                return color
        return "#c0c0c0"

    def show_header(self, n_tokens: int = 0):
        """Encabezado animado antes del árbol."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.clear()
        self._node_count = 0
        self.append(
            f'<div style="padding:10px 14px 6px;">'
            f'<span style="color:#1e1e1e;font-size:7pt;">{"─" * 60}</span>'
            f'</div>'
        )
        self.append(
            f'<div style="padding:2px 14px 8px;">'
            f'<span style="color:#7dd3fc;font-size:12pt;font-weight:700;">'
            f'  ⬡ ÁRBOL SINTÁCTICO</span>'
            f'&nbsp;&nbsp;&nbsp;'
            f'<span style="color:#333;font-size:8.5pt;">{ts}</span>'
            + (f'&nbsp;&nbsp;<span style="color:#3a3a3a;font-size:8pt;">'
               f'{n_tokens} tokens</span>' if n_tokens else '')
            + f'</div>'
        )
        self.append(
            f'<div style="padding:0 14px 10px;">'
            f'<span style="color:#1e1e1e;font-size:7pt;">{"─" * 60}</span>'
            f'</div>'
        )

    def show_ok(self, msg: str = "Sin errores sintácticos"):
        self.append(
            f'<div style="margin:14px 14px 8px;padding:10px 16px;'
            f'background:#0a1a0a;border-left:3px solid #22c55e;border-radius:0 4px 4px 0;">'
            f'<span style="color:#22c55e;font-size:11pt;font-weight:700;">✔</span>'
            f'&nbsp;&nbsp;'
            f'<span style="color:#81c784;font-size:10pt;">{self._esc(msg)}</span>'
            f'</div>'
        )

    def append_node(self, node_type: str, value=None, line=None, col=None,
                    level: int = 0, is_last: bool = False, prefix: str = ""):
        """
        Renderiza un nodo del AST como una línea HTML enriquecida.
        prefix: prefijo acumulado de barras verticales de ancestros
        is_last: si es el último hijo de su padre
        """
        self._node_count += 1
        color = self._node_color(node_type)

        # Rama unicode
        branch = "╚═ " if is_last else "╠═ "
        connector_html = (
            f'<span style="color:#2a2a2a;font-family:monospace;">'
            f'{self._esc(prefix)}{branch}</span>'
        )

        # Tipo de nodo — badge coloreado
        type_html = (
            f'<span style="color:{color};font-weight:700;font-size:10pt;">'
            f'{self._esc(node_type)}</span>'
        )

        # Valor (si existe)
        val_html = ""
        if value is not None:
            vstr = str(value)
            # Detecta si parece string, número u operador
            if vstr.startswith('"') or vstr.startswith("'"):
                vc = "#ce9178"
            elif re.match(r'^-?\d+(\.\d+)?$', vstr):
                vc = "#b5cea8"
            elif len(vstr) <= 3 and not vstr.isalnum():
                vc = "#f78c6c"
            else:
                vc = "#9cdcfe"
            val_html = (
                f'&nbsp;<span style="color:#444;font-size:9pt;">→</span>&nbsp;'
                f'<span style="color:{vc};font-family:monospace;font-size:10pt;">'
                f'{self._esc(vstr)}</span>'
            )

        # Posición (línea:col)
        pos_html = ""
        if line is not None:
            pos_str = f"[{line}"
            if col is not None:
                pos_str += f":{col}"
            pos_str += "]"
            pos_html = (
                f'&nbsp;&nbsp;<span style="color:#2e2e2e;font-size:8pt;">'
                f'{pos_str}</span>'
            )

        self.append(
            f'<div style="margin:0;padding:1px 8px;">'
            f'{connector_html}{type_html}{val_html}{pos_html}'
            f'</div>'
        )

    def show_empty(self):
        """AST vacío / parse fallido."""
        self.append(
            f'<div style="margin:20px 14px;padding:12px 16px;'
            f'background:#0d0d0d;border-left:3px solid #444;border-radius:0 4px 4px 0;">'
            f'<span style="color:#555;font-size:10pt;">No se generó árbol.</span>'
            f'</div>'
        )

    def show_footer(self):
        """Pie con conteo de nodos."""
        self.append(
            f'<div style="padding:8px 14px 4px;">'
            f'<span style="color:#222;font-size:7pt;">{"─" * 60}</span>'
            f'</div>'
        )
        self.append(
            f'<div style="padding:2px 14px 12px;">'
            f'<span style="color:#2a2a2a;font-size:8pt;">'
            f'  {self._node_count} nodo(s)</span>'
            f'</div>'
        )
        self.verticalScrollBar().setValue(0)

    # ── Menú contextual ──────────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_CSS)
        has_sel = self.textCursor().hasSelection()

        def _a(label, slot, enabled=True):
            a = QAction(label, self)
            a.triggered.connect(slot)
            a.setEnabled(enabled)
            menu.addAction(a)

        _a("Copiar selección",  self.copy,     has_sel)
        _a("Seleccionar todo",  self.selectAll)
        menu.addSeparator()
        _a("Limpiar",           self.clear)
        _a("Guardar árbol…",    self._save_output)
        menu.addSeparator()
        _a("Scroll al inicio",  lambda: self.verticalScrollBar().setValue(0))

        menu.exec(event.globalPos())

    def _save_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar árbol sintáctico", "arbol_sintactico.txt",
            "Texto (*.txt);;Todos los archivos (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.toPlainText())
