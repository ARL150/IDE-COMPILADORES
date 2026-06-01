# ui/themes.py
# ThemeManager — aplica temas completos a toda la aplicación.

from PyQt6.QtWidgets import QApplication

# ══════════════════════════════════════════════════════════════
#  DARK PROFESSIONAL  (#007acc accent — VS Code style)
# ══════════════════════════════════════════════════════════════
_DARK_PRO = """
* { outline: none; }

/* ── Base ── */
QMainWindow, QWidget { background: #1e1e1e; color: #cccccc;
    font-family: 'Segoe UI', 'SF Pro Text', Arial, sans-serif; font-size: 10pt; }

/* ── Splitter ── */
QSplitter::handle { background: #2d2d2d; }
QSplitter#MainSplitter::handle { background: #333; width: 3px; }
QSplitter#MainSplitter::handle:hover { background: #007acc; }

/* ── Panel headers ── */
QWidget#PanelHeader {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2d2d2d,stop:1 #252526);
    border-bottom: 2px solid #007acc;
}
QLabel#PanelTitle {
    color: #9d9d9d; font-size: 9.5pt; font-weight: bold; letter-spacing: 2px;
}
QLabel#FileLabel { color: #569cd6; font-size: 9pt; }

/* ── Menu bar ── */
QMenuBar { background: #333; color: #ccc; border-bottom: 1px solid #252526; padding: 1px 4px; }
QMenuBar::item { padding: 4px 10px; border-radius: 3px; }
QMenuBar::item:selected { background: #094771; }
QMenu { background: #252526; color: #ccc; border: 1px solid #454545; padding: 4px 0; }
QMenu::item { padding: 5px 24px 5px 14px; }
QMenu::item:selected { background: #094771; }
QMenu::separator { height: 1px; background: #3d3d3d; margin: 4px 8px; }

/* ── Toolbar ── */
QToolBar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2d2d2d,stop:1 #252526);
    border-bottom: 1px solid #1e1e1e;
    spacing: 2px; padding: 3px 8px;
}
QToolBar QLabel { color: #666; font-size: 8.5pt; font-weight: bold;
    letter-spacing: 1px; padding: 0 6px; text-transform: uppercase; }
QToolBar::separator { background: #444; width: 1px; margin: 5px 6px; }

QToolButton {
    color: #ccc; background: transparent;
    border: 1px solid transparent; border-radius: 5px;
    padding: 5px 10px; font-size: 9.5pt; min-width: 30px;
}
QToolButton:hover { background: #3e3e42; border-color: #555; color: white; }
QToolButton:pressed { background: #094771; border-color: #007acc; }

QToolButton[role="primary"] {
    background: #0e639c; color: white; border-color: #0e639c; font-weight: bold;
}
QToolButton[role="primary"]:hover { background: #1177bb; border-color: #1177bb; }
QToolButton[role="primary"]:pressed { background: #094771; }

QToolButton[role="success"] {
    background: #167a3b; color: #4ec9b0; border-color: #1d9a4c; font-weight: bold;
}
QToolButton[role="success"]:hover { background: #1d9a4c; color: white; }

QToolButton[role="danger"] {
    color: #f48771; border-color: transparent;
}
QToolButton[role="danger"]:hover { background: #3a1e1e; border-color: #f48771; }

/* ── Editor tabs (multiple open files) ── */
QTabWidget#EditorTabs::pane { border: none; background: #1e1e1e; }
QTabWidget#EditorTabs QTabBar { background: #252526; }
QTabWidget#EditorTabs QTabBar::tab {
    background: #2d2d2d; color: #9d9d9d;
    padding: 6px 16px; border: none; border-right: 1px solid #1e1e1e;
    min-width: 80px; max-width: 180px;
}
QTabWidget#EditorTabs QTabBar::tab:selected {
    background: #1e1e1e; color: #fff; border-top: 2px solid #007acc;
}
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background: #37373d; color: #ccc; }
QTabWidget#EditorTabs QTabBar::tab:first { border-left: none; }

/* ── Result tabs ── */
QTabWidget#ResultTabs::pane { border: none; background: #1e1e1e; }
QTabWidget#ResultTabs QTabBar { background: #252526; }
QTabWidget#ResultTabs QTabBar::tab {
    background: #252526; color: #888;
    padding: 8px 14px; border: none; border-right: 1px solid #333;
    font-size: 9pt; min-width: 70px;
}
QTabWidget#ResultTabs QTabBar::tab:selected {
    background: #1e1e1e; color: #4ec9b0; border-top: 2px solid #4ec9b0; font-weight: bold;
}
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background: #2a2a2a; color: #bbb; }

/* ── Lex table ── */
QTableWidget#LexTable {
    background: #1e1e1e; color: #cccccc;
    gridline-color: #2a2a2a; border: none;
    alternate-background-color: #252526;
    selection-background-color: #094771;
    font-family: Consolas, 'Courier New', monospace; font-size: 10pt;
}
QTableWidget#LexTable::item { padding: 3px 8px; border: none; }
QTableWidget#LexTable QHeaderView::section {
    background: #252526; color: #9d9d9d;
    padding: 7px 8px; border: none;
    border-right: 1px solid #333; border-bottom: 2px solid #007acc;
    font-weight: bold; font-size: 9.5pt;
}

/* ── Error table ── */
QTableWidget#ErrorTable {
    background: #1a0e0e; color: #f48771;
    gridline-color: #2a1a1a; border: none;
    alternate-background-color: #1e1010;
    selection-background-color: #5a1a1a;
    font-family: Consolas, 'Courier New', monospace; font-size: 10pt;
}
QTableWidget#ErrorTable::item { padding: 3px 8px; border: none; }
QTableWidget#ErrorTable QHeaderView::section {
    background: #252526; color: #9d9d9d;
    padding: 7px 8px; border: none;
    border-right: 1px solid #333; border-bottom: 2px solid #f48771;
    font-weight: bold; font-size: 9.5pt;
}

/* ── Generic header ── */
QHeaderView::section {
    background: #252526; color: #9d9d9d;
    padding: 6px 8px; border: none;
    border-right: 1px solid #333; border-bottom: 2px solid #007acc;
    font-weight: bold; font-family: 'Segoe UI', Arial, sans-serif;
}

/* ── Plain text (sintáctico output) ── */
QPlainTextEdit {
    background: #1e1e1e; color: #cccccc; border: none;
    selection-background-color: #264f78;
    font-family: Consolas, monospace; font-size: 10pt; padding: 6px;
}
QPlainTextEdit#SynText { background: #1a1a2e; color: #d4d4d4; }

/* ── Console ── */
QTextEdit#CompilerConsole {
    background: #0d0d0d; color: #cccccc; border: none;
    font-family: Consolas, 'Courier New', monospace; font-size: 10pt; padding: 10px;
}

/* ── AST Tree ── */
QTreeWidget {
    background: #1e1e1e; color: #cccccc; border: none;
    alternate-background-color: #252526;
    font-family: Consolas, monospace; font-size: 10pt;
}
QTreeWidget::item { padding: 3px 4px; }
QTreeWidget::item:selected { background: #094771; color: white; }
QTreeWidget::item:hover { background: #2a2d2e; }
QTreeWidget::branch { background: #1e1e1e; }
QTreeWidget QHeaderView::section {
    background: #252526; color: #9d9d9d; padding: 6px 8px;
    border: none; border-right: 1px solid #333; border-bottom: 2px solid #4ec9b0;
    font-weight: bold;
}

/* ── Empty state ── */
QWidget#EmptyState { background: transparent; }
QLabel#EmptyIcon { color: #2d2d2d; font-size: 52px; }
QLabel#EmptyTitle { color: #444; font-size: 15px; font-weight: bold; margin-top: 8px; }
QLabel#EmptySub { color: #383838; font-size: 10px; margin-top: 4px; }

/* ── Status bar ── */
QStatusBar {
    background: #007acc; color: white; font-size: 9pt; padding: 1px 8px;
}
QStatusBar::item { border: none; }
QStatusBar QLabel { color: white; padding: 1px 8px; }
QLabel#StatusIndicator { font-weight: bold; font-size: 9pt; }

/* ── Scrollbars ── */
QScrollBar:vertical { background: #1e1e1e; width: 10px; margin: 0; border: none; }
QScrollBar::handle:vertical { background: #3d3d3d; min-height: 20px; border-radius: 5px; margin: 1px; }
QScrollBar::handle:vertical:hover { background: #555; }
QScrollBar:horizontal { background: #1e1e1e; height: 10px; margin: 0; border: none; }
QScrollBar::handle:horizontal { background: #3d3d3d; min-width: 20px; border-radius: 5px; margin: 1px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }

/* ── Buttons / dialogs ── */
QPushButton { background: #0e639c; color: white; border: none; padding: 6px 14px; border-radius: 4px; }
QPushButton:hover { background: #1177bb; }
QPushButton:pressed { background: #094771; }
QPushButton:disabled { background: #3d3d3d; color: #666; }
QLineEdit { background: #3c3c3c; color: #ccc; border: 1px solid #555; padding: 4px 8px; border-radius: 3px; }
QLineEdit:focus { border-color: #007acc; }
QDialog { background: #252526; color: #ccc; }
QMessageBox { background: #252526; color: #ccc; }
"""

# ══════════════════════════════════════════════════════════════
#  LIGHT PROFESSIONAL  (#0078d4 accent — Microsoft Fluent)
# ══════════════════════════════════════════════════════════════
_LIGHT_PRO = """
* { outline: none; }

QMainWindow, QWidget { background: #f0f0f0; color: #1e1e1e;
    font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; }

QSplitter#MainSplitter::handle { background: #c8c8c8; width: 3px; }
QSplitter#MainSplitter::handle:hover { background: #0078d4; }

QWidget#PanelHeader {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #e8e8e8,stop:1 #dedede);
    border-bottom: 2px solid #0078d4;
}
QLabel#PanelTitle { color: #555; font-size: 9.5pt; font-weight: bold; letter-spacing: 2px; }
QLabel#FileLabel { color: #0078d4; font-size: 9pt; }

QMenuBar { background: #e4e4e4; color: #1e1e1e; border-bottom: 1px solid #ccc; padding: 1px 4px; }
QMenuBar::item { padding: 4px 10px; border-radius: 3px; }
QMenuBar::item:selected { background: #cce5ff; color: #0a4d8c; }
QMenu { background: #fff; color: #1e1e1e; border: 1px solid #ccc; padding: 4px 0; }
QMenu::item { padding: 5px 24px 5px 14px; }
QMenu::item:selected { background: #cce5ff; }
QMenu::separator { height: 1px; background: #e0e0e0; margin: 4px 8px; }

QToolBar { background: #e4e4e4; border-bottom: 1px solid #ccc; spacing: 2px; padding: 3px 8px; }
QToolBar QLabel { color: #888; font-size: 8.5pt; font-weight: bold; letter-spacing: 1px; padding: 0 6px; }
QToolBar::separator { background: #ccc; width: 1px; margin: 5px 6px; }
QToolButton { color: #1e1e1e; background: transparent; border: 1px solid transparent; border-radius: 5px; padding: 5px 10px; font-size: 9.5pt; min-width: 30px; }
QToolButton:hover { background: #d4d4d4; border-color: #bbb; }
QToolButton:pressed { background: #cce5ff; border-color: #0078d4; }
QToolButton[role="primary"] { background: #0078d4; color: white; border-color: #0078d4; font-weight: bold; }
QToolButton[role="primary"]:hover { background: #106ebe; border-color: #106ebe; }
QToolButton[role="success"] { background: #107c10; color: white; border-color: #107c10; font-weight: bold; }
QToolButton[role="success"]:hover { background: #0e6a0e; }
QToolButton[role="danger"] { color: #c0392b; border-color: transparent; }
QToolButton[role="danger"]:hover { background: #fde8e8; border-color: #c0392b; }

QTabWidget#EditorTabs::pane { border: none; background: #fff; }
QTabWidget#EditorTabs QTabBar { background: #e4e4e4; }
QTabWidget#EditorTabs QTabBar::tab { background: #dedede; color: #666; padding: 6px 16px; border: none; border-right: 1px solid #ccc; min-width: 80px; max-width: 180px; }
QTabWidget#EditorTabs QTabBar::tab:selected { background: #fff; color: #1e1e1e; border-top: 2px solid #0078d4; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background: #d0d0d0; }

QTabWidget#ResultTabs::pane { border: none; background: #fff; }
QTabWidget#ResultTabs QTabBar { background: #e4e4e4; }
QTabWidget#ResultTabs QTabBar::tab { background: #e4e4e4; color: #666; padding: 8px 14px; border: none; border-right: 1px solid #ccc; font-size: 9pt; min-width: 70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background: #fff; color: #0078d4; border-top: 2px solid #0078d4; font-weight: bold; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background: #d8d8d8; }

QTableWidget#LexTable { background: #fff; color: #1e1e1e; gridline-color: #eee; border: none; alternate-background-color: #f7f7f7; selection-background-color: #cce5ff; font-family: Consolas, monospace; font-size: 10pt; }
QTableWidget#LexTable::item { padding: 3px 8px; }
QTableWidget#LexTable QHeaderView::section { background: #e4e4e4; color: #444; padding: 7px 8px; border: none; border-right: 1px solid #ccc; border-bottom: 2px solid #0078d4; font-weight: bold; }

QTableWidget#ErrorTable { background: #fff8f8; color: #c0392b; gridline-color: #f0dede; border: none; alternate-background-color: #fdf2f2; selection-background-color: #fddede; font-family: Consolas, monospace; font-size: 10pt; }
QTableWidget#ErrorTable::item { padding: 3px 8px; }
QTableWidget#ErrorTable QHeaderView::section { background: #e4e4e4; color: #444; padding: 7px 8px; border: none; border-right: 1px solid #ccc; border-bottom: 2px solid #c0392b; font-weight: bold; }

QHeaderView::section { background: #e4e4e4; color: #444; padding: 6px 8px; border: none; border-right: 1px solid #ccc; border-bottom: 2px solid #0078d4; font-weight: bold; }

QPlainTextEdit { background: #fff; color: #1e1e1e; border: none; selection-background-color: #cce5ff; font-family: Consolas, monospace; font-size: 10pt; padding: 6px; }
QPlainTextEdit#SynText { background: #f0f8ff; }
QTextEdit#CompilerConsole { background: #1a1a1a; color: #ccc; border: none; font-family: Consolas, monospace; font-size: 10pt; padding: 10px; }

QTreeWidget { background: #fff; color: #1e1e1e; border: none; alternate-background-color: #f7f7f7; font-family: Consolas, monospace; font-size: 10pt; }
QTreeWidget::item { padding: 3px 4px; }
QTreeWidget::item:selected { background: #cce5ff; color: #1e1e1e; }
QTreeWidget::item:hover { background: #e8f4ff; }
QTreeWidget QHeaderView::section { background: #e4e4e4; color: #444; border: none; border-right: 1px solid #ccc; border-bottom: 2px solid #0078d4; padding: 6px 8px; font-weight: bold; }

QWidget#EmptyState { background: transparent; }
QLabel#EmptyIcon { color: #d0d0d0; font-size: 52px; }
QLabel#EmptyTitle { color: #aaa; font-size: 15px; font-weight: bold; margin-top: 8px; }
QLabel#EmptySub { color: #bbb; font-size: 10px; margin-top: 4px; }

QStatusBar { background: #0078d4; color: white; font-size: 9pt; padding: 1px 8px; }
QStatusBar::item { border: none; }
QStatusBar QLabel { color: white; padding: 1px 8px; }
QLabel#StatusIndicator { font-weight: bold; }

QScrollBar:vertical { background: #f0f0f0; width: 10px; margin: 0; border: none; }
QScrollBar::handle:vertical { background: #c0c0c0; min-height: 20px; border-radius: 5px; margin: 1px; }
QScrollBar::handle:vertical:hover { background: #a0a0a0; }
QScrollBar:horizontal { background: #f0f0f0; height: 10px; margin: 0; border: none; }
QScrollBar::handle:horizontal { background: #c0c0c0; min-width: 20px; border-radius: 5px; margin: 1px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }

QPushButton { background: #0078d4; color: white; border: none; padding: 6px 14px; border-radius: 4px; }
QPushButton:hover { background: #106ebe; }
QPushButton:pressed { background: #005a9e; }
QPushButton:disabled { background: #ddd; color: #888; }
QLineEdit { background: #fff; color: #1e1e1e; border: 1px solid #bbb; padding: 4px 8px; border-radius: 3px; }
QLineEdit:focus { border-color: #0078d4; }
QDialog { background: #f0f0f0; color: #1e1e1e; }
QMessageBox { background: #f0f0f0; color: #1e1e1e; }
"""

# ══════════════════════════════════════════════════════════════
#  CYBER BLUE  (#00b4d8 accent — dark cyber aesthetic)
# ══════════════════════════════════════════════════════════════
_CYBER_BLUE = """
* { outline: none; }

QMainWindow, QWidget { background: #07101e; color: #7ab8d4;
    font-family: Consolas, 'Courier New', monospace; font-size: 10pt; }

QSplitter#MainSplitter::handle { background: #0d2a4a; width: 3px; }
QSplitter#MainSplitter::handle:hover { background: #00b4d8; }

QWidget#PanelHeader {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #0d1e38,stop:1 #0a1628);
    border-bottom: 2px solid #00b4d8;
}
QLabel#PanelTitle { color: #00b4d8; font-size: 9.5pt; font-weight: bold; letter-spacing: 3px; }
QLabel#FileLabel { color: #48cae4; font-size: 9pt; }

QMenuBar { background: #0a1628; color: #7ab8d4; border-bottom: 1px solid #0d2a4a; padding: 1px 4px; }
QMenuBar::item { padding: 4px 10px; border-radius: 3px; }
QMenuBar::item:selected { background: #0a4a6e; color: #00b4d8; }
QMenu { background: #0c1e38; color: #7ab8d4; border: 1px solid #0d2a4a; padding: 4px 0; }
QMenu::item { padding: 5px 24px 5px 14px; }
QMenu::item:selected { background: #0a4a6e; color: #00b4d8; }
QMenu::separator { height: 1px; background: #0d2a4a; margin: 4px 8px; }

QToolBar { background: #0a1628; border-bottom: 1px solid #0d2a4a; spacing: 2px; padding: 3px 8px; }
QToolBar QLabel { color: #1a4a6a; font-size: 8.5pt; font-weight: bold; letter-spacing: 1px; padding: 0 6px; }
QToolBar::separator { background: #0d2a4a; width: 1px; margin: 5px 6px; }
QToolButton { color: #7ab8d4; background: transparent; border: 1px solid transparent; border-radius: 5px; padding: 5px 10px; font-size: 9.5pt; min-width: 30px; }
QToolButton:hover { background: #0a2a4a; border-color: #00b4d8; color: #00b4d8; }
QToolButton:pressed { background: #0a4a6e; }
QToolButton[role="primary"] { background: #00476e; color: #00b4d8; border: 1px solid #00b4d8; font-weight: bold; }
QToolButton[role="primary"]:hover { background: #0a5a7e; color: #48cae4; }
QToolButton[role="success"] { background: #004d30; color: #00f5d4; border: 1px solid #00f5d4; font-weight: bold; }
QToolButton[role="success"]:hover { background: #006040; }
QToolButton[role="danger"] { color: #e57373; border-color: transparent; }
QToolButton[role="danger"]:hover { background: #1a0a0a; border-color: #e57373; }

QTabWidget#EditorTabs::pane { border: none; background: #07101e; }
QTabWidget#EditorTabs QTabBar { background: #0a1628; }
QTabWidget#EditorTabs QTabBar::tab { background: #0c1e38; color: #4a7a9a; padding: 6px 16px; border: none; border-right: 1px solid #0d2a4a; min-width: 80px; max-width: 180px; }
QTabWidget#EditorTabs QTabBar::tab:selected { background: #07101e; color: #00b4d8; border-top: 2px solid #00b4d8; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background: #0a1e38; color: #6a9ab4; }

QTabWidget#ResultTabs::pane { border: none; background: #07101e; }
QTabWidget#ResultTabs QTabBar { background: #0a1628; }
QTabWidget#ResultTabs QTabBar::tab { background: #0a1628; color: #4a7a9a; padding: 8px 14px; border: none; border-right: 1px solid #0d2a4a; font-size: 9pt; min-width: 70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background: #07101e; color: #00b4d8; border-top: 2px solid #00b4d8; font-weight: bold; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background: #0a1e38; color: #6a9ab4; }

QTableWidget#LexTable { background: #07101e; color: #7ab8d4; gridline-color: #0d2a4a; border: none; alternate-background-color: #0c1e38; selection-background-color: #0a4a6e; font-family: Consolas, monospace; font-size: 10pt; }
QTableWidget#LexTable::item { padding: 3px 8px; }
QTableWidget#LexTable QHeaderView::section { background: #0a1628; color: #4a7a9a; padding: 7px 8px; border: none; border-right: 1px solid #0d2a4a; border-bottom: 2px solid #00b4d8; font-weight: bold; }

QTableWidget#ErrorTable { background: #0e0a0a; color: #e57373; gridline-color: #2a0d0d; border: none; alternate-background-color: #120c0c; selection-background-color: #3a0a0a; font-family: Consolas, monospace; font-size: 10pt; }
QTableWidget#ErrorTable::item { padding: 3px 8px; }
QTableWidget#ErrorTable QHeaderView::section { background: #0a1628; color: #4a7a9a; padding: 7px 8px; border: none; border-right: 1px solid #0d2a4a; border-bottom: 2px solid #e57373; font-weight: bold; }

QHeaderView::section { background: #0a1628; color: #4a7a9a; padding: 6px 8px; border: none; border-right: 1px solid #0d2a4a; border-bottom: 2px solid #00b4d8; font-weight: bold; }

QPlainTextEdit { background: #07101e; color: #7ab8d4; border: none; selection-background-color: #0a4a6e; font-family: Consolas, monospace; font-size: 10pt; padding: 6px; }
QPlainTextEdit#SynText { background: #060d1a; color: #8ab8d4; }
QTextEdit#CompilerConsole { background: #030811; color: #7ab8d4; border: none; font-family: Consolas, monospace; font-size: 10pt; padding: 10px; }

QTreeWidget { background: #07101e; color: #7ab8d4; border: none; alternate-background-color: #0c1e38; font-family: Consolas, monospace; font-size: 10pt; }
QTreeWidget::item { padding: 3px 4px; }
QTreeWidget::item:selected { background: #0a4a6e; color: #00b4d8; }
QTreeWidget::item:hover { background: #0a2a4a; }
QTreeWidget::branch { background: #07101e; }
QTreeWidget QHeaderView::section { background: #0a1628; color: #4a7a9a; border: none; border-right: 1px solid #0d2a4a; border-bottom: 2px solid #00b4d8; padding: 6px 8px; font-weight: bold; }

QWidget#EmptyState { background: transparent; }
QLabel#EmptyIcon { color: #0d2a4a; font-size: 52px; }
QLabel#EmptyTitle { color: #1a4a6a; font-size: 15px; font-weight: bold; margin-top: 8px; }
QLabel#EmptySub { color: #1a3a5a; font-size: 10px; margin-top: 4px; }

QStatusBar { background: #00476e; color: #00b4d8; font-size: 9pt; padding: 1px 8px; border-top: 1px solid #00b4d8; }
QStatusBar::item { border: none; }
QStatusBar QLabel { color: #00b4d8; padding: 1px 8px; }
QLabel#StatusIndicator { font-weight: bold; color: #48cae4; }

QScrollBar:vertical { background: #07101e; width: 10px; margin: 0; border: none; }
QScrollBar::handle:vertical { background: #0d2a4a; min-height: 20px; border-radius: 5px; margin: 1px; }
QScrollBar::handle:vertical:hover { background: #00b4d8; }
QScrollBar:horizontal { background: #07101e; height: 10px; margin: 0; border: none; }
QScrollBar::handle:horizontal { background: #0d2a4a; min-width: 20px; border-radius: 5px; margin: 1px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }

QPushButton { background: #00476e; color: #00b4d8; border: 1px solid #00b4d8; padding: 6px 14px; border-radius: 4px; }
QPushButton:hover { background: #0a5a7e; color: #48cae4; }
QPushButton:pressed { background: #0a4a6e; }
QPushButton:disabled { background: #0a1628; color: #1a4a6a; border-color: #0d2a4a; }
QLineEdit { background: #0c1e38; color: #7ab8d4; border: 1px solid #0d2a4a; padding: 4px 8px; border-radius: 3px; }
QLineEdit:focus { border-color: #00b4d8; }
QDialog { background: #0c1e38; color: #7ab8d4; }
QMessageBox { background: #0c1e38; color: #7ab8d4; }
"""


# ══════════════════════════════════════════════════════════════
#  Temas clásicos (versión compacta que sólo ajusta los colores
#  principales — heredan el resto del tema base)
# ══════════════════════════════════════════════════════════════

def _classic(bg, panel, text, accent, tab_sel, tab_sel_txt="white",
             menu_bg=None, edit_bg=None):
    """Genera un tema clásico de 1 acento."""
    mb  = menu_bg  or panel
    eb  = edit_bg  or bg
    return f"""
* {{ outline: none; }}
QMainWindow, QWidget {{ background: {bg}; color: {text};
    font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; }}
QSplitter#MainSplitter::handle {{ background: {panel}; width: 3px; }}
QSplitter#MainSplitter::handle:hover {{ background: {accent}; }}
QWidget#PanelHeader {{ background: {panel}; border-bottom: 2px solid {accent}; }}
QLabel#PanelTitle {{ color: {text}; font-size: 9.5pt; font-weight: bold; letter-spacing: 1px; opacity: 0.7; }}
QMenuBar {{ background: {mb}; color: {text}; border-bottom: 1px solid {panel}; padding: 1px 4px; }}
QMenuBar::item:selected {{ background: {accent}; color: {tab_sel_txt}; }}
QMenu {{ background: {panel}; color: {text}; border: 1px solid {accent}; padding: 4px 0; }}
QMenu::item {{ padding: 5px 24px 5px 14px; }}
QMenu::item:selected {{ background: {accent}; color: {tab_sel_txt}; }}
QMenu::separator {{ height: 1px; background: {accent}; margin: 4px 8px; opacity: 0.3; }}
QToolBar {{ background: {panel}; border-bottom: 1px solid {bg}; spacing: 2px; padding: 3px 8px; }}
QToolBar QLabel {{ color: {text}; font-size: 8.5pt; font-weight: bold; letter-spacing: 1px; padding: 0 6px; opacity: 0.6; }}
QToolBar::separator {{ background: {text}; width: 1px; margin: 5px 6px; opacity: 0.2; }}
QToolButton {{ color: {text}; background: transparent; border: 1px solid transparent; border-radius: 4px; padding: 5px 10px; font-size: 9.5pt; min-width: 30px; }}
QToolButton:hover {{ background: {accent}; color: {tab_sel_txt}; border-color: {accent}; }}
QToolButton:pressed {{ opacity: 0.8; }}
QTabWidget#EditorTabs::pane {{ border: none; background: {bg}; }}
QTabWidget#EditorTabs QTabBar {{ background: {panel}; }}
QTabWidget#EditorTabs QTabBar::tab {{ background: {panel}; color: {text}; padding: 6px 16px; border: none; border-right: 1px solid {bg}; min-width: 80px; opacity: 0.7; }}
QTabWidget#EditorTabs QTabBar::tab:selected {{ background: {bg}; color: {tab_sel_txt}; border-top: 2px solid {accent}; opacity: 1; }}
QTabWidget#ResultTabs::pane {{ border: none; background: {bg}; }}
QTabWidget#ResultTabs QTabBar {{ background: {panel}; }}
QTabWidget#ResultTabs QTabBar::tab {{ background: {panel}; color: {text}; padding: 8px 14px; border: none; border-right: 1px solid {bg}; font-size: 9pt; min-width: 70px; opacity: 0.7; }}
QTabWidget#ResultTabs QTabBar::tab:selected {{ background: {bg}; color: {tab_sel}; border-top: 2px solid {tab_sel}; font-weight: bold; opacity: 1; }}
QTableWidget#LexTable {{ background: {eb}; color: {text}; gridline-color: {panel}; border: none; alternate-background-color: {panel}; selection-background-color: {accent}; font-family: Consolas, monospace; font-size: 10pt; }}
QTableWidget#LexTable QHeaderView::section {{ background: {panel}; color: {text}; padding: 6px 8px; border: none; border-bottom: 2px solid {accent}; font-weight: bold; }}
QTableWidget#ErrorTable {{ background: {eb}; color: #f48771; gridline-color: {panel}; border: none; alternate-background-color: {panel}; font-family: Consolas, monospace; font-size: 10pt; }}
QTableWidget#ErrorTable QHeaderView::section {{ background: {panel}; color: {text}; padding: 6px 8px; border: none; border-bottom: 2px solid #f48771; font-weight: bold; }}
QHeaderView::section {{ background: {panel}; color: {text}; padding: 6px 8px; border: none; border-bottom: 2px solid {accent}; font-weight: bold; }}
QPlainTextEdit {{ background: {eb}; color: {text}; border: none; font-family: Consolas, monospace; font-size: 10pt; padding: 6px; }}
QTextEdit#CompilerConsole {{ background: #0d0d0d; color: #cccccc; border: none; font-family: Consolas, monospace; font-size: 10pt; padding: 10px; }}
QTreeWidget {{ background: {eb}; color: {text}; border: none; alternate-background-color: {panel}; font-family: Consolas, monospace; font-size: 10pt; }}
QTreeWidget::item:selected {{ background: {accent}; color: {tab_sel_txt}; }}
QTreeWidget::item:hover {{ background: {panel}; }}
QTreeWidget QHeaderView::section {{ background: {panel}; color: {text}; border: none; border-bottom: 2px solid {accent}; padding: 5px 8px; font-weight: bold; }}
QWidget#EmptyState {{ background: transparent; }}
QStatusBar {{ background: {accent}; color: {tab_sel_txt}; font-size: 9pt; padding: 1px 8px; }}
QStatusBar::item {{ border: none; }}
QStatusBar QLabel {{ color: {tab_sel_txt}; padding: 1px 8px; }}
QScrollBar:vertical {{ background: {bg}; width: 10px; margin: 0; border: none; }}
QScrollBar::handle:vertical {{ background: {panel}; min-height: 20px; border-radius: 5px; margin: 1px; }}
QScrollBar:horizontal {{ background: {bg}; height: 10px; margin: 0; border: none; }}
QScrollBar::handle:horizontal {{ background: {panel}; min-width: 20px; border-radius: 5px; margin: 1px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QPushButton {{ background: {accent}; color: {tab_sel_txt}; border: none; padding: 6px 14px; border-radius: 4px; }}
QPushButton:hover {{ opacity: 0.85; }}
QLineEdit {{ background: {panel}; color: {text}; border: 1px solid {accent}; padding: 4px 8px; border-radius: 3px; }}
QDialog {{ background: {panel}; color: {text}; }}
QMessageBox {{ background: {panel}; color: {text}; }}
"""


_DRACULA    = _classic("#282a36", "#44475a", "#f8f8f2", "#bd93f9", "#bd93f9", "#282a36", "#21222c")
_OCEAN      = _classic("#0f172a", "#1e293b", "#e2e8f0", "#3b82f6", "#3b82f6", "white",   "#0f172a")
_SUNSET     = _classic("#2b1d1d", "#3a2a2a", "#ffe4d6", "#ff7b00", "#ff7b00", "black",   "#2b1d1d")
_FOREST     = _classic("#0d1f1a", "#13332b", "#d1fae5", "#10b981", "#10b981", "black",   "#0d1f1a")
_NEON       = _classic("#140021", "#1f0033", "#f5d0fe", "#c026d3", "#c026d3", "white",   "#140021")
_HACKER     = _classic("black",   "#001100", "#00ff00", "#00aa00", "#00aa00", "black",   "black", "black")


# ══════════════════════════════════════════════════════════════
#  ThemeManager
# ══════════════════════════════════════════════════════════════
class ThemeManager:
    """Aplica temas QSS completos a toda la aplicación."""

    _current = "dark_pro"

    _themes = {
        # Profesionales (completos)
        "dark_pro":   _DARK_PRO,
        "light_pro":  _LIGHT_PRO,
        "cyber_blue": _CYBER_BLUE,
        # Clásicos
        "dracula":    _DRACULA,
        "ocean":      _OCEAN,
        "sunset":     _SUNSET,
        "forest":     _FOREST,
        "neon":       _NEON,
        "hacker":     _HACKER,
    }

    _labels = {
        "dark_pro":   "Dark Professional",
        "light_pro":  "Light Professional",
        "cyber_blue": "Cyber Blue",
        "dracula":    "Dracula",
        "ocean":      "Ocean Blue",
        "sunset":     "Sunset",
        "forest":     "Forest",
        "neon":       "Neon Purple",
        "hacker":     "Hacker Classic",
    }

    @classmethod
    def apply(cls, key: str, app=None):
        if app is None:
            app = QApplication.instance()
        if app and key in cls._themes:
            cls._current = key
            app.setStyleSheet(cls._themes[key])

    @classmethod
    def current(cls) -> str:
        return cls._current

    @classmethod
    def label(cls, key: str) -> str:
        return cls._labels.get(key, key)

    @classmethod
    def all_keys(cls) -> list:
        return list(cls._themes.keys())
