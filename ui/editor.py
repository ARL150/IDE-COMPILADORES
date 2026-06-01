import platform
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QMenu
from PyQt6.QtGui import (
    QColor, QTextFormat, QPainter, QFont, QAction,
    QTextCursor, QKeySequence,
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from ui.syntax_highlighter import SyntaxHighlighter


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    """
    Editor de código con:
    - Números de línea
    - Resaltado de línea actual
    - Atajos profesionales (Ctrl+D, Ctrl+/, Alt+↑↓, etc.)
    - Auto-cierre de brackets y comillas
    - Auto-indentación inteligente
    - Drag & drop de archivos
    - Menú contextual rico
    - Señal de modificación para indicador en pestaña
    """

    file_modified = pyqtSignal()   # emitido cuando el contenido cambia por primera vez

    GUTTER_BG        = QColor("#161616")
    GUTTER_ACTIVE_BG = QColor("#252525")
    GUTTER_BORDER    = QColor("#2a2a2a")
    LINE_NUM_COLOR   = QColor("#3d3d3d")
    LINE_NUM_ACTIVE  = QColor("#bbbbbb")
    CURRENT_LINE_BG  = QColor(40, 44, 52, 70)

    def __init__(self):
        super().__init__()
        self.file_path = None
        self._modified = False

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setAcceptDrops(True)

        if platform.system() == "Darwin":
            code_font = QFont("Menlo", 12)
        else:
            code_font = QFont("Consolas", 11)
        code_font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(code_font)

        # Gutter
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._update_gutter_region)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self._update_gutter_width(0)
        self.highlightCurrentLine()

        self.highlighter = SyntaxHighlighter(self.document())

        # Señal de modificación
        self.document().contentsChanged.connect(self._on_contents_changed)

    # ── Gutter ──────────────────────────────────────────────────

    def lineNumberAreaWidth(self):
        digits = max(3, len(str(self.blockCount())))
        return self.fontMetrics().horizontalAdvance("9") * digits + 28

    def _update_gutter_width(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def _update_gutter_region(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_gutter_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        w = self.lineNumberArea.width()
        painter.fillRect(event.rect(), self.GUTTER_BG)
        painter.setPen(self.GUTTER_BORDER)
        painter.drawLine(w - 1, event.rect().top(), w - 1, event.rect().bottom())

        block     = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top       = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom    = top + int(self.blockBoundingRect(block).height())
        current   = self.textCursor().blockNumber()
        line_h    = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                is_cur = (block_num == current)
                if is_cur:
                    painter.fillRect(0, top, w - 1, line_h, self.GUTTER_ACTIVE_BG)
                    painter.setPen(self.LINE_NUM_ACTIVE)
                    f = painter.font(); f.setBold(True); painter.setFont(f)
                else:
                    painter.setPen(self.LINE_NUM_COLOR)
                    f = painter.font(); f.setBold(False); painter.setFont(f)
                painter.drawText(
                    0, top, w - 8, line_h,
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    str(block_num + 1),
                )
            block     = block.next()
            top       = bottom
            bottom    = top + int(self.blockBoundingRect(block).height())
            block_num += 1

    # ── Línea actual ─────────────────────────────────────────────

    def highlightCurrentLine(self):
        selections = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(self.CURRENT_LINE_BG)
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            selections.append(sel)
        self.setExtraSelections(selections)

    # ── Modificación ─────────────────────────────────────────────

    def _on_contents_changed(self):
        if not self._modified:
            self._modified = True
            self.file_modified.emit()

    def mark_saved(self):
        self._modified = False

    # ── Atajos de teclado profesionales ──────────────────────────

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        Ctrl  = Qt.KeyboardModifier.ControlModifier
        Alt   = Qt.KeyboardModifier.AltModifier
        Shift = Qt.KeyboardModifier.ShiftModifier
        No    = Qt.KeyboardModifier.NoModifier

        # Ctrl+D — duplicar línea
        if key == Qt.Key.Key_D and mod == Ctrl:
            self._duplicate_line(); return

        # Ctrl+/ — comentar / descomentar
        if key == Qt.Key.Key_Slash and mod == Ctrl:
            self._toggle_comment(); return

        # Ctrl+Shift+K — eliminar línea
        if key == Qt.Key.Key_K and mod == (Ctrl | Shift):
            self._delete_line(); return

        # Alt+↑ — mover línea arriba
        if key == Qt.Key.Key_Up and mod == Alt:
            self._move_line(-1); return

        # Alt+↓ — mover línea abajo
        if key == Qt.Key.Key_Down and mod == Alt:
            self._move_line(1); return

        # Tab → 4 espacios (si no hay selección)
        if key == Qt.Key.Key_Tab and mod == No:
            cur = self.textCursor()
            if cur.hasSelection():
                self._indent_selection(1)
            else:
                cur.insertText("    ")
            return

        # Shift+Tab → des-indentar
        if key == Qt.Key.Key_Backtab:
            self._indent_selection(-1); return

        # Auto-cierre de brackets
        _PAIRS = {
            Qt.Key.Key_BraceLeft:   ("{", "}"),
            Qt.Key.Key_ParenLeft:   ("(", ")"),
            Qt.Key.Key_BracketLeft: ("[", "]"),
        }
        if key in _PAIRS and mod == No:
            self._auto_close(*_PAIRS[key]); return

        # Auto-cierre de comillas dobles
        if key == Qt.Key.Key_QuoteDbl and mod == No:
            self._auto_close('"', '"'); return

        # Enter inteligente (mantiene indentación)
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and mod == No:
            self._smart_enter(); return

        super().keyPressEvent(event)

    # ── Acciones de edición ──────────────────────────────────────

    def _duplicate_line(self):
        cur = self.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cur.movePosition(QTextCursor.MoveOperation.EndOfLine,
                         QTextCursor.MoveMode.KeepAnchor)
        text = cur.selectedText()
        cur.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cur.insertText("\n" + text)
        self.setTextCursor(cur)

    def _toggle_comment(self):
        cur = self.textCursor()
        if cur.hasSelection():
            start = cur.selectionStart()
            end   = cur.selectionEnd()
            cur.setPosition(start)
            cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cur.movePosition(QTextCursor.MoveOperation.EndOfLine,
                             QTextCursor.MoveMode.KeepAnchor)
        else:
            cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cur.movePosition(QTextCursor.MoveOperation.EndOfLine,
                             QTextCursor.MoveMode.KeepAnchor)

        text  = cur.selectedText()
        lines = text.split(" ")   # Qt usa U+2029 como separador de párrafo
        first = lines[0].lstrip()
        if first.startswith("//"):
            new_lines = [ln.replace("// ", "", 1).replace("//", "", 1)
                         for ln in lines]
        else:
            new_lines = ["// " + ln for ln in lines]
        cur.insertText(" ".join(new_lines))

    def _delete_line(self):
        cur = self.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cur.movePosition(QTextCursor.MoveOperation.EndOfLine,
                         QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()
        cur.deleteChar()   # borra el salto de línea
        self.setTextCursor(cur)

    def _move_line(self, direction: int):
        cur = self.textCursor()
        doc = self.document()
        block = cur.block()

        if direction == -1 and block.blockNumber() == 0:
            return
        if direction == 1 and block.blockNumber() == doc.blockCount() - 1:
            return

        text = block.text()
        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cur.movePosition(QTextCursor.MoveOperation.EndOfLine,
                         QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()
        cur.deleteChar()  # quitar salto de línea de esta posición

        if direction == -1:
            cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cur.insertText(text + "\n")
            cur.movePosition(QTextCursor.MoveOperation.Up)
        else:
            cur.movePosition(QTextCursor.MoveOperation.EndOfLine)
            cur.insertText("\n" + text)

        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        self.setTextCursor(cur)

    def _indent_selection(self, direction: int):
        cur = self.textCursor()
        if not cur.hasSelection():
            return
        start = cur.selectionStart()
        end   = cur.selectionEnd()
        cur.setPosition(start)
        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cur.movePosition(QTextCursor.MoveOperation.EndOfLine,
                         QTextCursor.MoveMode.KeepAnchor)
        text  = cur.selectedText()
        lines = text.split(" ")
        if direction == 1:
            new_lines = ["    " + ln for ln in lines]
        else:
            new_lines = [ln[4:] if ln.startswith("    ") else ln.lstrip("\t")
                         for ln in lines]
        cur.insertText(" ".join(new_lines))

    def _auto_close(self, open_: str, close_: str):
        cur = self.textCursor()
        if cur.hasSelection():
            text = cur.selectedText()
            cur.insertText(open_ + text + close_)
        else:
            cur.insertText(open_ + close_)
            cur.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cur)

    def _smart_enter(self):
        cur = self.textCursor()
        line    = cur.block().text()
        indent  = len(line) - len(line.lstrip())
        stripped = line.rstrip()
        extra = "    " if stripped.endswith(("{", "(", ":")) else ""
        cur.insertText("\n" + " " * indent + extra)
        self.setTextCursor(cur)
        self.ensureCursorVisible()

    # ── Zoom con Ctrl+rueda ──────────────────────────────────────

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoomIn(2)
            else:
                self.zoomOut(2)
        else:
            super().wheelEvent(event)

    # ── Menú contextual ──────────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#1e1e1e; color:#ccc; border:1px solid #3a3a3a;
                    padding:4px 0; border-radius:6px; }
            QMenu::item { padding:6px 28px 6px 16px; font-size:9.5pt; }
            QMenu::item:selected { background:#094771; color:#fff; }
            QMenu::separator { height:1px; background:#2a2a2a; margin:4px 8px; }
        """)

        def _a(label, shortcut, slot, enabled=True):
            a = QAction(label, self)
            if shortcut:
                a.setShortcut(QKeySequence(shortcut))
            a.triggered.connect(slot)
            a.setEnabled(enabled)
            menu.addAction(a)
            return a

        has_sel = self.textCursor().hasSelection()
        _a("Cortar",             "Ctrl+X",       self.cut,      has_sel)
        _a("Copiar",             "Ctrl+C",       self.copy,     has_sel)
        _a("Pegar",              "Ctrl+V",       self.paste)
        menu.addSeparator()
        _a("Deshacer",           "Ctrl+Z",       self.undo,
           self.document().isUndoAvailable())
        _a("Rehacer",            "Ctrl+Y",       self.redo,
           self.document().isRedoAvailable())
        menu.addSeparator()
        _a("Duplicar línea",     "Ctrl+D",       self._duplicate_line)
        _a("Comentar / desc.",   "Ctrl+/",       self._toggle_comment)
        _a("Eliminar línea",     "Ctrl+Shift+K", self._delete_line)
        menu.addSeparator()
        _a("Mover línea arriba", "Alt+↑",        lambda: self._move_line(-1))
        _a("Mover línea abajo",  "Alt+↓",        lambda: self._move_line(1))
        menu.addSeparator()
        _a("Seleccionar todo",   "Ctrl+A",       self.selectAll)
        menu.addSeparator()
        _a("Zoom +",  "Ctrl++",  lambda: self.zoomIn(2))
        _a("Zoom -",  "Ctrl+-",  lambda: self.zoomOut(2))

        menu.exec(event.globalPos())

    # ── Drag & Drop de archivos ──────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            # Delegar al MainWindow para abrir los archivos
            urls = event.mimeData().urls()
            parent = self.window()
            if hasattr(parent, "open_file"):
                for url in urls:
                    path = url.toLocalFile()
                    if path:
                        parent.open_file(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
