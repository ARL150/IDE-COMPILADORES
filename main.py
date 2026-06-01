"""
IDE Compilador — Punto de entrada.
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPainterPath

from ui.main_window import MainWindow
from ui.themes import ThemeManager


def _make_app_icon() -> QIcon:
    """
    Icono minimalista >_ con esquinas redondeadas estilo macOS.
    Radio: 22.4% del tamaño (estándar Apple).
    """
    from PyQt6.QtGui import QPen
    icon = QIcon()

    for sz in (16, 32, 64, 128, 256):
        px = QPixmap(sz, sz)
        px.fill(Qt.GlobalColor.transparent)   # fondo transparente → bordes redondeados visibles

        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # ── Forma redondeada estilo macOS ──────────────────────
        radius  = sz * 0.2237           # radio oficial Apple
        shape   = QPainterPath()
        shape.addRoundedRect(QRectF(0, 0, sz, sz), radius, radius)

        # Fondo casi negro con leve gradiente
        from PyQt6.QtGui import QLinearGradient
        grad = QLinearGradient(0, 0, 0, sz)
        grad.setColorAt(0.0, QColor("#1a1a1a"))
        grad.setColorAt(1.0, QColor("#0a0a0a"))

        p.fillPath(shape, grad)

        # Borde interior sutil (profundidad)
        p.setPen(QPen(QColor("#2a2a2a"), max(1, sz * 0.012)))
        p.drawPath(shape)

        # ── Texto >_ ──────────────────────────────────────────
        p.setPen(QColor("#ffffff"))
        f = QFont("Menlo" if sys.platform == "darwin" else "Consolas")
        f.setPixelSize(max(7, int(sz * 0.34)))
        f.setBold(True)
        p.setFont(f)

        # Centrado visual (ligeramente arriba del centro geométrico)
        from PyQt6.QtCore import QRectF as RF
        p.drawText(
            RF(0, sz * 0.05, sz, sz * 0.9),
            Qt.AlignmentFlag.AlignCenter,
            ">_"
        )

        p.end()
        icon.addPixmap(px)

    return icon


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("IDE Compilador")
    app.setOrganizationName("IDECompilador")
    app.setApplicationDisplayName("IDE Compilador")

    app_icon = _make_app_icon()
    app.setWindowIcon(app_icon)

    # macOS: cambiar ícono del Dock si pyobjc está disponible
    if sys.platform == "darwin":
        try:
            import tempfile, os
            from AppKit import NSApplication, NSImage
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            app_icon.pixmap(256, 256).save(tmp.name, "PNG")
            ns_img = NSImage.alloc().initWithContentsOfFile_(tmp.name)
            if ns_img:
                NSApplication.sharedApplication().setApplicationIconImage_(ns_img)
            os.unlink(tmp.name)
        except Exception:
            pass

    ThemeManager.apply("dark_pro", app)

    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
