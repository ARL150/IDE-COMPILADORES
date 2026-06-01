# ui/console.py
# Consola integrada con mensajes diferenciados por tipo.

from datetime import datetime
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class CompilerConsole(QTextEdit):
    """
    Consola visual tipo IDE con mensajes coloreados.

    Uso:
        console.info("Análisis léxico iniciado...")
        console.ok("57 tokens generados.")
        console.warning("Se encontraron errores léxicos.")
        console.error("Se esperaba ';' — línea 4, col 10.")
        console.separator()
    """

    # Colores por tipo (se ven bien en fondo oscuro y fondo negro)
    _COLORS = {
        "info":    "#64b5f6",   # azul suave
        "ok":      "#81c784",   # verde
        "warning": "#ffb74d",   # naranja
        "error":   "#e57373",   # rojo suave
        "step":    "#ce93d8",   # morado
        "dim":     "#4a4a4a",   # gris muy oscuro (separadores)
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompilerConsole")
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.document().setDefaultStyleSheet(
            "span { font-family: Consolas, 'Courier New', monospace; }"
        )

    # ─────────────────────────────────────────────────────────────
    # Helpers internos
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _ts() -> str:
        """Timestamp actual."""
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _esc(text: str) -> str:
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

    def _append(self, ts_color: str, ts: str,
                badge_color: str, badge: str,
                msg_color: str, msg: str):
        html = (
            f'<span style="color:{ts_color};font-size:9pt;">{ts}&nbsp;</span>'
            f'<span style="color:{badge_color};font-weight:bold;">{badge}&nbsp;</span>'
            f'<span style="color:{msg_color};">{self._esc(msg)}</span>'
        )
        self.append(html)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ─────────────────────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────────────────────

    def info(self, message: str):
        self._append("#3a3a3a", self._ts(),
                     self._COLORS["info"],  "[INFO] ",
                     "#9d9d9d", message)

    def ok(self, message: str):
        self._append("#3a3a3a", self._ts(),
                     self._COLORS["ok"],    "[OK]   ",
                     "#cccccc", message)

    def warning(self, message: str):
        self._append("#3a3a3a", self._ts(),
                     self._COLORS["warning"], "[WARN] ",
                     "#cccccc", message)

    def error(self, message: str):
        self._append("#3a3a3a", self._ts(),
                     self._COLORS["error"],  "[ERROR]",
                     self._COLORS["error"], message)

    def step(self, num: int, message: str):
        badge = f"[{num}]    "
        self._append("#3a3a3a", self._ts(),
                     self._COLORS["step"], badge,
                     "#cccccc", message)

    def separator(self, label: str = ""):
        line = "─" * 50
        if label:
            pad = (50 - len(label) - 2) // 2
            line = "─" * pad + f" {label} " + "─" * pad
        self.append(
            f'<span style="color:{self._COLORS["dim"]};">{line}</span>'
        )
        self._scroll_to_bottom()

    def clear_log(self):
        self.clear()

    def welcome(self):
        """Mensaje de bienvenida inicial."""
        self.separator("IDE COMPILADOR")
        self.info("Bienvenido al IDE de Compiladores")
        self.info("Gramática: descendente recursiva — Fase 2")
        self.info("Carga un archivo o escribe código y presiona Léxico o Sintáctico.")
        self.separator()
