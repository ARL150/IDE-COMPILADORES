# ui/splash.py — Splash screen animado al iniciar el IDE
from PyQt6.QtWidgets import QSplashScreen, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient


class SplashScreen(QWidget):
    finished = pyqtSignal()

    _STEPS = [
        (15,  "Cargando módulos..."),
        (35,  "Iniciando lexer..."),
        (55,  "Cargando parser..."),
        (75,  "Inicializando analizador semántico..."),
        (90,  "Construyendo interfaz..."),
        (100, "¡Listo!"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 280)

        # Centra en pantalla
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2
        )

        self._build_ui()
        self._step = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(260)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Contenedor con fondo
        self._card = QWidget(self)
        self._card.setFixedSize(480, 280)
        self._card.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1a1b26, stop:0.5 #1e1e2e, stop:1 #0f172a);
                border-radius: 18px;
                border: 1px solid #313244;
            }
        """)

        cl = QVBoxLayout(self._card)
        cl.setContentsMargins(40, 36, 40, 32)
        cl.setSpacing(0)

        # Icono / logo
        logo = QLabel("⟨/⟩")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            "font-size: 46px; color: #89b4fa; font-weight: 900;"
            "font-family: 'Menlo','SF Mono','Consolas',monospace;"
            "background: transparent; border: none;"
        )
        cl.addWidget(logo)

        cl.addSpacing(8)

        # Nombre del IDE
        title = QLabel("IDE Compiladores")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 22pt; font-weight: 700; color: #cdd6f4;"
            "font-family: 'SF Pro Display','Segoe UI',Arial,sans-serif;"
            "background: transparent; border: none;"
        )
        cl.addWidget(title)

        # Subtítulo
        sub = QLabel("Análisis Léxico · Sintáctico · Semántico")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            "font-size: 10pt; color: #6c7086;"
            "font-family: 'SF Pro Text','Segoe UI',Arial,sans-serif;"
            "background: transparent; border: none; margin-top: 4px;"
        )
        cl.addWidget(sub)

        cl.addSpacing(24)

        # Barra de progreso
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)
        self._bar.setStyleSheet("""
            QProgressBar {
                background: #313244;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #89b4fa, stop:1 #a6e3a1);
                border-radius: 2px;
            }
        """)
        cl.addWidget(self._bar)

        cl.addSpacing(10)

        # Texto de estado
        self._status = QLabel("Iniciando...")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet(
            "font-size: 8.5pt; color: #45475a;"
            "font-family: 'SF Mono','Menlo',monospace;"
            "background: transparent; border: none;"
        )
        cl.addWidget(self._status)

        cl.addStretch()

        # Versión abajo derecha
        ver = QLabel("v3.0  —  Fase 3")
        ver.setAlignment(Qt.AlignmentFlag.AlignRight)
        ver.setStyleSheet(
            "font-size: 7.5pt; color: #313244;"
            "background: transparent; border: none;"
        )
        cl.addWidget(ver)

    def _advance(self):
        if self._step >= len(self._STEPS):
            self._timer.stop()
            QTimer.singleShot(200, self.finished.emit)
            QTimer.singleShot(200, self.close)
            return
        val, msg = self._STEPS[self._step]
        self._bar.setValue(val)
        self._status.setText(msg)
        self._step += 1
