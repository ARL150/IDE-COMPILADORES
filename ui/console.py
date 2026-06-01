import re
import sys
from datetime import datetime
from PyQt6.QtWidgets import QTextEdit, QMenu, QFileDialog
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtCore import Qt

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
        self.clear()
        self.append(
            f'<div style="margin:16px 8px;">'
            f'<span style="color:#22c55e;font-size:11pt;font-weight:600;">✔</span>'
            f'&nbsp;&nbsp;'
            f'<span style="color:#81c784;font-size:10pt;">{self._esc(msg)}</span>'
            f'</div>'
        )

    def show_lex_errors(self, lex_errors):
        self.clear()
        if not lex_errors:
            self.show_ok("Sin errores léxicos"); return
        self.append(
            f'<div style="padding:8px 12px 10px;">'
            f'<span style="color:{self._accent};font-size:8.5pt;font-weight:700;'
            f'letter-spacing:1.5px;">── {self._label} &nbsp; {len(lex_errors)} error(es) ──</span>'
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
            self.show_ok("Sin errores sintácticos"); return
        self.append(
            f'<div style="padding:8px 12px 10px;">'
            f'<span style="color:{self._accent};font-size:8.5pt;font-weight:700;'
            f'letter-spacing:1.5px;">── {self._label} &nbsp; {len(syn_errors)} error(es) ──</span>'
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
