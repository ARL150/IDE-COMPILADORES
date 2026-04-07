from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSettings, QTimer, QDir
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QFileSystemModel
from ui.editor import CodeEditor
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QStyle
from PyQt6.QtCore import QSize
import subprocess
import os
from PyQt6.QtGui import QTextCursor, QTextFormat
import locale
import re

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.settings = QSettings("IDECompilador", "IDEConfig")
        self.setWindowTitle("IDE Compilador")
        self.resize(1200, 800)

        self.closed_tabs = []
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.statusBar().showMessage("Línea: 1 Columna: 1")
        self.create_menu()
        self.create_toolbar()
        self.create_docks()
        self.create_file_explorer()
        self.init_terminal()

        self.new_file()

        saved_theme = self.settings.value("theme", "dark")
        self.set_theme(saved_theme)

        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.auto_save)
        self.autosave_timer.start(5000)  # cada 5 segundos

        # Restaurar geometría de la ventana
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)

    def decode_data(self, qbytearray):
        encoding = locale.getpreferredencoding()
        return qbytearray.data().decode(encoding, errors="replace")

    def activate_button(self, btn, func):
        for action in self.toolbar.actions():
            if action.isCheckable():
                action.setChecked(False)

        btn.setChecked(True)
        func()

    # =========================
    # EDITOR ACTUAL
    # =========================

    def current_editor(self):
        return self.tabs.currentWidget()

    def update_cursor(self):
        editor = self.current_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            self.statusBar().showMessage(f"Línea: {line} Columna: {col}")

    # =========================
    # ARCHIVOS
    # =========================

    def new_file(self):
        editor = CodeEditor()
        index = self.tabs.addTab(editor, "Sin título")
        self.tabs.setCurrentIndex(index)
        editor.cursorPositionChanged.connect(self.update_cursor)

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Abrir")

        if file:
            with open(file, "r") as f:
                content = f.read()

            editor = CodeEditor()
            editor.setPlainText(content)

            filename = os.path.basename(file)
            # si quieres forzar extensión .py por defecto:
            if not os.path.splitext(filename)[1]:
                filename += ".py"

            index = self.tabs.addTab(editor, filename)
            self.tabs.setCurrentIndex(index)

            name, ext = os.path.splitext(filename)
            self.tabs.setTabText(index, name + ext)
            self.tabs.tabBar().setTabTextColor(index, QColor("red"))

            editor.file_path = file
            editor.cursorPositionChanged.connect(self.update_cursor)

    def save_file(self):
        editor = self.current_editor()

        if hasattr(editor, "file_path"):
            with open(editor.file_path, "w") as f:
                f.write(editor.toPlainText())
        else:
            self.save_as_file()

    def save_as_file(self):
        editor = self.current_editor()

        file, _ = QFileDialog.getSaveFileName(self, "Guardar", filter="Python Files (*.py);;All Files (*)")
        if file:
            # forzar extensión .py si el usuario no puso ninguna
            if not os.path.splitext(file)[1]:
                file += ".py"

            with open(file, "w") as f:
                f.write(editor.toPlainText())

            editor.file_path = file
            filename = os.path.basename(file)
            self.tabs.setTabText(self.tabs.currentIndex(), filename)
    
    def close_tab(self, index):
        editor = self.tabs.widget(index)

        if editor:
            self.closed_tabs.append({
                "content": editor.toPlainText(),
                "title": self.tabs.tabText(index),
                "file_path": getattr(editor, "file_path", None)
            })

        self.tabs.removeTab(index)

    def close_file(self):
        index = self.tabs.currentIndex()
        if index != -1:
            self.tabs.removeTab(index)

    def reopen_last_tab(self):
        if not self.closed_tabs:
            return

        data = self.closed_tabs.pop()

        editor = CodeEditor()
        editor.setPlainText(data["content"])

        if data["file_path"]:
            editor.file_path = data["file_path"]

        index = self.tabs.addTab(editor, data["title"])
        self.tabs.setCurrentIndex(index)

        editor.cursorPositionChanged.connect(self.update_cursor)

    # =========================
    # AUTOGUARDADO
    # =========================

    def auto_save(self):

        editor = self.current_editor()

        if editor and hasattr(editor, "file_path"):

            try:
                with open(editor.file_path, "w") as f:
                    f.write(editor.toPlainText())

                self.statusBar().showMessage("Autoguardado ✔", 2000)

            except:
                pass

    # =========================
    # EDITAR FUNCIONES
    # =========================

    def current_editor(self):
        editor = self.tabs.currentWidget()
        if isinstance(editor, CodeEditor):
            return editor
        return None

    def undo_text(self):
        editor = self.current_editor()
        if editor:
            editor.undo()

    def redo_text(self):
        editor = self.current_editor()
        if editor:
            editor.redo()

    def cut_text(self):
        editor = self.current_editor()
        if editor:
            editor.cut()

    def copy_text(self):
        editor = self.current_editor()
        if editor:
            editor.copy()

    def paste_text(self):
        editor = self.current_editor()
        if editor:
            editor.paste()

    def select_all_text(self):
        editor = self.current_editor()
        if editor:
            editor.selectAll()

    def show_find_dialog(self):
        editor = self.current_editor()
        if editor:
            text, ok = QInputDialog.getText(self, "Buscar", "Texto:")
            if ok and text:
                if not editor.find(text):
                    QMessageBox.information(self, "Buscar", "No se encontró el texto")

    # =========================
    # ZOOM
    # =========================

    def zoom_in(self):
        editor = self.current_editor()
        if editor:
            editor.zoomIn(2)

    def zoom_out(self):
        editor = self.current_editor()
        if editor:
            editor.zoomOut(2)

    def reset_zoom(self):
        editor = self.current_editor()
        if editor:
            font = editor.font()
            font.setPointSize(12)
            editor.setFont(font)

    # =========================
    # TERMINAL FUNCIONAL SIMPLE
    # =========================
    def init_terminal(self):
        self.process = QProcess(self)
        shell = "cmd.exe" if os.name == "nt" else "/bin/zsh"
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_terminal_output)
        self.process.readyReadStandardError.connect(self.handle_terminal_output)
        self.process.start(shell)
        self.console.appendPlainText(f"Terminal iniciada en: {os.getcwd()}\n")
        self.command_history = []
        self.history_index = -1

    # def handle_terminal_output(self):
    #     if self.process:
    #         data = self.decode_data(self.process.readAllStandardOutput())
    #         if data:
    #             self.console.appendPlainText(data)
    #             self.console.moveCursor(QTextCursor.MoveOperation.End)

    def keyPressEvent(self, event):
        if self.console.hasFocus():
            if event.key() == Qt.Key.Key_Return:
                # Obtener la última línea como comando
                command = self.console.toPlainText().splitlines()[-1].strip()
                if command:
                    self.command_history.append(command)
                    self.history_index = len(self.command_history)
                    self.process.write((command + "\n").encode())
                return
            elif event.key() == Qt.Key.Key_Up:
                # Navegar historial arriba
                if self.command_history and self.history_index > 0:
                    self.history_index -= 1
                    self.replace_last_line(self.command_history[self.history_index])
                return
            elif event.key() == Qt.Key.Key_Down:
                # Navegar historial abajo
                if self.command_history and self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.replace_last_line(self.command_history[self.history_index])
                elif self.history_index == len(self.command_history) - 1:
                    self.history_index += 1
                    self.replace_last_line("")
                return
        super().keyPressEvent(event)

    def replace_last_line(self, text):
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(text)
        self.console.setTextCursor(cursor)

    # =========================
    # MENÚ
    # =========================
    def create_menu(self):
        menu_bar = self.menuBar()

        # ===== ARCHIVO =====
        file_menu = menu_bar.addMenu("Archivo")

        new_action = QAction("Nuevo", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Abrir", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Menú Archivo
        open_folder_action = QAction("Abrir carpeta", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)    
                

        save_action = QAction("Guardar", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        saveas_action = QAction("Guardar como", self)
        saveas_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        saveas_action.triggered.connect(self.save_as_file)
        file_menu.addAction(saveas_action)

        close_action = QAction("Cerrar", self)
        close_action.setShortcut(QKeySequence("Ctrl+W"))
        close_action.triggered.connect(self.close_file)
        file_menu.addAction(close_action)

        file_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ===== EDITAR =====
        edit_menu = menu_bar.addMenu("Editar")

        undo_action = QAction("Deshacer", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo_text)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Rehacer", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.redo_text)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cortar", self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        cut_action.triggered.connect(self.cut_text)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copiar", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.triggered.connect(self.copy_text)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Pegar", self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))
        paste_action.triggered.connect(self.paste_text)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Seleccionar Todo", self)
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self.select_all_text)
        edit_menu.addAction(select_all_action)

        edit_menu.addSeparator()

        find_action = QAction("Buscar", self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)

        edit_menu.addSeparator()

        zoom_in_action = QAction("Zoom +", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.zoom_in)
        edit_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom -", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.zoom_out)
        edit_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction("Restablecer Zoom", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.triggered.connect(self.reset_zoom)
        edit_menu.addAction(reset_zoom_action)    

        # ===== PESTAÑAS =====
        tabs_menu = menu_bar.addMenu("Pestañas")
        tabs_menu.addSeparator()

        next_tab = QAction("Siguiente", self)
        next_tab.setShortcut(QKeySequence("Ctrl+Tab"))
        next_tab.triggered.connect(
            lambda: self.tabs.setCurrentIndex(
                (self.tabs.currentIndex() + 1) % self.tabs.count()
            )
        )
        tabs_menu.addAction(next_tab)

        prev_tab = QAction("Anterior", self)
        prev_tab.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
        prev_tab.triggered.connect(
            lambda: self.tabs.setCurrentIndex(
                (self.tabs.currentIndex() - 1) % self.tabs.count()
            )
        )
        tabs_menu.addAction(prev_tab)

        # ===== TEMAS =====
        theme_menu = menu_bar.addMenu("Temas")

        dark = QAction("Oscuro", self)
        dark.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark)

        light = QAction("Claro", self)
        light.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light)

        dracula = QAction("Dracula", self)
        dracula.triggered.connect(lambda: self.set_theme("dracula"))
        theme_menu.addAction(dracula)

        ocean = QAction("Ocean Blue", self)
        ocean.triggered.connect(lambda: self.set_theme("ocean"))
        theme_menu.addAction(ocean)

        sunset = QAction("Sunset", self)
        sunset.triggered.connect(lambda: self.set_theme("sunset"))
        theme_menu.addAction(sunset)

        forest = QAction("Forest", self)
        forest.triggered.connect(lambda: self.set_theme("forest"))
        theme_menu.addAction(forest)

        neon = QAction("Neon Purple", self)
        neon.triggered.connect(lambda: self.set_theme("neon"))
        theme_menu.addAction(neon)

        hacker = QAction("Hacker Classic", self)
        hacker.triggered.connect(lambda: self.set_theme("hacker"))
        theme_menu.addAction(hacker)

        # ===== DESARROLLADORES =====
        dev_menu = menu_bar.addMenu("Desarrolladores")

        about_dev = QAction("Equipo de Desarrollo", self)
        about_dev.triggered.connect(self.show_developers)
        dev_menu.addAction(about_dev)

    # =========================
    # TOOLBAR
    # =========================

    def create_toolbar(self):
        self.toolbar = self.addToolBar("Principal")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        # 🎨 Estilo moderno oscuro
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 10px;
                padding: 8px;
                background-color: #1e1e1e;
                border: none;
            }
            QLabel {
                font-weight: bold;
                font-size: 11px;
                color: white;
                padding: 4px;
            }
            QToolButton {
                color: white;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #2a2a2a;
                border-radius: 4px;
            }
        """)

        # ========================
        # 📂 SECCIÓN ARCHIVO
        # ========================

        archivo_label = QLabel("ARCHIVO")
        self.toolbar.addWidget(archivo_label)

        self.toolbar.addSeparator()

        # NUEVO
        new_action = QAction(QIcon("icons/file.svg"), "Nuevo", self)
        new_action.triggered.connect(self.new_file)
        self.toolbar.addAction(new_action)

        # ABRIR
        open_action = QAction(QIcon("icons/folder-open (2).svg"), "Abrir", self)
        open_action.triggered.connect(self.open_file)
        self.toolbar.addAction(open_action)

        # GUARDAR
        save_action = QAction(QIcon("icons/save.svg"), "Guardar", self)
        save_action.triggered.connect(self.save_file)
        self.toolbar.addAction(save_action)

        # GUARDAR COMO
        save_as_action = QAction(QIcon("icons/archive.svg"), "Guardar como", self)
        save_as_action.triggered.connect(self.save_as_file)
        self.toolbar.addAction(save_as_action)

        # CERRAR
        close_action = QAction(QIcon("icons/x-circle.svg"), "Cerrar", self)
        close_action.triggered.connect(self.close_file)
        self.toolbar.addAction(close_action)

        # SALIR
        exit_action = QAction(QIcon("icons/x.svg"), "Salir", self)
        exit_action.triggered.connect(self.close)
        self.toolbar.addAction(exit_action)

        # Separador grande visual
        self.toolbar.addSeparator()
        # ========================
        # ▶ SECCIÓN EJECUTAR
        # ========================

        ejecutar_label = QLabel("EJECUTAR")
        self.toolbar.addWidget(ejecutar_label)

        self.toolbar.addSeparator()

        # LÉXICO
        self.lex_btn = QAction(QIcon("icons/captions.svg"), "Léxico", self)
        self.lex_btn.triggered.connect(self.run_lexer)
        self.toolbar.addAction(self.lex_btn)

        # SINTÁCTICO
        self.syn_btn = QAction(QIcon("icons/blanket.svg"), "Sintáctico", self)
        self.syn_btn.triggered.connect(self.run_parser)
        self.toolbar.addAction(self.syn_btn)

        # SEMÁNTICO
        self.sem_btn = QAction(QIcon("icons/message-circle-captions.svg"), "Semántico", self)
        self.sem_btn.triggered.connect(self.run_semantic)
        self.toolbar.addAction(self.sem_btn)

        # INTERMEDIO
        self.int_btn = QAction(QIcon("icons/monitor-wide.svg"), "Intermedio", self)
        self.int_btn.triggered.connect(self.run_intermediate)
        self.toolbar.addAction(self.int_btn)

        # EJECUTAR
        self.exe_btn = QAction(QIcon("icons/play.svg"), "Ejecutar", self)
        self.exe_btn.triggered.connect(self.run_execution)
        self.toolbar.addAction(self.exe_btn)

        self.toolbar.addAction(self.lex_btn)
        self.toolbar.addAction(self.syn_btn)
        self.toolbar.addAction(self.sem_btn)
        self.toolbar.addAction(self.int_btn)
        self.toolbar.addAction(self.exe_btn)

    # =========================
    # DOCKS
    # =========================

        # =========================
    # DOCKS Y TOOLBAR CON GUARDADO DE POSICIÓN
    # =========================

    def create_docks(self):
        # Docks que muestran salida de texto
        self.lex = QPlainTextEdit(); self.lex.setReadOnly(True)
        self.syn = QPlainTextEdit(); self.syn.setReadOnly(True)
        self.sem = QPlainTextEdit(); self.sem.setReadOnly(True)
        self.inter = QPlainTextEdit(); self.inter.setReadOnly(True)
        self.sym = QPlainTextEdit(); self.sym.setReadOnly(True)
        self.err = QPlainTextEdit(); self.err.setReadOnly(True)
        self.err.setStyleSheet("""background-color: #1e1e1e;color: #ff4c4c; font-weight: bold; """)
        self.console = QPlainTextEdit()
        self.console.setStyleSheet("background:black; color:#00ff00;")
        self.console.setFont(QFont("JetBrains Mono", 11))

        # Crear docks
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.createDock("Léxico", self.lex, "dock_lex"))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.createDock("Sintáctico", self.syn, "dock_syn"))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.createDock("Semántico", self.sem, "dock_sem"))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.createDock("Intermedio", self.inter, "dock_int"))
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.createDock("Tabla de Símbolos", self.sym, "dock_sym"))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.createDock("Errores", self.err, "dock_err"))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.createDock("Consola", self.console, "dock_console"))
        
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))

    def createDock(self, title, widget, object_name):
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setObjectName(object_name)  # MUY IMPORTANTE para que saveState funcione

        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        return dock
    
    def run_lexer(self):
        self.lex.clear()
        self.err.clear() 
        self.run_process("lexer.py", self.lex)


    # =========================
    # SOBRESCRIBIR CLOSEEVENT PARA GUARDAR ESTADO
    # =========================
    def closeEvent(self, event):
        # Guardar geometría y estado de docks/toolbar
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def createDock(self, title, widget, object_name):
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setObjectName(object_name)  # <-- ESTO ES IMPORTANTE
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        return dock
    
    # =========================
    # EXPLORADOR DE ARCHIVOS
    # =========================

    def create_file_explorer(self):
        self.model = QFileSystemModel()
        self.model.setRootPath("")  # Sin ruta al inicio
        self.model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.doubleClicked.connect(self.open_file_from_explorer)
        self.tree.setColumnWidth(0, 250)

        self.explorer_dock = QDockWidget("Explorador", self)
        self.explorer_dock.setWidget(self.tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer_dock)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Abrir carpeta", QDir.homePath())
        if folder:
            # Cambiar raíz del modelo a la nueva carpeta
            self.tree.setRootIndex(self.model.setRootPath(folder))
            self.explorer_dock.setWindowTitle(f"Explorador - {folder}")

    # =========================
    # COMPILADOR
    # =========================

    def run_process(self, script, output_widget):
        editor = self.current_editor()
        if not editor or not hasattr(editor, "file_path"):
            self.console.appendPlainText("Guarda el archivo primero")
            return
        
        #Limpiar salida y errores antes de ejecutar
        output_widget.clear()
        self.err.clear()

        self.process = QProcess(self)
        self.process.setProgram("python")
        self.process.setArguments([f"compiler/{script}", editor.file_path])
        self.process.readyReadStandardOutput.connect(lambda: self.handle_process_output(output_widget))
        self.process.readyReadStandardError.connect(lambda: self.handle_process_output(self.err))
        self.process.start()

    def run_lexer(self):
        self.run_process("lexer.py", self.lex)

    def run_parser(self): self.run_process("parser.py", self.syn)
    def run_semantic(self):
        editor = self.current_editor()
        if not editor or not hasattr(editor, "file_path"):
            self.console.appendPlainText("Guarda el archivo primero")
            return

        self.process = QProcess(self)
        self.process.setProgram("python")
        self.process.setArguments(["compiler/semantic.py", editor.file_path])
        self.process.readyReadStandardOutput.connect(self.handle_semantic_output)
        self.process.readyReadStandardError.connect(lambda: self.err.appendPlainText(self.decode_data(self.process.readAllStandardError())))
        self.process.start()
    def run_intermediate(self): self.run_process("intermediate.py", self.inter)
    def run_execution(self): self.run_process("executor.py", self.console)
    
    def handle_semantic_output(self):
        output = self.decode_data(self.process.readAllStandardOutput())
        if not output.strip():
            return
        # Separar tabla y errores
        if "===TABLA_DE_SIMBOLOS===" in output and "===ERRORES_SEMANTICOS===" in output:
            tabla = output.split("===TABLA_DE_SIMBOLOS===")[1].split("===ERRORES_SEMANTICOS===")[0].strip()
            errores = output.split("===ERRORES_SEMANTICOS===")[1].strip()
            self.sym.setPlainText(tabla if tabla else "(Tabla vacía)")
            self.err.setPlainText(errores if errores else "Sin errores semánticos")
        else:
            self.console.appendPlainText(output)
    # =========================
    # TEMAS
    # =========================

    def set_theme(self, theme):

        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow { background:#1e1e1e; color:white; }
                QTextEdit { background:#252526; color:#f8f8f2; }
                QTabBar::tab:selected { background:#007acc; }
            """)

        elif theme == "light":
            self.setStyleSheet("""
                QMainWindow { background:white; color:black; }
                QTextEdit { background:white; color:black; }
                QTabBar::tab:selected { background:#ddd; }
            """)

        elif theme == "dracula":
            self.setStyleSheet("""
                QMainWindow { background:#282a36; color:#f8f8f2; }
                QTextEdit { background:#44475a; color:#f8f8f2; }
                QTabBar::tab:selected { background:#bd93f9; }
            """)

        elif theme == "ocean":
            self.setStyleSheet("""
                QMainWindow { background:#0f172a; color:#e2e8f0; }
                QTextEdit { background:#1e293b; color:#e2e8f0; }
                QTabWidget::pane { border: 1px solid #334155; }
                QTabBar::tab { background:#1e293b; padding:8px; }
                QTabBar::tab:selected { background:#3b82f6; color:white; }
                QMenuBar { background:#0f172a; color:#e2e8f0; }
                QMenu { background:#1e293b; color:#e2e8f0; }
            """)

        elif theme == "sunset":
            self.setStyleSheet("""
                QMainWindow { background:#2b1d1d; color:#ffe4d6; }
                QTextEdit { background:#3a2a2a; color:#fff3e6; }
                QTabBar::tab { background:#3a2a2a; padding:8px; }
                QTabBar::tab:selected { background:#ff7b00; color:black; }
                QMenuBar { background:#2b1d1d; color:#ffe4d6; }
                QMenu { background:#3a2a2a; color:#fff3e6; }
            """)

        elif theme == "forest":
            self.setStyleSheet("""
                QMainWindow { background:#0d1f1a; color:#d1fae5; }
                QTextEdit { background:#13332b; color:#a7f3d0; }
                QTabBar::tab { background:#13332b; padding:8px; }
                QTabBar::tab:selected { background:#10b981; color:black; }
                QMenuBar { background:#0d1f1a; color:#d1fae5; }
                QMenu { background:#13332b; color:#a7f3d0; }
            """)            

        elif theme == "neon":
            self.setStyleSheet("""
                QMainWindow { background:#140021; color:#f5d0fe; }
                QTextEdit { background:#1f0033; color:#e879f9; }
                QTabBar::tab { background:#1f0033; padding:8px; }
                QTabBar::tab:selected { background:#c026d3; color:white; }
                QMenuBar { background:#140021; color:#f5d0fe; }
                QMenu { background:#1f0033; color:#e879f9; }
            """)

        elif theme == "hacker":
            self.setStyleSheet("""
                QMainWindow { background:black; color:#00ff00; }
                QTextEdit { background:black; color:#00ff00; }
                QTabBar::tab { background:#001100; padding:8px; }
                QTabBar::tab:selected { background:#00aa00; color:black; }
                QMenuBar { background:black; color:#00ff00; }
                QMenu { background:#001100; color:#00ff00; }
            """)

        self.settings.setValue("theme", theme)

    
    def show_developers(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Desarrolladores")
        dialog.resize(420, 300)

        layout = QVBoxLayout()

        title = QLabel("IDE Compilador")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold;")

        subtitle = QLabel("Equipo de Desarrollo:")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dev1 = QLabel("Jesus Abraham Robledo Lopez")
        dev1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev1.setStyleSheet("font-size:14px; color:#3b82f6;")

        id1 = QLabel("ID: 284745")
        id1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dev2 = QLabel("Edgar Alejandro Cedeño Suarez")
        dev2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev2.setStyleSheet("font-size:14px; color:#10b981;")

        id2 = QLabel("ID: 262728")
        id2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version = QLabel("Versión 1.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(dev1)
        layout.addWidget(id1)
        layout.addSpacing(10)
        layout.addWidget(dev2)
        layout.addWidget(id2)
        layout.addSpacing(10)
        layout.addWidget(version)

        dialog.setLayout(layout)
        dialog.exec()

    def open_file_from_explorer(self, index):

        file_path = self.model.filePath(index)

        if os.path.isfile(file_path):

            with open(file_path, "r") as f:
                content = f.read()

            editor = CodeEditor()
            editor.setPlainText(content)
            editor.file_path = file_path

            filename = os.path.basename(file_path)

            i = self.tabs.addTab(editor, filename)
            self.tabs.setCurrentIndex(i)

            editor.cursorPositionChanged.connect(self.update_cursor)
   
    def handle_terminal_output(self):
        if self.process:
            data = self.decode_data(self.process.readAllStandardOutput())
            if data:
                self.console.appendPlainText(data)

    def keyPressEvent(self, event):
        if self.console.hasFocus() and event.key() == Qt.Key.Key_Return:
            cursor = self.console.textCursor()
            cursor.movePosition(cursor.MoveOperation.StartOfBlock, cursor.MoveMode.KeepAnchor)
            command = cursor.selectedText().strip()
            if command:
                self.process.write((command + "\n").encode())
                self.console.appendPlainText(f"$ {command}")  # opcional, muestra comando
            return
        super().keyPressEvent(event)

    def handle_process_output(self, output_widget):
        if not self.process:
            return

        out = self.decode_data(self.process.readAllStandardOutput())
        err = self.decode_data(self.process.readAllStandardError())

        def es_error(texto):
            texto = texto.lower()
            return (
                "error" in texto or
                "syntax" in texto or
                "exception" in texto or
                "unexpected" in texto
            )

        if out:
            lineas = out.splitlines()
            for linea in lineas:
                if es_error(linea):
                    self.err.appendPlainText(linea)
                    self.marcar_error_en_editor(linea)

                    self.err.verticalScrollBar().setValue(self.err.verticalScrollBar().maximum())

                else:
                    output_widget.appendPlainText(linea)
                    output_widget.verticalScrollBar().setValue(output_widget.verticalScrollBar().maximum())

        if err:
            self.err.appendPlainText(err)
            self.marcar_error_en_editor(err)

    def marcar_error_en_editor(self, texto):
        editor = self.current_editor()
        if not editor:
            return

        #Buscar numero de linea 
        match = re.search(r'linea\s*(\d+)|line\s*(\d+)', texto.lower())
        if not match:
            return  
        
        linea = int(match.group(1) or match.group(2))

        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        for _ in range(linea - 1):
            cursor.movePosition(QTextCursor.MoveOperation.Down)

        editor.setTextCursor(cursor)

        extraSelections = []
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        selection.format.setBackground(QColor("#ff4c4c"))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        extraSelections.append(selection)
        editor.setExtraSelections(extraSelections)


    

    def run_execution(self):
        self.run_process("executor.py", self.console)
 