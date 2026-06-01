# ui/main_window.py
import os
import re
import sys

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QFileDialog, QDialog, QInputDialog,
    QMessageBox, QToolBar, QTextEdit, QSizePolicy, QFrame,
    QPushButton, QScrollArea, QGridLayout, QListWidget,
    QListWidgetItem, QLineEdit,
)
from PyQt6.QtGui import (
    QAction, QKeySequence, QIcon, QFont, QColor,
    QTextCursor, QTextFormat,
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QSize

from ui.editor import CodeEditor
from ui.syntax_tree import SyntaxTreeWidget
from ui.console import CompilerConsole, ErrorTerminal
from ui.themes import ThemeManager
from compiler.lexer import tokenize
from compiler.parser import Parser, load_tokens_from_file

_IN_VENV = sys.prefix != sys.base_prefix

_TYPE_COLORS = {
    "MAIN":"#569cd6","IF":"#569cd6","THEN":"#569cd6","ELSE":"#569cd6","END":"#569cd6",
    "WHILE":"#569cd6","DO":"#569cd6","CIN":"#569cd6","COUT":"#569cd6",
    "INT":"#569cd6","FLOAT":"#569cd6","BOOL":"#569cd6","TRUE":"#569cd6","FALSE":"#569cd6",
    "ID":"#4ec9b0","NUMBER":"#b5cea8","REAL":"#b5cea8","STRING":"#ce9178",
    "PLUS":"#d4d4d4","MINUS":"#d4d4d4","MULT":"#d4d4d4","DIV":"#d4d4d4",
    "MOD":"#d4d4d4","POWER":"#d4d4d4","INCREMENT":"#d4d4d4","DECREMENT":"#d4d4d4",
    "AND":"#c586c0","OR":"#c586c0","NOT":"#c586c0","LT":"#c586c0","LE":"#c586c0",
    "GT":"#c586c0","GE":"#c586c0","EQ":"#c586c0","NE":"#c586c0","EQUAL":"#d7ba7d",
    "SHIFT_LEFT":"#d4d4d4","SHIFT_RIGHT":"#d4d4d4",
}

# Extensiones de código soportadas
_CODE_EXTS = (
    "Todos los archivos (*);;Código (*.c *.cpp *.h *.java *.py *.js *.ts *.cs *.go *.rs *.txt)"
    ";;C/C++ (*.c *.cpp *.h *.hpp)"
    ";;Python (*.py)"
    ";;Java (*.java)"
    ";;JavaScript/TS (*.js *.ts)"
    ";;Texto (*.txt)"
)
_SAVE_EXTS = (
    "Todos los archivos (*);;Texto (*.txt);;C (*.c);;C++ (*.cpp)"
    ";;Python (*.py);;Java (*.java);;JavaScript (*.js)"
    ";;TypeScript (*.ts);;C# (*.cs);;Go (*.go);;HTML (*.html)"
)


# ═══════════════════════════════════════════════════════════════
# FileBreadcrumb
# ═══════════════════════════════════════════════════════════════
class FileBreadcrumb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FileBreadcrumb")
        self.setFixedHeight(30)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(4)

        self._dir  = QLabel(""); self._dir.setObjectName("BreadcrumbDir")
        self._sep  = QLabel("›"); self._sep.setObjectName("BreadcrumbSep"); self._sep.setVisible(False)
        self._file = QLabel("Sin título"); self._file.setObjectName("BreadcrumbFile")
        self._badge= QLabel(""); self._badge.setObjectName("BreadcrumbBadge"); self._badge.setVisible(False)

        layout.addWidget(self._dir)
        layout.addWidget(self._sep)
        layout.addWidget(self._file)
        layout.addStretch()
        layout.addWidget(self._badge)

    def update_path(self, file_path):
        if not file_path:
            self._dir.setText(""); self._sep.setVisible(False)
            self._file.setText("Sin título"); self._badge.setVisible(False)
            return
        folder = os.path.basename(os.path.dirname(os.path.abspath(file_path)))
        name   = os.path.basename(file_path)
        ext    = os.path.splitext(name)[1].lower()
        self._dir.setText(folder); self._sep.setVisible(True); self._file.setText(name)
        if ext == ".py":
            self._badge.setText("🐍 Python (venv)" if _IN_VENV else "🐍 Python")
            self._badge.setVisible(True)
        else:
            self._badge.setVisible(False)


# ═══════════════════════════════════════════════════════════════
# CommandPalette — paleta de comandos estilo VS Code (Ctrl+Shift+P)
# ═══════════════════════════════════════════════════════════════
class CommandPalette(QDialog):
    """
    Paleta de comandos flotante.
    Muestra todos los comandos disponibles con búsqueda en tiempo real.
    """

    def __init__(self, commands: list[tuple[str, str, callable]], parent=None):
        """
        commands: [(label, shortcut, callback), ...]
        """
        super().__init__(parent)
        self._commands = commands
        self._filtered = list(commands)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(580)
        self.setMaximumWidth(660)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._container = QWidget()
        self._container.setObjectName("PaletteContainer")
        self._container.setStyleSheet("""
            QWidget#PaletteContainer {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 12px;
            }
        """)
        cl = QVBoxLayout(self._container)
        cl.setContentsMargins(0, 0, 0, 8)
        cl.setSpacing(0)

        # ── Fila superior: búsqueda + botón cerrar ──
        top_row = QWidget()
        top_row.setStyleSheet("background:transparent;")
        tr = QHBoxLayout(top_row)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(0)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar comando…  (Esc para cerrar)")
        self._search.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: #d4d4d4;
                border: none;
                border-bottom: 1px solid #2d2d2d;
                padding: 14px 0 14px 20px;
                font-size: 13pt;
                font-family: 'SF Pro Text', 'Segoe UI', Arial, sans-serif;
            }
        """)
        self._search.textChanged.connect(self._filter)
        tr.addWidget(self._search, 1)

        # Botón ×
        close_btn = QPushButton("×")
        close_btn.setFixedSize(50, 50)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #555;
                border: none;
                font-size: 18pt;
                font-weight: 300;
                padding-bottom: 2px;
            }
            QPushButton:hover { color: #fff; }
        """)
        close_btn.clicked.connect(self.reject)
        tr.addWidget(close_btn)

        cl.addWidget(top_row)

        # Lista de resultados
        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 4px 0;
            }
            QListWidget::item {
                padding: 9px 20px;
                color: #c0c0c0;
                font-size: 10pt;
                font-family: 'SF Pro Text', 'Segoe UI', Arial, sans-serif;
            }
            QListWidget::item:selected {
                background: #094771;
                color: #ffffff;
            }
            QListWidget::item:hover:!selected {
                background: #252525;
            }
        """)
        self._list.setMaximumHeight(360)
        self._list.itemActivated.connect(self._execute)
        cl.addWidget(self._list)

        # Pie: hint de teclas
        hint = QLabel("↑↓ navegar   ↵ ejecutar   Esc cerrar")
        hint.setStyleSheet(
            "color:#3a3a3a;font-size:8pt;padding:6px 20px 2px;"
            "background:transparent;"
        )
        cl.addWidget(hint)

        outer.addWidget(self._container)
        self._populate(commands)
        self._search.installEventFilter(self)

    def _populate(self, cmds):
        self._list.clear()
        for label, shortcut, _ in cmds:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, label)
            display = f"  {label}"
            if shortcut:
                display = f"{display}   \t{shortcut}"
            item.setText(display)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _filter(self, text: str):
        q = text.lower()
        self._filtered = [
            c for c in self._commands
            if q in c[0].lower()
        ] if q else list(self._commands)
        self._populate(self._filtered)

    def _execute(self, item):
        label = item.data(Qt.ItemDataRole.UserRole)
        for lbl, _, cb in self._filtered:
            if lbl == label:
                self.accept()
                cb()
                return
        self.reject()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        if obj is self._search and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                row = min(self._list.currentRow() + 1, self._list.count() - 1)
                self._list.setCurrentRow(row)
                return True
            if key == Qt.Key.Key_Up:
                row = max(self._list.currentRow() - 1, 0)
                self._list.setCurrentRow(row)
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = self._list.currentItem()
                if item:
                    self._execute(item)
                return True
            if key == Qt.Key.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        """Cierra al hacer clic en el área transparente fuera del contenedor."""
        if not self._container.geometry().contains(event.pos()):
            self.reject()
        else:
            super().mousePressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            pg = self.parent().geometry()
            x  = pg.x() + (pg.width()  - self.width())  // 2
            y  = pg.y() + int(pg.height() * 0.15)
            self.move(x, y)
        self._search.setFocus()


# ═══════════════════════════════════════════════════════════════
# EmptyState
# ═══════════════════════════════════════════════════════════════
class EmptyState(QWidget):
    def __init__(self, icon="✦", title="Sin resultados",
                 subtitle="Ejecuta el análisis para ver resultados.", parent=None):
        super().__init__(parent)
        self.setObjectName("EmptyState")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        for text, obj in [(icon,"EmptyIcon"),(title,"EmptyTitle"),(subtitle,"EmptySub")]:
            lbl = QLabel(text); lbl.setObjectName(obj)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            layout.addWidget(lbl)


# ═══════════════════════════════════════════════════════════════
# MainWindow
# ═══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._settings    = QSettings("IDECompilador", "Config_v5")
        self._closed_tabs = []
        self._run_action  = None
        self._recent_files= self._settings.value("recent_files", []) or []

        self.setWindowTitle("IDE Compilador")
        self.setMinimumSize(1050, 680)
        self.resize(1420, 900)
        self.setAcceptDrops(True)   # drag & drop de archivos

        self._build_central()
        self._build_toolbar()
        self._build_menu()
        self._build_statusbar()

        self.new_file()

        theme = self._settings.value("theme", "dark_pro")
        ThemeManager.apply(theme)

        self._autosave = QTimer()
        self._autosave.timeout.connect(self._auto_save)
        self._autosave.start(5000)

        geom = self._settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)

        self._console.welcome()
        self._result_tabs.setCurrentIndex(5)

    # ═══════════════════════════════════════════════════════════
    # LAYOUT CENTRAL
    # ═══════════════════════════════════════════════════════════

    def _build_central(self):
        root = QWidget(); root.setObjectName("RootWidget")
        rl   = QVBoxLayout(root); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setObjectName("MainSplitter")
        self._splitter.setChildrenCollapsible(False)
        self._splitter.addWidget(self._build_editor_panel())
        self._splitter.addWidget(self._build_results_panel())
        self._splitter.setSizes([480, 840])

        rl.addWidget(self._splitter)
        self.setCentralWidget(root)

    def _build_editor_panel(self):
        panel  = QWidget(); panel.setObjectName("EditorPanel")
        layout = QVBoxLayout(panel); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        self._breadcrumb = FileBreadcrumb()
        layout.addWidget(self._breadcrumb)

        self._editor_tabs = QTabWidget()
        self._editor_tabs.setObjectName("EditorTabs")
        self._editor_tabs.setTabsClosable(True)
        self._editor_tabs.setDocumentMode(True)
        self._editor_tabs.setMovable(True)
        self._editor_tabs.tabCloseRequested.connect(self._close_tab)
        self._editor_tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._editor_tabs)
        return panel

    def _build_results_panel(self):
        panel  = QWidget(); panel.setObjectName("ResultsPanel")
        layout = QVBoxLayout(panel); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        layout.addWidget(self._make_panel_header("RESULTADOS"))

        self._result_tabs = QTabWidget()
        self._result_tabs.setObjectName("ResultTabs")
        self._result_tabs.setDocumentMode(True)
        self._result_tabs.setMovable(True)
        layout.addWidget(self._result_tabs)

        # Tab 0 — Tokens (tabla)
        self._lex_table = self._make_lex_table()
        self._result_tabs.addTab(self._lex_table, "Tokens")

        # Tab 1 — Errores léxicos (terminal rojo)
        self._lex_err_term = ErrorTerminal(accent="#f28b82", label="ERRORES LÉXICOS")
        self._result_tabs.addTab(self._lex_err_term, "Err. Léxicos")

        # Tab 2 — AST gráfico
        self._ast_widget = SyntaxTreeWidget()
        self._result_tabs.addTab(self._ast_widget, "Árbol AST")

        # Tab 3 — Sintáctico texto (terminal morado/azul)
        self._syn_text = QPlainTextEdit()
        self._syn_text.setReadOnly(True)
        self._syn_text.setObjectName("SynText")
        self._syn_text.setFont(QFont("Menlo" if sys.platform=="darwin" else "Consolas", 10))
        self._result_tabs.addTab(self._syn_text, "Sintáctico")

        # Tab 4 — Errores sintácticos (terminal naranja)
        self._syn_err_term = ErrorTerminal(accent="#ffb74d", label="ERRORES SINTÁCTICOS")
        self._result_tabs.addTab(self._syn_err_term, "Err. Sint.")

        # Tab 5 — Consola
        self._console = CompilerConsole()
        self._result_tabs.addTab(self._console, "Consola")

        return panel

    def _make_panel_header(self, title):
        w = QWidget(); w.setObjectName("PanelHeader"); w.setFixedHeight(30)
        h = QHBoxLayout(w); h.setContentsMargins(14,0,14,0)
        lbl = QLabel(title); lbl.setObjectName("PanelTitle")
        h.addWidget(lbl); h.addStretch()
        return w

    def _make_lex_table(self):
        t = QTableWidget(); t.setObjectName("LexTable")
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["#", "Tipo", "Lexema", "Ln", "Col"])
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        t.setColumnWidth(0,44); t.setColumnWidth(3,52); t.setColumnWidth(4,46)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.setFont(QFont("Menlo" if sys.platform=="darwin" else "Consolas", 10))
        t.setShowGrid(True)
        return t

    # ═══════════════════════════════════════════════════════════
    # TOOLBAR — sin labels de sección, solo iconos + texto
    # ═══════════════════════════════════════════════════════════

    def _build_toolbar(self):
        tb = self.addToolBar("Principal")
        tb.setObjectName("MainToolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        def _sep(): tb.addSeparator()

        def _btn(icon_path, label, slot, tip=""):
            a = QAction(label, self)
            if os.path.exists(icon_path):
                a.setIcon(QIcon(icon_path))
            if tip:
                a.setToolTip(tip)
            a.triggered.connect(slot)
            tb.addAction(a)
            return a

        _btn("icons/file.svg",            "Nuevo",       self.new_file,       "Ctrl+N")
        _btn("icons/folder-open (2).svg", "Abrir",       self.open_file,      "Ctrl+O")
        _btn("icons/save.svg",            "Guardar",     self.save_file,      "Ctrl+S")
        _btn("icons/archive.svg",         "Guardar como",self.save_as_file,   "Ctrl+Shift+S")
        _sep()
        _btn("icons/captions.svg",                "Léxico",     self.run_lexer,      "F5")
        _btn("icons/blanket.svg",                 "Sintáctico", self.run_parser,     "F6")
        _btn("icons/message-circle-captions.svg", "Semántico",  self.run_semantic)
        _btn("icons/monitor-wide.svg",            "Intermedio", self.run_intermediate)
        _sep()
        run_icon = "icons/run.svg"
        if not os.path.exists(run_icon):
            run_icon = "icons/play.svg"
        self._run_action = _btn(run_icon, "Ejecutar", self.run_all, "F7 — Compilar todo")
        _sep()
        _btn("icons/x-circle.svg", "Cerrar tab",
             lambda: self._close_tab(self._editor_tabs.currentIndex()))
        _sep()
        theme_a = QAction("Temas", self)
        theme_a.triggered.connect(self._show_theme_dialog)
        tb.addAction(theme_a)

    # ═══════════════════════════════════════════════════════════
    # MENÚ
    # ═══════════════════════════════════════════════════════════

    def _build_menu(self):
        mb = self.menuBar()

        # ── Archivo ──
        fm = mb.addMenu("Archivo")
        self._act(fm, "Nuevo",             "Ctrl+N",       self.new_file)
        self._act(fm, "Abrir…",            "Ctrl+O",       self.open_file)

        # Abrir recientes
        self._recent_menu = fm.addMenu("Abrir reciente")
        self._refresh_recent_menu()

        fm.addSeparator()
        self._act(fm, "Guardar",           "Ctrl+S",       self.save_file)
        self._act(fm, "Guardar como…",     "Ctrl+Shift+S", self.save_as_file)
        self._act(fm, "Exportar como…",    "Ctrl+E",       self.export_as)
        fm.addSeparator()
        self._act(fm, "Abrir PDF…",        None,           self.open_pdf)
        fm.addSeparator()
        self._act(fm, "Cerrar pestaña",       "Ctrl+W",
                  lambda: self._close_tab(self._editor_tabs.currentIndex()))
        self._act(fm, "Reabrir tab cerrado", "Ctrl+Shift+T", self._reopen_closed_tab)
        self._act(fm, "Salir",               "Ctrl+Q",       self.close)

        # ── Editar ──
        em = mb.addMenu("Editar")
        self._act(em,"Deshacer","Ctrl+Z",lambda:self._ed() and self._ed().undo())
        self._act(em,"Rehacer","Ctrl+Y",lambda:self._ed() and self._ed().redo())
        em.addSeparator()
        self._act(em,"Cortar","Ctrl+X",lambda:self._ed() and self._ed().cut())
        self._act(em,"Copiar","Ctrl+C",lambda:self._ed() and self._ed().copy())
        self._act(em,"Pegar","Ctrl+V",lambda:self._ed() and self._ed().paste())
        em.addSeparator()
        self._act(em,"Seleccionar todo","Ctrl+A",lambda:self._ed() and self._ed().selectAll())
        self._act(em,"Buscar","Ctrl+F",self._find)
        em.addSeparator()
        self._act(em,"Zoom +","Ctrl++",lambda:self._ed() and self._ed().zoomIn(2))
        self._act(em,"Zoom -","Ctrl+-",lambda:self._ed() and self._ed().zoomOut(2))

        # ── Analizar ──
        an = mb.addMenu("Analizar")
        self._act(an,"Análisis léxico","F5",self.run_lexer)
        self._act(an,"Análisis sintáctico","F6",self.run_parser)
        self._act(an,"Análisis semántico",None,self.run_semantic)
        self._act(an,"Código intermedio",None,self.run_intermediate)
        self._act(an,"Compilar todo","F7",self.run_all)
        an.addSeparator()
        self._act(an,"Limpiar resultados",None,self.clear_all)

        # ── Temas ──
        thm = mb.addMenu("Temas")
        _mod = ["dark_pro","pure_black","pure_white","light_pro",
                "cyber_blue","tokyo_night","catppuccin","monokai","nord"]
        _cls = ["dracula","ocean","sunset","forest","neon","hacker"]
        thm.addSection("Modernos")
        for k in _mod:
            a = QAction(ThemeManager.label(k), self)
            a.triggered.connect(lambda _, key=k: self._apply_theme(key))
            thm.addAction(a)
        thm.addSeparator()
        thm.addSection("Clásicos")
        for k in _cls:
            a = QAction(ThemeManager.label(k), self)
            a.triggered.connect(lambda _, key=k: self._apply_theme(key))
            thm.addAction(a)

        # ── Ver ──
        vm = mb.addMenu("Ver")
        self._act(vm, "Paleta de comandos",    "Ctrl+Shift+P", self._show_command_palette)
        self._act(vm, "Atajos de teclado",     "Ctrl+K Ctrl+S", self._show_shortcuts_dialog)
        vm.addSeparator()
        self._act(vm, "Ir a línea…",           "Ctrl+G",       self._goto_line)
        vm.addSeparator()
        self._act(vm, "Zoom +",                "Ctrl++",       lambda: self._ed() and self._ed().zoomIn(2))
        self._act(vm, "Zoom -",                "Ctrl+-",       lambda: self._ed() and self._ed().zoomOut(2))
        self._act(vm, "Zoom reset",            "Ctrl+0",       self._zoom_reset)

        # ── Acerca de ──
        ab = mb.addMenu("Acerca de")
        self._act(ab,"Desarrolladores",None,self._show_about)

    def _act(self, menu, label, shortcut, slot):
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        if slot:
            a.triggered.connect(slot)
        menu.addAction(a)
        return a

    # ═══════════════════════════════════════════════════════════
    # STATUS BAR
    # ═══════════════════════════════════════════════════════════

    def _build_statusbar(self):
        sb = self.statusBar()
        self._lbl_cursor  = QLabel("Ln: 1   Col: 1")
        self._lbl_tokens  = QLabel("Tokens: —")
        self._lbl_errors  = QLabel("")          # contador de errores
        self._lbl_status  = QLabel("● Listo")
        self._lbl_status.setObjectName("StatusIndicator")

        sb.addWidget(self._lbl_cursor)
        sb.addWidget(self._vsep())
        sb.addWidget(self._lbl_tokens)
        sb.addWidget(self._vsep())
        sb.addWidget(self._lbl_errors)

        # Hint de paleta de comandos
        hint = QLabel("Ctrl+Shift+P")
        hint.setStyleSheet(
            "color:rgba(255,255,255,0.45);font-size:8pt;"
            "padding:0 10px;letter-spacing:0.5px;"
        )
        hint.setCursor(Qt.CursorShape.PointingHandCursor)
        hint.mousePressEvent = lambda _: self._show_command_palette()
        sb.addWidget(hint)

        sb.addPermanentWidget(self._lbl_status)
        if _IN_VENV:
            vl = QLabel("🐍 venv"); vl.setObjectName("VenvLabel")
            sb.addPermanentWidget(self._vsep())
            sb.addPermanentWidget(vl)

    def _update_error_counter(self, lex_n: int = 0, syn_n: int = 0):
        total = lex_n + syn_n
        if total == 0:
            self._lbl_errors.setText("")
        else:
            parts = []
            if lex_n:
                parts.append(f"⚠ {lex_n} léx.")
            if syn_n:
                parts.append(f"✖ {syn_n} sint.")
            self._lbl_errors.setText("   ".join(parts))
            self._lbl_errors.setStyleSheet(
                "color:#f28b82;font-size:8.5pt;font-weight:600;"
            )

    def _vsep(self):
        f = QFrame(); f.setFrameShape(QFrame.Shape.VLine)
        f.setStyleSheet("color:rgba(255,255,255,0.2);margin:3px 2px;")
        return f

    def _set_status(self, text, color="white"):
        self._lbl_status.setText(text)
        self._lbl_status.setStyleSheet(f"color:{color};font-weight:bold;")

    # ═══════════════════════════════════════════════════════════
    # EDITOR helpers
    # ═══════════════════════════════════════════════════════════

    def _ed(self):
        w = self._editor_tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def _update_cursor(self):
        e = self._ed()
        if e:
            c = e.textCursor()
            self._lbl_cursor.setText(f"Ln: {c.blockNumber()+1}   Col: {c.columnNumber()+1}")

    def _on_tab_changed(self, _):
        self._update_cursor()
        self._update_breadcrumb()

    def _update_breadcrumb(self):
        e  = self._ed()
        fp = getattr(e, "file_path", None) if e else None
        self._breadcrumb.update_path(fp)

    def _set_tab_icon(self, index, file_path=""):
        ext = os.path.splitext(file_path)[1].lower() if file_path else ""
        icon_path = ("icons/python-venv.svg" if _IN_VENV else "icons/python.svg") \
                    if ext == ".py" else "icons/file.svg"
        if os.path.exists(icon_path):
            self._editor_tabs.setTabIcon(index, QIcon(icon_path))

    # ═══════════════════════════════════════════════════════════
    # ARCHIVOS
    # ═══════════════════════════════════════════════════════════

    def new_file(self):
        e = CodeEditor()
        idx = self._editor_tabs.addTab(e, "Sin título")
        self._editor_tabs.setCurrentIndex(idx)
        self._set_tab_icon(idx, "")
        e.cursorPositionChanged.connect(self._update_cursor)
        e.file_modified.connect(lambda: self._mark_tab_modified(e))

    def open_file(self, path=""):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", _CODE_EXTS)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as exc:
                QMessageBox.warning(self, "Error al abrir", str(exc)); return
        except Exception as exc:
            QMessageBox.warning(self, "Error al abrir", str(exc)); return

        e = CodeEditor(); e.setPlainText(content); e.file_path = path
        e.mark_saved()
        e.cursorPositionChanged.connect(self._update_cursor)
        e.file_modified.connect(lambda: self._mark_tab_modified(e))
        idx = self._editor_tabs.addTab(e, os.path.basename(path))
        self._editor_tabs.setCurrentIndex(idx)
        self._set_tab_icon(idx, path)
        self._add_recent(path)

    def save_file(self):
        e = self._ed()
        if not e: return
        if hasattr(e, "file_path") and e.file_path:
            try:
                with open(e.file_path, "w", encoding="utf-8") as f:
                    f.write(e.toPlainText())
                e.mark_saved()
                self._mark_tab_saved(self._editor_tabs.currentIndex())
                self._set_status("● Guardado ✔", "#81c784")
                QTimer.singleShot(2000, lambda: self._set_status("● Listo"))
            except Exception as exc:
                QMessageBox.warning(self, "Error al guardar", str(exc))
        else:
            self.save_as_file()

    def save_as_file(self):
        e = self._ed()
        if not e: return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", _SAVE_EXTS)
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            f.write(e.toPlainText())
        e.file_path = path
        idx = self._editor_tabs.currentIndex()
        self._editor_tabs.setTabText(idx, os.path.basename(path))
        self._set_tab_icon(idx, path)
        self._update_breadcrumb()
        self._add_recent(path)

    def export_as(self):
        """Exportar el contenido actual con un formato diferente."""
        e = self._ed()
        if not e: return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar como", "",
            "C++ (*.cpp);;C (*.c);;Java (*.java);;Python (*.py)"
            ";;JavaScript (*.js);;HTML (*.html);;Texto (*.txt)"
        )
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            f.write(e.toPlainText())
        self._console.ok(f"Exportado: {os.path.basename(path)}")
        self._set_status("● Exportado ✔", "#81c784")
        QTimer.singleShot(2000, lambda: self._set_status("● Listo"))

    def open_pdf(self):
        """Intenta abrir un PDF como texto plano."""
        path, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", "", "PDF (*.pdf)")
        if not path: return

        try:
            import fitz  # PyMuPDF
            doc  = fitz.open(path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
        except ImportError:
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            except ImportError:
                QMessageBox.information(
                    self, "PDF no disponible",
                    "Para abrir PDFs instala PyMuPDF:\n\n  pip install pymupdf\n\n"
                    "o pdfplumber:\n\n  pip install pdfplumber"
                )
                return
            except Exception as exc:
                QMessageBox.warning(self, "Error al abrir PDF", str(exc)); return
        except Exception as exc:
            QMessageBox.warning(self, "Error al abrir PDF", str(exc)); return

        e = CodeEditor(); e.setPlainText(text)
        name = os.path.basename(path)
        idx  = self._editor_tabs.addTab(e, name)
        self._editor_tabs.setCurrentIndex(idx)
        e.cursorPositionChanged.connect(self._update_cursor)
        self._console.ok(f"PDF cargado como texto: {name}")

    def _close_tab(self, index):
        e = self._editor_tabs.widget(index)
        if e:
            self._closed_tabs.append({
                "content":   e.toPlainText(),
                "title":     self._editor_tabs.tabText(index),
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

    # ── Archivos recientes ──────────────────────────────────────

    def _add_recent(self, path):
        if path in self._recent_files:
            self._recent_files.remove(path)
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:10]
        self._settings.setValue("recent_files", self._recent_files)
        self._refresh_recent_menu()

    def _refresh_recent_menu(self):
        self._recent_menu.clear()
        if not self._recent_files:
            a = QAction("(vacío)", self); a.setEnabled(False)
            self._recent_menu.addAction(a)
            return
        for fp in self._recent_files:
            a = QAction(os.path.basename(fp), self)
            a.setToolTip(fp)
            a.triggered.connect(lambda _, p=fp: self.open_file(p))
            self._recent_menu.addAction(a)
        self._recent_menu.addSeparator()
        clr = QAction("Limpiar recientes", self)
        clr.triggered.connect(self._clear_recent)
        self._recent_menu.addAction(clr)

    def _clear_recent(self):
        self._recent_files = []
        self._settings.setValue("recent_files", [])
        self._refresh_recent_menu()

    # ═══════════════════════════════════════════════════════════
    # ANÁLISIS LÉXICO
    # ═══════════════════════════════════════════════════════════

    def run_lexer(self):
        e = self._ed()
        if not e: return
        code = e.toPlainText().strip()
        if not code:
            self._console.warning("El editor está vacío."); return

        self._console.separator("ANÁLISIS LÉXICO")
        self._console.info("Iniciando análisis léxico...")
        self._set_status("● Analizando léxico…", "#64b5f6")

        tokens, lex_errors = tokenize(code)

        # Tabla de tokens
        self._lex_table.setRowCount(0)
        self._lex_table.setRowCount(len(tokens))
        for i, (tipo, lexema, linea, col) in enumerate(tokens):
            self._lex_table.setItem(i, 0, self._cell(str(i+1), center=True))
            ti = QTableWidgetItem(tipo)
            ti.setForeground(QColor(_TYPE_COLORS.get(tipo, "#cccccc")))
            self._lex_table.setItem(i, 1, ti)
            self._lex_table.setItem(i, 2, self._cell(lexema))
            self._lex_table.setItem(i, 3, self._cell(str(linea), center=True))
            self._lex_table.setItem(i, 4, self._cell(str(col),   center=True))
        self._lex_table.resizeRowsToContents()

        try:
            with open("tokens.txt", "w", encoding="utf-8") as f:
                f.write("TIPO\tLEXEMA\tLINEA\tCOLUMNA\n" + "-"*55 + "\n")
                for t in tokens:
                    f.write(f"{t[0]}\t{t[1]}\t{t[2]}\t{t[3]}\n")
        except Exception:
            pass

        # Terminal de errores léxicos
        self._lex_err_term.show_lex_errors(lex_errors)

        self._lbl_tokens.setText(f"Tokens: {len(tokens)}")
        self._update_error_counter(lex_n=len(lex_errors))
        if lex_errors:
            self._console.warning(f"{len(lex_errors)} error(es) léxico(s) — ver pestaña.")
            self._set_status(f"● {len(lex_errors)} error(es) léxico(s)", "#ffb74d")
        else:
            self._console.ok(f"Léxico OK — {len(tokens)} tokens.")
            self._set_status("● Léxico OK", "#81c784")

        self._result_tabs.setCurrentIndex(0)

    # ═══════════════════════════════════════════════════════════
    # ANÁLISIS SINTÁCTICO
    # ═══════════════════════════════════════════════════════════

    def run_parser(self):
        e = self._ed()
        if not e: return
        code = e.toPlainText().strip()
        if not code:
            self._console.warning("El editor está vacío."); return

        self._console.separator("ANÁLISIS SINTÁCTICO")
        self._console.info("Ejecutando análisis léxico previo...")
        tokens, lex_errors = tokenize(code)

        self._lex_table.setRowCount(len(tokens))
        for i, (tipo, lexema, linea, col) in enumerate(tokens):
            self._lex_table.setItem(i, 0, self._cell(str(i+1), center=True))
            ti = QTableWidgetItem(tipo)
            ti.setForeground(QColor(_TYPE_COLORS.get(tipo, "#cccccc")))
            self._lex_table.setItem(i, 1, ti)
            self._lex_table.setItem(i, 2, self._cell(lexema))
            self._lex_table.setItem(i, 3, self._cell(str(linea), center=True))
            self._lex_table.setItem(i, 4, self._cell(str(col),   center=True))
        self._lbl_tokens.setText(f"Tokens: {len(tokens)}")

        if lex_errors:
            self._console.warning(f"{len(lex_errors)} error(es) léxico(s).")

        self._console.info("Iniciando análisis sintáctico...")
        self._set_status("● Analizando sintaxis...", "#64b5f6")

        if os.path.exists("tokens.txt"):
            tf = load_tokens_from_file("tokens.txt")
            parser = Parser(tf if tf else tokens)
            self._console.info("Tokens leídos desde tokens.txt.")
        else:
            parser = Parser(tokens)
        ast = parser.parse()
        parser.save_errors()

        self._ast_widget.clear()
        if ast:
            self._ast_widget.load_ast(ast)
            self._console.ok("AST generado correctamente.")

        self._syn_text.clear()
        self._syn_text.appendPlainText("═══ ÁRBOL SINTÁCTICO ═══\n")
        self._print_ast_text(ast, 0)

        # Terminal de errores sintácticos
        self._syn_err_term.show_syn_errors(parser.errors)

        self._update_error_counter(syn_n=len(parser.errors))
        if parser.errors:
            for err in parser.errors:
                self._console.error(err)
                self._mark_error_line(err)
            self._set_status(f"● {len(parser.errors)} error(es) sintáctico(s)", "#e57373")
            self._result_tabs.setCurrentIndex(4)
        else:
            self._syn_text.appendPlainText("\n✔  Sin errores sintácticos")
            self._console.ok("Sintáctico correcto — sin errores.")
            self._set_status("● Sintáctico OK", "#81c784")
            self._result_tabs.setCurrentIndex(2)

    def _print_ast_text(self, node, level):
        if not node: return
        indent = "  " * level
        text   = f"{indent}{node.node_type}"
        if node.value  is not None: text += f": {node.value}"
        if node.line   is not None: text += f"  [{node.line}:{node.column}]"
        self._syn_text.appendPlainText(text)
        for child in node.children:
            self._print_ast_text(child, level+1)

    def _mark_error_line(self, text):
        e = self._ed()
        if not e: return
        m = re.search(r'línea\s+(\d+)', text.lower())
        if not m: return
        cursor = e.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(int(m.group(1)) - 1):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        e.setTextCursor(cursor)

    # ═══════════════════════════════════════════════════════════
    # EJECUTAR / STUBS
    # ═══════════════════════════════════════════════════════════

    def run_semantic(self):
        self._console.separator("ANÁLISIS SEMÁNTICO")
        self._console.warning("Semántico aún no implementado en esta fase.")
        self._result_tabs.setCurrentIndex(5)

    def run_intermediate(self):
        self._console.separator("CÓDIGO INTERMEDIO")
        self._console.warning("Generación de código intermedio aún no implementada.")
        self._result_tabs.setCurrentIndex(5)

    def run_all(self):
        self._console.clear_log()
        self._console.separator("COMPILACIÓN COMPLETA")
        self.run_lexer()
        self.run_parser()
        self._console.separator()

    def clear_all(self):
        self._lex_table.setRowCount(0)
        self._lex_err_term.clear()
        self._syn_err_term.clear()
        self._ast_widget.clear()
        self._syn_text.clear()
        self._console.clear_log()
        self._console.info("Resultados limpiados.")
        self._lbl_tokens.setText("Tokens: —")
        self._set_status("● Listo")

    # ═══════════════════════════════════════════════════════════
    # TEMAS — selector visual minimalista
    # ═══════════════════════════════════════════════════════════

    def _apply_theme(self, key):
        ThemeManager.apply(key)
        self._settings.setValue("theme", key)
        self._console.info(f"Tema: {ThemeManager.label(key)}")

    def _show_theme_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Temas")
        dlg.setMinimumWidth(480)
        dlg.setMinimumHeight(420)

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(24, 24, 24, 20)
        main_layout.setSpacing(0)

        title = QLabel("Seleccionar tema")
        title.setStyleSheet("font-size:14pt;font-weight:700;margin-bottom:16px;")
        main_layout.addWidget(title)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(); scroll_layout = QVBoxLayout(content)
        scroll_layout.setSpacing(16)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        groups = [
            ("Oscuros",  ["dark_pro","pure_black","cyber_blue","tokyo_night","catppuccin","monokai","nord"]),
            ("Claros",   ["pure_white","light_pro"]),
            ("Clásicos", ["dracula","ocean","sunset","forest","neon","hacker"]),
        ]

        current = ThemeManager.current()

        for section_name, keys in groups:
            sec = QLabel(section_name.upper())
            sec.setStyleSheet(
                "font-size:8pt;font-weight:700;color:#666;"
                "letter-spacing:2px;margin-top:4px;margin-bottom:6px;"
            )
            scroll_layout.addWidget(sec)

            grid = QWidget(); gl = QGridLayout(grid); gl.setSpacing(8)
            for idx, key in enumerate(keys):
                btn = QPushButton()
                btn.setFixedHeight(56)
                bg     = ThemeManager.bg(key)
                accent = ThemeManager.accent(key)
                label  = ThemeManager.label(key)
                is_cur = (key == current)
                border = f"3px solid {accent}" if is_cur else f"1px solid #333"
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background:{bg}; color:{accent};
                        border:{border}; border-radius:8px;
                        font-size:9.5pt; font-weight:600;
                        text-align:left; padding:0 14px;
                    }}
                    QPushButton:hover {{
                        border:2px solid {accent};
                    }}
                """)
                btn.setText(("● " if is_cur else "  ") + label)
                btn.clicked.connect(lambda _, k=key: (self._apply_theme(k), dlg.accept()))
                gl.addWidget(btn, idx // 2, idx % 2)
            scroll_layout.addWidget(grid)

        scroll_layout.addStretch()
        dlg.exec()

    # ═══════════════════════════════════════════════════════════
    # PALETA DE COMANDOS
    # ═══════════════════════════════════════════════════════════

    def _show_command_palette(self):
        commands = [
            # (label, atajo, callback)
            ("Nuevo archivo",           "Ctrl+N",       self.new_file),
            ("Abrir archivo…",          "Ctrl+O",       self.open_file),
            ("Guardar",                 "Ctrl+S",       self.save_file),
            ("Guardar como…",           "Ctrl+Shift+S", self.save_as_file),
            ("Exportar como…",          "Ctrl+E",       self.export_as),
            ("Abrir PDF…",              "",             self.open_pdf),
            ("Cerrar pestaña",          "Ctrl+W",
             lambda: self._close_tab(self._editor_tabs.currentIndex())),
            ("Análisis léxico",         "F5",           self.run_lexer),
            ("Análisis sintáctico",     "F6",           self.run_parser),
            ("Análisis semántico",      "",             self.run_semantic),
            ("Código intermedio",       "",             self.run_intermediate),
            ("Compilar todo",           "F7",           self.run_all),
            ("Limpiar resultados",      "",             self.clear_all),
            ("Buscar en editor",        "Ctrl+F",       self._find),
            ("Zoom +",                  "Ctrl++",
             lambda: self._ed() and self._ed().zoomIn(2)),
            ("Zoom -",                  "Ctrl+-",
             lambda: self._ed() and self._ed().zoomOut(2)),
            ("Zoom reset",              "Ctrl+0",       self._zoom_reset),
            ("Seleccionar tema…",       "",             self._show_theme_dialog),
            ("Acerca de / Desarrolladores", "",         self._show_about),
            ("Salir",                   "Ctrl+Q",       self.close),
        ]
        # Agregar temas directamente
        for key in ["dark_pro","pure_black","pure_white","light_pro",
                    "cyber_blue","tokyo_night","catppuccin","monokai","nord",
                    "dracula","ocean","sunset","forest","neon","hacker"]:
            from ui.themes import ThemeManager as TM
            commands.append((
                f"Tema: {TM.label(key)}", "",
                lambda _, k=key: self._apply_theme(k)
            ))

        commands += [
            ("Ir a línea…",        "Ctrl+G",       self._goto_line),
            ("Atajos de teclado",  "Ctrl+K Ctrl+S",self._show_shortcuts_dialog),
            ("Reabrir pestaña cerrada", "Ctrl+Shift+T", self._reopen_closed_tab),
        ]

        palette = CommandPalette(commands, parent=self)
        palette.exec()

    def _zoom_reset(self):
        e = self._ed()
        if not e:
            return
        e.setFont(
            __import__("PyQt6.QtGui", fromlist=["QFont"]).QFont(
                "Menlo" if __import__("sys").platform == "darwin" else "Consolas", 12
            )
        )

    # ═══════════════════════════════════════════════════════════
    # BUSCAR
    # ═══════════════════════════════════════════════════════════

    def _find(self):
        e = self._ed()
        if not e: return
        text, ok = QInputDialog.getText(self, "Buscar", "Texto a buscar:")
        if ok and text:
            if not e.find(text):
                QMessageBox.information(self, "Buscar", "No se encontró el texto.")

    # ═══════════════════════════════════════════════════════════
    # ACERCA DE — diseño moderno
    # ═══════════════════════════════════════════════════════════

    def _show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Acerca de")
        dlg.setFixedSize(420, 460)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header de color
        accent = ThemeManager.accent(ThemeManager.current())
        header = QWidget()
        header.setFixedHeight(120)
        header.setStyleSheet(f"background:{accent};")
        hl = QVBoxLayout(header)
        hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.setSpacing(4)

        logo = QLabel("⟨/⟩")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color:white;font-size:28pt;font-weight:300;")

        name = QLabel("IDE Compilador")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("color:white;font-size:14pt;font-weight:700;")

        hl.addWidget(logo); hl.addWidget(name)
        layout.addWidget(header)

        # Cuerpo
        body = QWidget()
        body.setStyleSheet("background:transparent;")
        bl   = QVBoxLayout(body)
        bl.setContentsMargins(32, 24, 32, 24)
        bl.setSpacing(6)

        def row(left, right, left_color="#888", right_color=None):
            rw = QWidget(); rl = QHBoxLayout(rw); rl.setContentsMargins(0,0,0,0)
            ll = QLabel(left);  ll.setStyleSheet(f"color:{left_color};font-size:9pt;")
            rl.addWidget(ll)
            rl.addStretch()
            lr = QLabel(right)
            if right_color:
                lr.setStyleSheet(f"color:{right_color};font-size:9pt;font-weight:600;")
            else:
                lr.setStyleSheet("font-size:9pt;font-weight:600;")
            rl.addWidget(lr)
            return rw

        def divider():
            f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
            f.setStyleSheet("color:#2a2a2a;margin:8px 0;")
            return f

        bl.addWidget(row("Versión", "2.1"))
        bl.addWidget(row("Fase", "Análisis Léxico & Sintáctico"))
        bl.addWidget(row("Entorno", "Python (venv activo)" if _IN_VENV else "Python",
                         right_color="#22c55e" if _IN_VENV else None))
        bl.addWidget(divider())

        dev1_w = QWidget(); d1l = QVBoxLayout(dev1_w); d1l.setContentsMargins(0,0,0,0); d1l.setSpacing(2)
        n1 = QLabel("Jesus Abraham Robledo Lopez")
        n1.setStyleSheet(f"color:{accent};font-size:10.5pt;font-weight:700;")
        i1 = QLabel("ID: 284745"); i1.setStyleSheet("color:#666;font-size:8.5pt;")
        d1l.addWidget(n1); d1l.addWidget(i1)
        bl.addWidget(dev1_w)
        bl.addSpacing(8)

        dev2_w = QWidget(); d2l = QVBoxLayout(dev2_w); d2l.setContentsMargins(0,0,0,0); d2l.setSpacing(2)
        n2 = QLabel("Edgar Alejandro Cedeño Suarez")
        n2.setStyleSheet(f"color:{accent};font-size:10.5pt;font-weight:700;")
        i2 = QLabel("ID: 262728"); i2.setStyleSheet("color:#666;font-size:8.5pt;")
        d2l.addWidget(n2); d2l.addWidget(i2)
        bl.addWidget(dev2_w)

        bl.addWidget(divider())
        close_btn = QPushButton("Cerrar")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(dlg.accept)
        bl.addWidget(close_btn)

        layout.addWidget(body)
        dlg.exec()

    # ═══════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════
    # IR A LÍNEA
    # ═══════════════════════════════════════════════════════════

    def _goto_line(self):
        e = self._ed()
        if not e:
            return
        max_ln = e.document().blockCount()
        ln, ok = QInputDialog.getInt(
            self, "Ir a línea", f"Número de línea (1 – {max_ln}):",
            self._ed().textCursor().blockNumber() + 1, 1, max_ln
        )
        if ok:
            cur = e.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(ln - 1):
                cur.movePosition(QTextCursor.MoveOperation.Down)
            cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
            e.setTextCursor(cur)
            e.centerCursor()
            e.setFocus()

    # ═══════════════════════════════════════════════════════════
    # REABRIR PESTAÑA CERRADA (Ctrl+Shift+T)
    # ═══════════════════════════════════════════════════════════

    def _reopen_closed_tab(self):
        if not self._closed_tabs:
            return
        data = self._closed_tabs.pop()
        e = CodeEditor()
        e.setPlainText(data["content"])
        if data.get("file_path"):
            e.file_path = data["file_path"]
        e.cursorPositionChanged.connect(self._update_cursor)
        e.file_modified.connect(lambda: self._mark_tab_modified(e))
        idx = self._editor_tabs.addTab(e, data["title"])
        self._editor_tabs.setCurrentIndex(idx)
        self._set_tab_icon(idx, data.get("file_path", ""))

    # ═══════════════════════════════════════════════════════════
    # INDICADOR DE ARCHIVO MODIFICADO EN PESTAÑA
    # ═══════════════════════════════════════════════════════════

    def _mark_tab_modified(self, editor: CodeEditor):
        for i in range(self._editor_tabs.count()):
            if self._editor_tabs.widget(i) is editor:
                title = self._editor_tabs.tabText(i)
                if not title.startswith("·"):
                    self._editor_tabs.setTabText(i, "· " + title)
                break

    def _mark_tab_saved(self, index: int):
        title = self._editor_tabs.tabText(index)
        if title.startswith("· "):
            self._editor_tabs.setTabText(index, title[2:])

    # ═══════════════════════════════════════════════════════════
    # DRAG & DROP de archivos sobre la ventana
    # ═══════════════════════════════════════════════════════════

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path:
                    self.open_file(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    # ═══════════════════════════════════════════════════════════
    # DIÁLOGO DE ATAJOS DE TECLADO
    # ═══════════════════════════════════════════════════════════

    def _show_shortcuts_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Atajos de teclado")
        dlg.setMinimumWidth(560)
        dlg.setMinimumHeight(520)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(0)

        title = QLabel("Atajos de teclado")
        title.setStyleSheet("font-size:14pt;font-weight:700;margin-bottom:14px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setSpacing(2)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        groups = [
            ("Archivo", [
                ("Ctrl+N",         "Nuevo archivo"),
                ("Ctrl+O",         "Abrir archivo"),
                ("Ctrl+S",         "Guardar"),
                ("Ctrl+Shift+S",   "Guardar como"),
                ("Ctrl+E",         "Exportar como"),
                ("Ctrl+W",         "Cerrar pestaña"),
                ("Ctrl+Shift+T",   "Reabrir pestaña cerrada"),
                ("Ctrl+Q",         "Salir"),
            ]),
            ("Editar", [
                ("Ctrl+Z",         "Deshacer"),
                ("Ctrl+Y",         "Rehacer"),
                ("Ctrl+X",         "Cortar"),
                ("Ctrl+C",         "Copiar"),
                ("Ctrl+V",         "Pegar"),
                ("Ctrl+A",         "Seleccionar todo"),
                ("Ctrl+F",         "Buscar"),
                ("Ctrl+D",         "Duplicar línea"),
                ("Ctrl+/",         "Comentar / descomentar"),
                ("Ctrl+Shift+K",   "Eliminar línea"),
                ("Alt+↑",          "Mover línea arriba"),
                ("Alt+↓",          "Mover línea abajo"),
                ("Tab",            "Indentar (4 espacios)"),
                ("Shift+Tab",      "Des-indentar"),
            ]),
            ("Ver", [
                ("Ctrl+G",         "Ir a línea"),
                ("Ctrl++",         "Zoom +"),
                ("Ctrl+-",         "Zoom -"),
                ("Ctrl+0",         "Zoom reset"),
                ("Ctrl+Shift+P",   "Paleta de comandos"),
                ("Ctrl+K Ctrl+S",  "Ver atajos"),
            ]),
            ("Analizar", [
                ("F5",             "Análisis léxico"),
                ("F6",             "Análisis sintáctico"),
                ("F7",             "Compilar todo"),
            ]),
            ("Editor", [
                ("Ctrl+Rueda",     "Zoom con mouse"),
                ("Drag & Drop",    "Arrastra archivos al editor"),
                ("Click derecho",  "Menú contextual del editor"),
            ]),
        ]

        for group_name, shortcuts in groups:
            sec = QLabel(group_name.upper())
            sec.setStyleSheet(
                "font-size:7.5pt;font-weight:700;color:#555;"
                "letter-spacing:2px;padding-top:14px;padding-bottom:4px;"
            )
            cl.addWidget(sec)

            for keys, desc in shortcuts:
                row = QWidget()
                rl  = QHBoxLayout(row)
                rl.setContentsMargins(0, 3, 0, 3)
                rl.setSpacing(12)

                key_lbl = QLabel(keys)
                key_lbl.setStyleSheet(
                    "background:#2a2a2a;color:#c0c0c0;border-radius:4px;"
                    "padding:3px 10px;font-family:monospace;font-size:9pt;"
                    "font-weight:600;min-width:140px;"
                )
                key_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                key_lbl.setFixedWidth(160)

                desc_lbl = QLabel(desc)
                desc_lbl.setStyleSheet("font-size:9.5pt;")

                rl.addWidget(key_lbl)
                rl.addWidget(desc_lbl)
                rl.addStretch()
                cl.addWidget(row)

        cl.addStretch()

        close_btn = QPushButton("Cerrar")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(dlg.accept)
        layout.addSpacing(12)
        layout.addWidget(close_btn)
        dlg.exec()

    @staticmethod
    def _cell(text, center=False, err=False):
        item = QTableWidgetItem(text)
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if err:
            item.setForeground(QColor("#f48771"))
        return item

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
