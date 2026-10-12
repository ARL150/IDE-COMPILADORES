# ui/welcome.py — Panel de bienvenida inicial del IDE
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal


class WelcomeWidget(QWidget):
    """Pantalla de bienvenida que se muestra en el primer tab del editor."""

    open_file   = pyqtSignal()
    new_file    = pyqtSignal()
    run_example = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomeWidget")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget()
        card.setFixedWidth(540)
        card.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Logo
        logo = QLabel("⟨/⟩")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            "font-size: 52px; font-weight: 900; color: #89b4fa;"
            "font-family: 'Menlo','SF Mono','Consolas',monospace;"
            "background: transparent;"
        )
        cl.addWidget(logo)
        cl.addSpacing(12)

        # Título
        title = QLabel("IDE Compiladores")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 26pt; font-weight: 700; color: #cdd6f4;"
            "font-family: 'SF Pro Display','Segoe UI',Arial,sans-serif;"
            "background: transparent;"
        )
        cl.addWidget(title)

        sub = QLabel("Análisis Léxico · Sintáctico · Semántico")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            "font-size: 11pt; color: #6c7086; margin-top: 4px;"
            "background: transparent;"
        )
        cl.addWidget(sub)

        cl.addSpacing(36)

        # Botones de acción
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_new = self._make_btn("＋  Nuevo archivo", primary=True)
        btn_new.clicked.connect(self.new_file)
        btn_row.addWidget(btn_new)

        btn_open = self._make_btn("📂  Abrir archivo")
        btn_open.clicked.connect(self.open_file)
        btn_row.addWidget(btn_open)

        btn_ex = self._make_btn("▶  Prueba maestra")
        btn_ex.clicked.connect(self.run_example)
        btn_row.addWidget(btn_ex)

        cl.addLayout(btn_row)
        cl.addSpacing(40)

        # Atajos rápidos
        shortcuts = [
            ("F5", "Análisis léxico"),
            ("F6", "Análisis sintáctico"),
            ("F7", "Compilar todo"),
            ("Ctrl+Shift+P", "Paleta de comandos"),
        ]
        sh_row = QHBoxLayout()
        sh_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sh_row.setSpacing(20)
        for key, desc in shortcuts:
            w = QWidget()
            wl = QVBoxLayout(w)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setSpacing(4)
            k = QLabel(key)
            k.setAlignment(Qt.AlignmentFlag.AlignCenter)
            k.setStyleSheet(
                "background: #313244; color: #89b4fa; border-radius: 6px;"
                "font-family: 'Menlo','Consolas',monospace; font-size: 9pt;"
                "font-weight: 700; padding: 4px 10px;"
            )
            d = QLabel(desc)
            d.setAlignment(Qt.AlignmentFlag.AlignCenter)
            d.setStyleSheet("color: #585b70; font-size: 8pt; background: transparent;")
            wl.addWidget(k)
            wl.addWidget(d)
            sh_row.addWidget(w)

        cl.addLayout(sh_row)
        cl.addSpacing(32)

        # Versión
        ver = QLabel("v3.0  ·  Fase 3: Análisis Semántico")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: #313244; font-size: 8pt; background: transparent;")
        cl.addWidget(ver)

        root.addWidget(card)

    def _make_btn(self, text: str, primary: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(38)
        btn.setMinimumWidth(148)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            btn.setStyleSheet("""
                QPushButton {
                    background: #89b4fa; color: #1e1e2e;
                    border: none; border-radius: 8px;
                    font-size: 10pt; font-weight: 700; padding: 0 18px;
                }
                QPushButton:hover  { background: #74c7ec; }
                QPushButton:pressed { background: #6c9cf5; }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background: #313244; color: #cdd6f4;
                    border: none; border-radius: 8px;
                    font-size: 10pt; padding: 0 18px;
                }
                QPushButton:hover  { background: #45475a; }
                QPushButton:pressed { background: #585b70; }
            """)
        return btn
