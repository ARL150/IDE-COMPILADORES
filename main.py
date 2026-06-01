"""
IDE Compilador — Análisis Léxico & Sintáctico
Punto de entrada principal.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from ui.themes import ThemeManager


def main():
    # Habilitar escalado HiDPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("IDE Compilador")
    app.setOrganizationName("IDECompilador")

    # Aplicar tema por defecto antes de crear la ventana
    ThemeManager.apply("dark_pro", app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
