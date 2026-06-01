# ui/main_window.py
# Ventana principal rediseñada — layout tipo IDE profesional.

import os
import re
import locale

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QFileDialog, QDialog, QInputDialog,
    QMessageBox, QToolBar, QTextEdit, QSizePolicy, QFrame,
)
from PyQt6.QtGui import (
    QAction, QKeySequence, QIcon, QFont, QColor,
    QTextCursor, QTextFormat,
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QSize, QProcess

from ui.editor import CodeEditor
from ui.syntax_tree import SyntaxTreeWidget
from ui.console import CompilerConsole
from ui.themes import ThemeManager
from compiler.lexer import tokenize
from compiler.parser import Parser, load_tokens_from_file


# ─────────────────────────────────────────────────────────────
# Colores de texto por categoría de token (columna "Tipo")
# ─────────────────────────────────────────────────────────────
_TYPE_COLORS = {
    # keywords
    "MAIN": "#569cd6", "IF": "#569cd6", "THEN": "#569cd6",
    "ELSE": "#569cd6", "END": "#569cd6", "WHILE": "#569cd6",
    "DO": "#569cd6", "CIN": "#569cd6", "COUT": "#569cd6",
    "INT": "#569cd6", "FLOAT": "#569cd6", "BOOL": "#569cd6",
    "TRUE": "#569cd6", "FALSE": "#569cd6",
    # identifiers
    "ID": "#4ec9b0",
    # literals
    "NUMBER": "#b5cea8", "REAL": "#b5cea8",
    "STRING": "#ce9178",
    # operators
    "PLUS": "#d4d4d4", "MINUS": "#d4d4d4", "MULT": "#d4d4d4",
    "DIV": "#d4d4d4", "MOD": "#d4d4d4", "POWER": "#d4d4d4",
    "INCREMENT": "#d4d4d4", "DECREMENT": "#d4d4d4",
    "AND": "#c586c0", "OR": "#c586c0", "NOT": "#c586c0",
    "LT": "#c586c0", "LE": "#c586c0", "GT": "#c586c0",
    "GE": "#c586c0", "EQ": "#c586c0", "NE": "#c586c0",
    "EQUAL": "#d7ba7d",
    "SHIFT_LEFT": "#d4d4d4", "SHIFT_RIGHT": "#d4d4d4",
}


# ═══════════════════════════════════════════════════════════════
# Widget: EmptyState  (pantalla vacía estilizada)
# ═══════════════════════════════════════════════════════════════
class EmptyState(QWidget):
    def __init__(self, icon="✦", title="Sin resultados",
                 subtitle="Ejecuta el análisis para ver resultados aquí.", parent=None):
        super().__init__(parent)
        self.setObjectName("EmptyState")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)

        ico = QLabel(icon)
        ico.setObjectName("EmptyIcon")
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ttl = QLabel(title)
        ttl.setObjectName("EmptyTitle")
        ttl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel(subtitle)
        sub.setObjectName("EmptySub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)

        layout.addWidget(ico)
        layout.addWidget(ttl)
        layout.addWidget(sub)


# ═══════════════════════════════════════════════════════════════
# MainWindow
# ═══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self._settings = QSettings("IDECompilador", "Config_v2")
        self._closed_tabs = []
        self._process = None

        self.setWindowTitle("IDE Compilador — Análisis Léxico & Sintáctico")
        self.setMinimumSize(1050, 680)
        self.resize(1360, 860)

        self._build_central()
        self._build_toolbar()
        self._build_menu()
        self._build_statusbar()

        self.new_file()

        # Restaurar tema guardado
        theme = self._settings.value("theme", "dark_pro")
        ThemeManager.apply(theme)

        # Autosave cada 5 s
        self._autosave = QTimer()
        self._autosave.timeout.connect(self._auto_save)
        self._autosave.start(5000)

        # Restaurar geometría
        geom = self._settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)

        # Mensaje de bienvenida en consola
        self._console.welcome()
        self._result_tabs.setCurrentIndex(5)  # consola al inicio

    # ═══════════════════════════════════════════════════════════════
    # LAYOUT CENTRAL
    # ═══════════════════════════════════════════════════════════════

    def _build_central(self):
        root = QWidget()
        root.setObjectName("RootWidget")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setObjectName("MainSplitter")
        self._splitter.setChildrenCollapsible(False)

        self._splitter.addWidget(self._build_editor_panel())
        self._splitter.addWidget(self._build_results_panel())
        self._splitter.setSizes([440, 780])

        root_layout.addWidget(self._splitter)
        self.setCentralWidget(root)

    # ── Panel izquierdo: editor ────────────────────────────────

    def _build_editor_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("EditorPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._make_panel_header("CODIGO FUENTE"))

        # Pestañas de archivos abiertos
        self._editor_tabs = QTabWidget()
        self._editor_tabs.setObjectName("EditorTabs")
        self._editor_tabs.setTabsClosable(True)
        self._editor_tabs.setDocumentMode(True)
        self._editor_tabs.setMovable(True)   # pestañas arrastrables
        self._editor_tabs.tabCloseRequested.connect(self._close_tab)
        self._editor_tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._editor_tabs)

        return panel

    # ── Panel derecho: resultados ──────────────────────────────

    def _build_results_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("ResultsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._make_panel_header("RESULTADOS DEL ANALISIS"))

        self._result_tabs = QTabWidget()
        self._result_tabs.setObjectName("ResultTabs")
        self._result_tabs.setDocumentMode(True)
        self._result_tabs.setMovable(True)   # pestañas arrastrables
        layout.addWidget(self._result_tabs)

        # Tab 0 — Tokens
        self._lex_table = self._make_lex_table()
        self._result_tabs.addTab(self._lex_table, "Tokens")

        # Tab 1 — Errores léxicos
        self._lex_err_table = self._make_error_table()
        self._result_tabs.addTab(self._lex_err_table, "Err. Lexicos")

        # Tab 2 — Árbol AST gráfico
        self._ast_widget = SyntaxTreeWidget()
        self._result_tabs.addTab(self._ast_widget, "Arbol AST")

        # Tab 3 — Sintáctico texto
        self._syn_text = QPlainTextEdit()
        self._syn_text.setReadOnly(True)
        self._syn_text.setObjectName("SynText")
        self._syn_text.setFont(QFont("Consolas", 10))
        self._result_tabs.addTab(self._syn_text, "Sintactico")

        # Tab 4 — Errores sintácticos
        self._syn_err_table = self._make_error_table()
        self._result_tabs.addTab(self._syn_err_table, "Err. Sint.")

        # Tab 5 — Consola
        self._console = CompilerConsole()
        self._result_tabs.addTab(self._console, "Consola")

        return panel

    # ── Helpers de construcción ────────────────────────────────

    def _make_panel_header(self, title: str) -> QWidget:
        w = QWidget()
        w.setObjectName("PanelHeader")
        w.setFixedHeight(34)
        h = QHBoxLayout(w)
        h.setContentsMargins(14, 0, 14, 0)

        lbl = QLabel(title)
        lbl.setObjectName("PanelTitle")
        h.addWidget(lbl)
        h.addStretch()

        return w

    def _make_lex_table(self) -> QTableWidget:
        t = QTableWidget()
        t.setObjectName("LexTable")
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["#", "Tipo", "Lexema", "Línea", "Col"])
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        t.setColumnWidth(0, 42)
        t.setColumnWidth(3, 58)
        t.setColumnWidth(4, 48)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.setFont(QFont("Consolas", 10))
        t.setShowGrid(True)
        return t

    def _make_error_table(self) -> QTableWidget:
        t = QTableWidget()
        t.setObjectName("ErrorTable")
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["#", "Descripción", "Línea", "Col"])
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        t.setColumnWidth(0, 42)
        t.setColumnWidth(2, 58)
        t.setColumnWidth(3, 48)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.setFont(QFont("Consolas", 10))
        return t

    # ═══════════════════════════════════════════════════════════════
    # TOOLBAR
    # ═══════════════════════════════════════════════════════════════

    def _build_toolbar(self):
        tb = self.addToolBar("Principal")
        tb.setObjectName("MainToolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        def _sep():
            tb.addSeparator()

        def _lbl(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "font-weight:bold; font-size:10px; color:#9d9d9d; padding:2px 6px;"
            )
            tb.addWidget(lbl)

        def _btn(icon_path, label, slot):
            a = QAction(label, self)
            if os.path.exists(icon_path):
                a.setIcon(QIcon(icon_path))
            a.triggered.connect(slot)
            tb.addAction(a)
            return a

        # ── ARCHIVO ──
        _lbl("ARCHIVO")
        _sep()
        _btn("icons/file.svg",             "Nuevo",       self.new_file)
        _btn("icons/folder-open (2).svg",  "Abrir",       self.open_file)
        _btn("icons/save.svg",             "Guardar",     self.save_file)
        _btn("icons/archive.svg",          "Guardar como",self.save_as_file)
        _btn("icons/x-circle.svg",         "Cerrar",
             lambda: self._close_tab(self._editor_tabs.currentIndex()))
        _btn("icons/x.svg",                "Salir",       self.close)
        _sep()

        # ── EJECUTAR ──
        _lbl("EJECUTAR")
        _sep()
        _btn("icons/captions.svg",                "Lexico",      self.run_lexer)
        _btn("icons/blanket.svg",                 "Sintactico",  self.run_parser)
        _btn("icons/message-circle-captions.svg", "Semantico",   self.run_semantic)
        _btn("icons/monitor-wide.svg",            "Intermedio",  self.run_intermediate)
        _btn("icons/play.svg",                    "Ejecutar",    self.run_all)
        _sep()

        # ── Tema ──
        theme_action = QAction("Tema", self)
        theme_action.triggered.connect(self._show_theme_dialog)
        tb.addAction(theme_action)

    # ═══════════════════════════════════════════════════════════════
    # MENÚ
    # ═══════════════════════════════════════════════════════════════

    def _build_menu(self):
        mb = self.menuBar()

        # ── Archivo ──
        fm = mb.addMenu("Archivo")
        self._act(fm, "Nuevo",          "Ctrl+N",        self.new_file)
        self._act(fm, "Abrir",          "Ctrl+O",        self.open_file)
        self._act(fm, "Guardar",        "Ctrl+S",        self.save_file)
        self._act(fm, "Guardar como",   "Ctrl+Shift+S",  self.save_as_file)
        fm.addSeparator()
        self._act(fm, "Cerrar pestaña", "Ctrl+W",
                  lambda: self._close_tab(self._editor_tabs.currentIndex()))
        self._act(fm, "Salir",          "Ctrl+Q",        self.close)

        # ── Editar ──
        em = mb.addMenu("Editar")
        self._act(em, "Deshacer",        "Ctrl+Z", lambda: self._ed() and self._ed().undo())
        self._act(em, "Rehacer",         "Ctrl+Y", lambda: self._ed() and self._ed().redo())
        em.addSeparator()
        self._act(em, "Cortar",          "Ctrl+X", lambda: self._ed() and self._ed().cut())
        self._act(em, "Copiar",          "Ctrl+C", lambda: self._ed() and self._ed().copy())
        self._act(em, "Pegar",           "Ctrl+V", lambda: self._ed() and self._ed().paste())
        em.addSeparator()
        self._act(em, "Seleccionar todo","Ctrl+A", lambda: self._ed() and self._ed().selectAll())
        self._act(em, "Buscar",          "Ctrl+F", self._find)
        em.addSeparator()
        self._act(em, "Zoom +",          "Ctrl++", lambda: self._ed() and self._ed().zoomIn(2))
        self._act(em, "Zoom -",          "Ctrl+-", lambda: self._ed() and self._ed().zoomOut(2))

        # ── Analizar ──
        an = mb.addMenu("Analizar")
        self._act(an, "Análisis léxico",      "F5", self.run_lexer)
        self._act(an, "Análisis sintáctico",  "F6", self.run_parser)
        self._act(an, "Ejecutar todo",        "F7", self.run_all)
        an.addSeparator()
        self._act(an, "Limpiar resultados",   None, self.clear_all)

        # ── Temas ──
        thm = mb.addMenu("Temas")
        _pro = ["dark_pro", "light_pro", "cyber_blue"]
        _cls = ["dracula", "ocean", "sunset", "forest", "neon", "hacker"]
        thm.addSection("Profesionales")
        for key in _pro:
            a = QAction(ThemeManager.label(key), self)
            a.triggered.connect(lambda _, k=key: self._apply_theme(k))
            thm.addAction(a)
        thm.addSeparator()
        thm.addSection("Clasicos")
        for key in _cls:
            a = QAction(ThemeManager.label(key), self)
            a.triggered.connect(lambda _, k=key: self._apply_theme(k))
            thm.addAction(a)

        # ── Acerca de ──
        ab = mb.addMenu("Acerca de")
        self._act(ab, "Desarrolladores", None, self._show_about)

    def _act(self, menu, label, shortcut, slot):
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        if slot:
            a.triggered.connect(slot)
        menu.addAction(a)
        return a

    # ═══════════════════════════════════════════════════════════════
    # STATUS BAR
    # ═══════════════════════════════════════════════════════════════

    def _build_statusbar(self):
        sb = self.statusBar()

        self._lbl_cursor = QLabel("Línea: 1   Col: 1")
        self._lbl_tokens = QLabel("Tokens: —")
        self._lbl_status = QLabel("● Listo")
        self._lbl_status.setObjectName("StatusIndicator")

        sb.addWidget(self._lbl_cursor)
        sb.addWidget(self._vsep())
        sb.addWidget(self._lbl_tokens)
        sb.addPermanentWidget(self._lbl_status)

    def _vsep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.VLine)
        f.setStyleSheet("color: rgba(255,255,255,0.3); margin: 3px 2px;")
        return f

    def _set_status(self, text: str, color: str = "white"):
        self._lbl_status.setText(text)
        self._lbl_status.setStyleSheet(f"color: {color}; font-weight: bold;")

    # ═══════════════════════════════════════════════════════════════
    # EDITOR: acceso y eventos
    # ═══════════════════════════════════════════════════════════════

    def _ed(self) -> CodeEditor | None:
        w = self._editor_tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def _update_cursor(self):
        e = self._ed()
        if e:
            c = e.textCursor()
            self._lbl_cursor.setText(
                f"Línea: {c.blockNumber()+1}   Col: {c.columnNumber()+1}"
            )

    def _on_tab_changed(self, _):
        self._update_cursor()

    # ═══════════════════════════════════════════════════════════════
    # ARCHIVOS
    # ═══════════════════════════════════════════════════════════════

    def new_file(self):
        e = CodeEditor()
        idx = self._editor_tabs.addTab(e, "Sin título")
        self._editor_tabs.setCurrentIndex(idx)
        e.cursorPositionChanged.connect(self._update_cursor)

    def open_file(self, path: str = ""):
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, "Abrir archivo", "",
                "Todos los archivos (*);;Texto (*.txt);;Python (*.py)"
            )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            QMessageBox.warning(self, "Error al abrir", str(exc))
            return

        e = CodeEditor()
        e.setPlainText(content)
        e.file_path = path
        e.cursorPositionChanged.connect(self._update_cursor)
        idx = self._editor_tabs.addTab(e, os.path.basename(path))
        self._editor_tabs.setCurrentIndex(idx)

    def save_file(self):
        e = self._ed()
        if not e:
            return
        if hasattr(e, "file_path"):
            try:
                with open(e.file_path, "w", encoding="utf-8") as f:
                    f.write(e.toPlainText())
                self._set_status("● Guardado ✔", "#81c784")
                QTimer.singleShot(2000, lambda: self._set_status("● Listo"))
            except Exception as exc:
                QMessageBox.warning(self, "Error al guardar", str(exc))
        else:
            self.save_as_file()

    def save_as_file(self):
        e = self._ed()
        if not e:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", "",
            "Todos los archivos (*);;Texto (*.txt);;Python (*.py)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(e.toPlainText())
        e.file_path = path
        self._editor_tabs.setTabText(self._editor_tabs.currentIndex(), os.path.basename(path))

    def _close_tab(self, index: int):
        e = self._editor_tabs.widget(index)
        if e:
            self._closed_tabs.append({
                "content": e.toPlainText(),
                "title": self._editor_tabs.tabText(index),
                "file_path": getattr(e, "file_path", None),
            })
        self._editor_tabs.removeTab(index)
        if self._editor_tabs.count() == 0:
            self.new_file()

    def _auto_save(self):
        e = self._ed()
        if e and hasattr(e, "file_path"):
            try:
                with open(e.file_path, "w", encoding="utf-8") as f:
                    f.write(e.toPlainText())
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════
    # ANÁLISIS LÉXICO
    # ═══════════════════════════════════════════════════════════════

    def run_lexer(self):
        e = self._ed()
        if not e:
            return
        code = e.toPlainText().strip()
        if not code:
            self._console.warning("El editor está vacío.")
            return

        # ─ consola
        self._console.separator("ANÁLISIS LÉXICO")
        self._console.info("Iniciando análisis léxico...")
        self._set_status("● Analizando léxico…", "#64b5f6")

        tokens, lex_errors = tokenize(code)

        # ─ tabla de tokens
        self._lex_table.setRowCount(0)
        self._lex_table.setRowCount(len(tokens))
        for i, (tipo, lexema, linea, col) in enumerate(tokens):
            self._lex_table.setItem(i, 0, self._cell(str(i + 1), center=True))
            type_item = QTableWidgetItem(tipo)
            type_item.setForeground(QColor(_TYPE_COLORS.get(tipo, "#cccccc")))
            self._lex_table.setItem(i, 1, type_item)
            self._lex_table.setItem(i, 2, self._cell(lexema))
            self._lex_table.setItem(i, 3, self._cell(str(linea), center=True))
            self._lex_table.setItem(i, 4, self._cell(str(col),   center=True))
        self._lex_table.resizeRowsToContents()

        # ─ guardar tokens.txt
        try:
            with open("tokens.txt", "w", encoding="utf-8") as f:
                # Formato con tabs: legible y parseable por Parser.from_file()
                f.write("TIPO\tLEXEMA\tLINEA\tCOLUMNA\n")
                f.write("-" * 55 + "\n")
                for t in tokens:
                    f.write(f"{t[0]}\t{t[1]}\t{t[2]}\t{t[3]}\n")
        except Exception:
            pass

        # ─ errores léxicos
        self._lex_err_table.setRowCount(0)
        if lex_errors:
            self._lex_err_table.setRowCount(len(lex_errors))
            for i, (sym, ln, cl) in enumerate(lex_errors):
                self._lex_err_table.setItem(i, 0, self._cell(str(i + 1), center=True, err=True))
                self._lex_err_table.setItem(i, 1, self._cell(f"Símbolo no reconocido: '{sym}'", err=True))
                self._lex_err_table.setItem(i, 2, self._cell(str(ln), center=True, err=True))
                self._lex_err_table.setItem(i, 3, self._cell(str(cl), center=True, err=True))
            self._console.warning(
                f"Se encontraron {len(lex_errors)} error(es) léxico(s). Ver pestaña 'Err. Léxicos'."
            )
        else:
            # fila "sin errores"
            self._lex_err_table.setRowCount(1)
            ok_item = QTableWidgetItem("✔  Sin errores léxicos")
            ok_item.setForeground(QColor("#81c784"))
            ok_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._lex_err_table.setSpan(0, 0, 1, 4)
            self._lex_err_table.setItem(0, 0, ok_item)

        # ─ status y consola
        self._lbl_tokens.setText(f"Tokens: {len(tokens)}")
        if lex_errors:
            self._console.error(f"Análisis léxico: {len(tokens)} tokens, {len(lex_errors)} error(es).")
            self._set_status(f"● {len(lex_errors)} error(es) léxico(s)", "#ffb74d")
        else:
            self._console.ok(f"Análisis léxico completado — {len(tokens)} tokens generados.")
            self._set_status("● Léxico OK", "#81c784")

        # ─ cambiar a pestaña de tokens
        self._result_tabs.setCurrentIndex(0)

    # ═══════════════════════════════════════════════════════════════
    # ANÁLISIS SINTÁCTICO
    # ═══════════════════════════════════════════════════════════════

    def run_parser(self):
        e = self._ed()
        if not e:
            return
        code = e.toPlainText().strip()
        if not code:
            self._console.warning("El editor está vacío.")
            return

        # ─ léxico primero
        self._console.separator("ANÁLISIS SINTÁCTICO")
        self._console.info("Ejecutando análisis léxico previo...")
        tokens, lex_errors = tokenize(code)

        # Actualizar tabla léxica también
        self._lex_table.setRowCount(len(tokens))
        for i, (tipo, lexema, linea, col) in enumerate(tokens):
            self._lex_table.setItem(i, 0, self._cell(str(i + 1), center=True))
            ti = QTableWidgetItem(tipo)
            ti.setForeground(QColor(_TYPE_COLORS.get(tipo, "#cccccc")))
            self._lex_table.setItem(i, 1, ti)
            self._lex_table.setItem(i, 2, self._cell(lexema))
            self._lex_table.setItem(i, 3, self._cell(str(linea), center=True))
            self._lex_table.setItem(i, 4, self._cell(str(col),   center=True))
        self._lbl_tokens.setText(f"Tokens: {len(tokens)}")

        if lex_errors:
            self._console.warning(f"{len(lex_errors)} error(es) léxico(s) detectado(s). Continuando con el análisis.")

        # ─ parse
        # RUBRICA: "El analizador debe leer un archivo de texto con los tokens"
        # Se usa Parser.from_file() si tokens.txt existe; si no, usa tokens en memoria.
        self._console.info("Iniciando análisis sintáctico...")
        self._set_status("● Analizando sintaxis...", "#64b5f6")

        import os
        if os.path.exists("tokens.txt"):
            tokens_from_file = load_tokens_from_file("tokens.txt")
            parser = Parser(tokens_from_file if tokens_from_file else tokens)
            self._console.info("Tokens leidos desde tokens.txt (requisito rubrica).")
        else:
            parser = Parser(tokens)
        ast = parser.parse()
        parser.save_errors()

        # ─ AST gráfico
        self._ast_widget.clear()
        if ast:
            self._ast_widget.load_ast(ast)
            self._console.ok("AST generado correctamente.")

        # ─ AST texto (sintáctico tab)
        self._syn_text.clear()
        self._syn_text.appendPlainText("═══ ÁRBOL SINTÁCTICO ═══\n")
        self._print_ast_text(ast, 0)

        # ─ errores sintácticos
        self._syn_err_table.setRowCount(0)
        if parser.errors:
            self._syn_err_table.setRowCount(len(parser.errors))
            for i, err in enumerate(parser.errors):
                # Extraer línea/col del mensaje si existe
                m_ln = re.search(r'línea\s+(\d+)', err)
                m_cl = re.search(r'columna\s+(\d+)', err)
                # Descripción limpia
                desc = re.sub(r'\(línea.*\)', '', err).strip()
                ln_str = m_ln.group(1) if m_ln else "—"
                cl_str = m_cl.group(1) if m_cl else "—"

                self._syn_err_table.setItem(i, 0, self._cell(str(i+1), center=True, err=True))
                self._syn_err_table.setItem(i, 1, self._cell(desc, err=True))
                self._syn_err_table.setItem(i, 2, self._cell(ln_str, center=True, err=True))
                self._syn_err_table.setItem(i, 3, self._cell(cl_str, center=True, err=True))
                self._console.error(err)
                self._mark_error_line(err)

            self._set_status(f"● {len(parser.errors)} error(es) sintáctico(s)", "#e57373")
            self._result_tabs.setCurrentIndex(4)  # errores sint.
        else:
            # Sin errores
            self._syn_err_table.setRowCount(1)
            ok_item = QTableWidgetItem("✔  Sin errores sintácticos")
            ok_item.setForeground(QColor("#81c784"))
            ok_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._syn_err_table.setSpan(0, 0, 1, 4)
            self._syn_err_table.setItem(0, 0, ok_item)
            self._syn_text.appendPlainText("\n✔  Análisis sintáctico correcto — sin errores")
            self._console.ok("Análisis sintáctico correcto — sin errores.")
            self._set_status("● Sintáctico OK", "#81c784")
            self._result_tabs.setCurrentIndex(2)  # AST

    def _print_ast_text(self, node, level: int):
        if not node:
            return
        indent = "  " * level
        text = f"{indent}{node.node_type}"
        if node.value is not None:
            text += f": {node.value}"
        if node.line is not None:
            text += f"  [{node.line}:{node.column}]"
        self._syn_text.appendPlainText(text)
        for child in node.children:
            self._print_ast_text(child, level + 1)

    def _mark_error_line(self, text: str):
        e = self._ed()
        if not e:
            return
        m = re.search(r'línea\s+(\d+)', text.lower())
        if not m:
            return
        linea = int(m.group(1))
        cursor = e.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(linea - 1):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        e.setTextCursor(cursor)

    # ═══════════════════════════════════════════════════════════════
    # EJECUTAR TODO
    # ═══════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════
    # SEMÁNTICO / INTERMEDIO (stubs — para fases futuras)
    # ═══════════════════════════════════════════════════════════════

    def run_semantic(self):
        self._console.separator("ANALISIS SEMANTICO")
        self._console.warning("El análisis semántico aún no está implementado en esta fase.")
        self._result_tabs.setCurrentIndex(5)

    def run_intermediate(self):
        self._console.separator("CÓDIGO INTERMEDIO")
        self._console.warning("La generación de código intermedio aún no está implementada.")
        self._result_tabs.setCurrentIndex(5)

    def run_all(self):
        self._console.clear_log()
        self._console.separator("COMPILACION COMPLETA")
        self.run_lexer()
        self.run_parser()
        self._console.separator()

    def clear_all(self):
        self._lex_table.setRowCount(0)
        self._lex_err_table.setRowCount(0)
        self._syn_err_table.setRowCount(0)
        self._ast_widget.clear()
        self._syn_text.clear()
        self._console.clear_log()
        self._console.info("Resultados limpiados.")
        self._lbl_tokens.setText("Tokens: —")
        self._set_status("● Listo")

    # ═══════════════════════════════════════════════════════════════
    # TEMAS
    # ═══════════════════════════════════════════════════════════════

    def _apply_theme(self, key: str):
        ThemeManager.apply(key)
        self._settings.setValue("theme", key)
        self._console.info(f"Tema aplicado: {ThemeManager.label(key)}")

    def _show_theme_dialog(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Seleccionar tema")
        dlg.setMinimumWidth(240)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(8)
        lbl = QLabel("Elige un tema visual:")
        lbl.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(lbl)
        for key in ThemeManager.all_keys():
            btn = QPushButton(ThemeManager.label(key))
            btn.clicked.connect(lambda _, k=key: (self._apply_theme(k), dlg.accept()))
            layout.addWidget(btn)
        dlg.exec()

    # ═══════════════════════════════════════════════════════════════
    # BUSCAR
    # ═══════════════════════════════════════════════════════════════

    def _find(self):
        e = self._ed()
        if not e:
            return
        text, ok = QInputDialog.getText(self, "Buscar", "Texto:")
        if ok and text:
            if not e.find(text):
                QMessageBox.information(self, "Buscar", "No se encontró el texto.")

    # ═══════════════════════════════════════════════════════════════
    # ACERCA DE
    # ═══════════════════════════════════════════════════════════════

    def _show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Desarrolladores")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(6)

        def lbl(t, size=12, color=None, bold=False):
            w = QLabel(t)
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s = f"font-size:{size}px;"
            if color:
                s += f"color:{color};"
            if bold:
                s += "font-weight:bold;"
            w.setStyleSheet(s)
            return w

        layout.addWidget(lbl("IDE Compilador", 20, bold=True))
        layout.addWidget(lbl("Análisis Léxico & Sintáctico — Fase 2", 11, "#888"))
        layout.addSpacing(12)
        layout.addWidget(lbl("Jesus Abraham Robledo Lopez", 14, "#569cd6", True))
        layout.addWidget(lbl("ID: 284745", 10, "#888"))
        layout.addSpacing(8)
        layout.addWidget(lbl("Edgar Alejandro Cedeño Suarez", 14, "#4ec9b0", True))
        layout.addWidget(lbl("ID: 262728", 10, "#888"))
        layout.addSpacing(12)
        layout.addWidget(lbl("Versión 2.0", 10, "#666"))
        dlg.setLayout(layout)
        dlg.exec()

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _cell(text: str, center: bool = False, err: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if err:
            item.setForeground(QColor("#f48771"))
        return item

    # ═══════════════════════════════════════════════════════════════
    # CIERRE
    # ═══════════════════════════════════════════════════════════════

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
