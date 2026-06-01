# ui/themes.py
from PyQt6.QtWidgets import QApplication

# ─────────────────────────────────────────────────────────────
# Fragmento base compartido (scrollbars, tooltips, QDialog)
# ─────────────────────────────────────────────────────────────
_BASE = """
* { outline: none; }
QScrollBar:vertical   { background:transparent; width:8px;  margin:0; border:none; }
QScrollBar:horizontal { background:transparent; height:8px; margin:0; border:none; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { border-radius:4px; margin:2px; }
QScrollBar::handle:vertical   { min-height:24px; }
QScrollBar::handle:horizontal { min-width:24px;  }
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page { background:none; border:none; }
QToolTip { border:1px solid #555; padding:5px 10px; border-radius:5px; font-size:9pt; }
"""

# ─────────────────────────────────────────────────────────────
# Estilos compartidos para terminales de error y tokens
# ─────────────────────────────────────────────────────────────
_TERMINALS = """
QTextEdit#ErrorTerminal, QTextEdit#CompilerConsole,
QTextEdit#SyntaxTerminal, QTextEdit#TokenTerminal,
QTextEdit#ASTTableView, QTextBrowser#ASTTableView {
    background: #0d0d0d; color: #cccccc; border: none;
    font-family: 'Menlo','SF Mono','Consolas',monospace; font-size: 10pt; padding: 0px;
}
QTextBrowser#ASTTableView a { color: #4a6fa5; text-decoration: none; }
"""


# ══════════════════════════════════════════════════════════════
#  DARK PROFESSIONAL (VS Code Dark+)
# ══════════════════════════════════════════════════════════════
_DARK_PRO = _BASE + _TERMINALS + """
QMainWindow, QWidget { background:#1e1e1e; color:#cccccc;
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#424242; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#686868; }
QToolTip { background:#252526; color:#ccc; border-color:#454545; }

QSplitter#MainSplitter::handle { background:#2d2d2d; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#007acc; }

QWidget#PanelHeader { background:#252526; border-bottom:1px solid #1a1a1a; }
QLabel#PanelTitle { color:#666; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#1e1e1e; border-bottom:1px solid #2a2a2a; }
QLabel#BreadcrumbDir  { color:#555; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#444; font-size:10pt; }
QLabel#BreadcrumbFile { color:#cccccc; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#4ec9b0; font-size:8.5pt; font-weight:600;
    background:#0e2626; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#2d2d2d; color:#ccc; border-bottom:1px solid #1e1e1e; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#094771; color:#fff; }
QMenu { background:#252526; color:#ccc; border:1px solid #454545; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#094771; color:#fff; }
QMenu::separator { height:1px; background:#3d3d3d; margin:4px 8px; }

QToolBar { background:#2d2d2d; border-bottom:1px solid #1e1e1e; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#444; width:1px; margin:5px 8px; }
QToolButton { color:#bbb; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#3e3e42; border-color:#555; color:#fff; }
QToolButton:pressed { background:#094771; border-color:#007acc; }

QTabWidget#EditorTabs::pane { border:none; background:#1e1e1e; }
QTabWidget#EditorTabs QTabBar { background:#252526; }
QTabWidget#EditorTabs QTabBar::tab { background:#2d2d2d; color:#9d9d9d;
    padding:7px 16px 6px; border:none; border-right:1px solid #252526;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#1e1e1e; color:#fff; border-top:2px solid #007acc; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#37373d; color:#ccc; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }
QTabWidget#EditorTabs QTabBar::close-button:hover { background:#5a1d1d; }

QTabWidget#ResultTabs::pane { border:none; background:#1e1e1e; }
QTabWidget#ResultTabs QTabBar { background:#252526; }
QTabWidget#ResultTabs QTabBar::tab { background:#252526; color:#777;
    padding:7px 14px; border:none; border-right:1px solid #333; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#1e1e1e; color:#4ec9b0;
    border-top:2px solid #4ec9b0; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#2a2a2a; color:#bbb; }

QPlainTextEdit { background:#1e1e1e; color:#d4d4d4; border:none;
    selection-background-color:#264f78;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#1e1e1e; color:#cccccc; gridline-color:#2a2a2a; border:none;
    alternate-background-color:#252526; selection-background-color:#094771;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#1a1a1a; color:#666;
    padding:7px 8px; border:none; border-right:1px solid #333; border-bottom:2px solid #007acc;
    font-weight:700; font-size:8.5pt; letter-spacing:0.5px; }

QHeaderView::section { background:#252526; color:#666; padding:6px 8px; border:none;
    border-right:1px solid #333; border-bottom:2px solid #007acc; font-weight:700; }

QTreeWidget { background:#1e1e1e; color:#cccccc; border:none;
    alternate-background-color:#252526; font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#094771; color:#fff; }
QTreeWidget::item:hover { background:#2a2d2e; }
QTreeWidget QHeaderView::section { background:#1a1a1a; color:#666; padding:6px 8px;
    border:none; border-right:1px solid #333; border-bottom:2px solid #4ec9b0; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#222; font-size:44px; }
QLabel#EmptyTitle { color:#333; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#2a2a2a; font-size:9px; margin-top:4px; }

QStatusBar { background:#007acc; color:#fff; font-size:9pt; padding:0 6px; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#fff; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; }
QLabel#VenvLabel { background:#005f9e; color:#90e0ff; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#0e639c; color:#fff; border:none; padding:7px 18px;
    border-radius:4px; font-size:10pt; }
QPushButton:hover  { background:#1177bb; }
QPushButton:pressed { background:#094771; }
QPushButton:disabled { background:#3d3d3d; color:#666; }
QLineEdit { background:#3c3c3c; color:#ccc; border:1px solid #555; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#007acc; }
QDialog    { background:#252526; color:#ccc; }
QMessageBox { background:#252526; color:#ccc; }
"""

# ══════════════════════════════════════════════════════════════
#  PURE BLACK (OLED / Minimal oscuro)
# ══════════════════════════════════════════════════════════════
_PURE_BLACK = _BASE + _TERMINALS + """
QMainWindow, QWidget { background:#000000; color:#e0e0e0;
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#1a1a1a; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#2a2a2a; }
QToolTip { background:#111; color:#e0e0e0; border-color:#222; }

QSplitter#MainSplitter::handle { background:#111; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#fff; }

QWidget#PanelHeader { background:#000; border-bottom:1px solid #1a1a1a; }
QLabel#PanelTitle { color:#333; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#000; border-bottom:1px solid #1a1a1a; }
QLabel#BreadcrumbDir  { color:#333; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#2a2a2a; font-size:10pt; }
QLabel#BreadcrumbFile { color:#e0e0e0; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#22c55e; font-size:8.5pt; font-weight:600;
    background:#001800; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#0a0a0a; color:#ccc; border-bottom:1px solid #111; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#1a1a1a; color:#fff; }
QMenu { background:#0d0d0d; color:#ccc; border:1px solid #222; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#1a1a1a; color:#fff; }
QMenu::separator { height:1px; background:#1a1a1a; margin:4px 8px; }

QToolBar { background:#0a0a0a; border-bottom:1px solid #111; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#1a1a1a; width:1px; margin:5px 8px; }
QToolButton { color:#999; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#1a1a1a; border-color:#333; color:#fff; }
QToolButton:pressed { background:#222; }

QTabWidget#EditorTabs::pane { border:none; background:#000; }
QTabWidget#EditorTabs QTabBar { background:#0a0a0a; }
QTabWidget#EditorTabs QTabBar::tab { background:#0a0a0a; color:#555;
    padding:7px 16px 6px; border:none; border-right:1px solid #000;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#000; color:#fff; border-top:2px solid #fff; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#111; color:#aaa; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }

QTabWidget#ResultTabs::pane { border:none; background:#000; }
QTabWidget#ResultTabs QTabBar { background:#0a0a0a; }
QTabWidget#ResultTabs QTabBar::tab { background:#0a0a0a; color:#444;
    padding:7px 14px; border:none; border-right:1px solid #111; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#000; color:#e0e0e0;
    border-top:2px solid #fff; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#111; color:#888; }

QPlainTextEdit { background:#000; color:#d4d4d4; border:none;
    selection-background-color:#1a1a1a;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#000; color:#ccc; gridline-color:#111; border:none;
    alternate-background-color:#080808; selection-background-color:#1a1a1a;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#0a0a0a; color:#444;
    padding:7px 8px; border:none; border-right:1px solid #1a1a1a; border-bottom:2px solid #fff;
    font-weight:700; font-size:8.5pt; }
QHeaderView::section { background:#0a0a0a; color:#444; padding:6px 8px; border:none;
    border-right:1px solid #1a1a1a; border-bottom:2px solid #fff; font-weight:700; }

QTreeWidget { background:#000; color:#ccc; border:none; alternate-background-color:#080808;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#1a1a1a; color:#fff; }
QTreeWidget::item:hover { background:#111; }
QTreeWidget QHeaderView::section { background:#0a0a0a; color:#444; padding:6px 8px;
    border:none; border-right:1px solid #1a1a1a; border-bottom:2px solid #fff; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#111; font-size:44px; }
QLabel#EmptyTitle { color:#222; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#1a1a1a; font-size:9px; margin-top:4px; }

QStatusBar { background:#111; color:#888; font-size:9pt; padding:0 6px; border-top:1px solid #222; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#888; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; color:#fff; }
QLabel#VenvLabel { background:#001a00; color:#22c55e; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#1a1a1a; color:#fff; border:1px solid #333; padding:7px 18px;
    border-radius:4px; font-size:10pt; }
QPushButton:hover  { background:#222; border-color:#555; }
QPushButton:pressed { background:#333; }
QPushButton:disabled { background:#0a0a0a; color:#333; border-color:#1a1a1a; }
QLineEdit { background:#0a0a0a; color:#ccc; border:1px solid #222; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#fff; }
QDialog    { background:#0d0d0d; color:#ccc; }
QMessageBox { background:#0d0d0d; color:#ccc; }
"""

# ══════════════════════════════════════════════════════════════
#  PURE WHITE (Minimalista blanco)
# ══════════════════════════════════════════════════════════════
_PURE_WHITE = _BASE + """
QMainWindow, QWidget { background:#ffffff; color:#111111;
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#d0d0d0; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#aaaaaa; }
QToolTip { background:#fff; color:#111; border-color:#ddd; }

QSplitter#MainSplitter::handle { background:#e0e0e0; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#111; }

QWidget#PanelHeader { background:#f7f7f7; border-bottom:1px solid #ebebeb; }
QLabel#PanelTitle { color:#bbb; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#fff; border-bottom:1px solid #ebebeb; }
QLabel#BreadcrumbDir  { color:#bbb; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#ccc; font-size:10pt; }
QLabel#BreadcrumbFile { color:#111; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#16a34a; font-size:8.5pt; font-weight:600;
    background:#f0fdf4; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#f7f7f7; color:#111; border-bottom:1px solid #e0e0e0; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#efefef; color:#000; }
QMenu { background:#fff; color:#111; border:1px solid #ddd; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#f0f0f0; color:#000; }
QMenu::separator { height:1px; background:#e8e8e8; margin:4px 8px; }

QToolBar { background:#f7f7f7; border-bottom:1px solid #e0e0e0; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#e0e0e0; width:1px; margin:5px 8px; }
QToolButton { color:#444; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#ebebeb; border-color:#ccc; color:#000; }
QToolButton:pressed { background:#e0e0e0; }

QTabWidget#EditorTabs::pane { border:none; background:#fff; }
QTabWidget#EditorTabs QTabBar { background:#f7f7f7; }
QTabWidget#EditorTabs QTabBar::tab { background:#f0f0f0; color:#888;
    padding:7px 16px 6px; border:none; border-right:1px solid #e8e8e8;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#fff; color:#111; border-top:2px solid #111; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#e8e8e8; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }
QTabWidget#EditorTabs QTabBar::close-button:hover { background:#fde0e0; }

QTabWidget#ResultTabs::pane { border:none; background:#fff; }
QTabWidget#ResultTabs QTabBar { background:#f7f7f7; }
QTabWidget#ResultTabs QTabBar::tab { background:#f7f7f7; color:#999;
    padding:7px 14px; border:none; border-right:1px solid #ebebeb; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#fff; color:#111;
    border-top:2px solid #111; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#ececec; }

QTextEdit#ErrorTerminal, QTextEdit#CompilerConsole,
QTextEdit#SyntaxTerminal, QTextEdit#TokenTerminal {
    background:#0d0d0d; color:#cccccc; border:none;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:10pt; padding:8px; }

QPlainTextEdit { background:#fff; color:#111; border:none; selection-background-color:#b8d6f5;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#fff; color:#111; gridline-color:#eee; border:none;
    alternate-background-color:#fafafa; selection-background-color:#e8f4ff;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#f7f7f7; color:#888;
    padding:7px 8px; border:none; border-right:1px solid #e0e0e0; border-bottom:2px solid #111;
    font-weight:700; font-size:8.5pt; }
QHeaderView::section { background:#f7f7f7; color:#888; padding:6px 8px; border:none;
    border-right:1px solid #e0e0e0; border-bottom:2px solid #111; font-weight:700; }

QTreeWidget { background:#fff; color:#111; border:none; alternate-background-color:#fafafa;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#ebebeb; color:#000; }
QTreeWidget::item:hover { background:#f5f5f5; }
QTreeWidget QHeaderView::section { background:#f7f7f7; color:#888; padding:6px 8px;
    border:none; border-right:1px solid #e0e0e0; border-bottom:2px solid #111; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#e8e8e8; font-size:44px; }
QLabel#EmptyTitle { color:#ccc; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#ddd; font-size:9px; margin-top:4px; }

QStatusBar { background:#111; color:#fff; font-size:9pt; padding:0 6px; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#fff; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; }
QLabel#VenvLabel { background:#333; color:#22c55e; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#111; color:#fff; border:none; padding:7px 18px;
    border-radius:4px; font-size:10pt; }
QPushButton:hover  { background:#333; }
QPushButton:pressed { background:#555; }
QPushButton:disabled { background:#eee; color:#bbb; }
QLineEdit { background:#fff; color:#111; border:1px solid #ccc; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#111; }
QDialog    { background:#fff; color:#111; }
QMessageBox { background:#fff; color:#111; }
"""

# ══════════════════════════════════════════════════════════════
#  LIGHT PROFESSIONAL (Microsoft Fluent)
# ══════════════════════════════════════════════════════════════
_LIGHT_PRO = _BASE + """
QMainWindow, QWidget { background:#f3f3f3; color:#1e1e1e;
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#c0c0c0; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#a0a0a0; }
QToolTip { background:#fff; color:#1e1e1e; border-color:#ccc; }

QSplitter#MainSplitter::handle { background:#ddd; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#0078d4; }

QWidget#PanelHeader { background:#ececec; border-bottom:1px solid #ddd; }
QLabel#PanelTitle { color:#aaa; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#f3f3f3; border-bottom:1px solid #e0e0e0; }
QLabel#BreadcrumbDir  { color:#aaa; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#bbb; font-size:10pt; }
QLabel#BreadcrumbFile { color:#1e1e1e; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#0e6b5c; font-size:8.5pt; font-weight:600;
    background:#d0f0ea; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#dddddd; color:#1e1e1e; border-bottom:1px solid #ccc; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#cce5ff; color:#0a4d8c; }
QMenu { background:#fff; color:#1e1e1e; border:1px solid #ccc; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#cce5ff; color:#0a4d8c; }
QMenu::separator { height:1px; background:#e0e0e0; margin:4px 8px; }

QToolBar { background:#ebebeb; border-bottom:1px solid #d0d0d0; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#ccc; width:1px; margin:5px 8px; }
QToolButton { color:#333; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#d8d8d8; border-color:#bbb; }
QToolButton:pressed { background:#cce5ff; border-color:#0078d4; }

QTabWidget#EditorTabs::pane { border:none; background:#fff; }
QTabWidget#EditorTabs QTabBar { background:#ececec; }
QTabWidget#EditorTabs QTabBar::tab { background:#e0e0e0; color:#666;
    padding:7px 16px 6px; border:none; border-right:1px solid #d0d0d0;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#fff; color:#1e1e1e; border-top:2px solid #0078d4; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#d4d4d4; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }
QTabWidget#EditorTabs QTabBar::close-button:hover { background:#fddede; }

QTabWidget#ResultTabs::pane { border:none; background:#fff; }
QTabWidget#ResultTabs QTabBar { background:#ececec; }
QTabWidget#ResultTabs QTabBar::tab { background:#ececec; color:#777;
    padding:7px 14px; border:none; border-right:1px solid #ddd; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#fff; color:#0078d4;
    border-top:2px solid #0078d4; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#e0e0e0; }

QTextEdit#ErrorTerminal, QTextEdit#CompilerConsole,
QTextEdit#SyntaxTerminal, QTextEdit#TokenTerminal {
    background:#0d0d0d; color:#cccccc; border:none;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:10pt; padding:8px; }

QPlainTextEdit { background:#fff; color:#1e1e1e; border:none; selection-background-color:#b8d6f5;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#fff; color:#1e1e1e; gridline-color:#eee; border:none;
    alternate-background-color:#f7f7f7; selection-background-color:#cce5ff;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#ececec; color:#777;
    padding:7px 8px; border:none; border-right:1px solid #ddd; border-bottom:2px solid #0078d4;
    font-weight:700; font-size:8.5pt; }
QHeaderView::section { background:#ececec; color:#777; padding:6px 8px; border:none;
    border-right:1px solid #ddd; border-bottom:2px solid #0078d4; font-weight:700; }

QTreeWidget { background:#fff; color:#1e1e1e; border:none; alternate-background-color:#f7f7f7;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#cce5ff; color:#1e1e1e; }
QTreeWidget::item:hover { background:#e8f4ff; }
QTreeWidget QHeaderView::section { background:#ececec; color:#777; padding:6px 8px;
    border:none; border-right:1px solid #ddd; border-bottom:2px solid #0078d4; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#d0d0d0; font-size:44px; }
QLabel#EmptyTitle { color:#bbb; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#ccc; font-size:9px; margin-top:4px; }

QStatusBar { background:#0078d4; color:#fff; font-size:9pt; padding:0 6px; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#fff; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; }
QLabel#VenvLabel { background:#005fa3; color:#a8d8ff; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#0078d4; color:#fff; border:none; padding:7px 18px;
    border-radius:4px; font-size:10pt; }
QPushButton:hover  { background:#106ebe; }
QPushButton:pressed { background:#005a9e; }
QPushButton:disabled { background:#ddd; color:#888; }
QLineEdit { background:#fff; color:#1e1e1e; border:1px solid #bbb; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#0078d4; }
QDialog    { background:#f3f3f3; color:#1e1e1e; }
QMessageBox { background:#f3f3f3; color:#1e1e1e; }
"""

# ══════════════════════════════════════════════════════════════
#  TOKYO NIGHT
# ══════════════════════════════════════════════════════════════
_TOKYO_NIGHT = _BASE + _TERMINALS + """
QMainWindow, QWidget { background:#1a1b26; color:#a9b1d6;
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#292e42; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#3d59a1; }
QToolTip { background:#16161e; color:#a9b1d6; border-color:#292e42; }

QSplitter#MainSplitter::handle { background:#292e42; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#7aa2f7; }

QWidget#PanelHeader { background:#16161e; border-bottom:1px solid #0d0e17; }
QLabel#PanelTitle { color:#3d59a1; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#1a1b26; border-bottom:1px solid #1f2335; }
QLabel#BreadcrumbDir  { color:#3d59a1; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#292e42; font-size:10pt; }
QLabel#BreadcrumbFile { color:#c0caf5; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#9ece6a; font-size:8.5pt; font-weight:600;
    background:#0d1a0d; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#16161e; color:#a9b1d6; border-bottom:1px solid #0d0e17; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#1f2335; color:#7aa2f7; }
QMenu { background:#1f2335; color:#a9b1d6; border:1px solid #292e42; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#292e42; color:#7aa2f7; }
QMenu::separator { height:1px; background:#292e42; margin:4px 8px; }

QToolBar { background:#16161e; border-bottom:1px solid #0d0e17; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#292e42; width:1px; margin:5px 8px; }
QToolButton { color:#a9b1d6; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#1f2335; border-color:#3d59a1; color:#c0caf5; }
QToolButton:pressed { background:#292e42; border-color:#7aa2f7; }

QTabWidget#EditorTabs::pane { border:none; background:#1a1b26; }
QTabWidget#EditorTabs QTabBar { background:#15161e; }
QTabWidget#EditorTabs QTabBar::tab { background:#15161e; color:#565f89;
    padding:7px 16px 6px; border:none; border-right:1px solid #1a1b26;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#1a1b26; color:#c0caf5; border-top:2px solid #7aa2f7; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#1f2335; color:#a9b1d6; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }

QTabWidget#ResultTabs::pane { border:none; background:#1a1b26; }
QTabWidget#ResultTabs QTabBar { background:#15161e; }
QTabWidget#ResultTabs QTabBar::tab { background:#15161e; color:#565f89;
    padding:7px 14px; border:none; border-right:1px solid #1a1b26; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#1a1b26; color:#9ece6a;
    border-top:2px solid #9ece6a; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#1f2335; color:#a9b1d6; }

QPlainTextEdit { background:#1a1b26; color:#a9b1d6; border:none;
    selection-background-color:#283457;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#1a1b26; color:#a9b1d6; gridline-color:#1f2335; border:none;
    alternate-background-color:#1f2335; selection-background-color:#283457;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#15161e; color:#565f89;
    padding:7px 8px; border:none; border-right:1px solid #292e42; border-bottom:2px solid #7aa2f7;
    font-weight:700; font-size:8.5pt; }
QHeaderView::section { background:#15161e; color:#565f89; padding:6px 8px; border:none;
    border-right:1px solid #292e42; border-bottom:2px solid #7aa2f7; font-weight:700; }

QTreeWidget { background:#1a1b26; color:#a9b1d6; border:none;
    alternate-background-color:#1f2335; font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#283457; color:#c0caf5; }
QTreeWidget::item:hover { background:#1f2335; }
QTreeWidget QHeaderView::section { background:#15161e; color:#565f89; padding:6px 8px;
    border:none; border-right:1px solid #292e42; border-bottom:2px solid #9ece6a; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#1f2335; font-size:44px; }
QLabel#EmptyTitle { color:#292e42; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#222; font-size:9px; margin-top:4px; }

QStatusBar { background:#3d59a1; color:#c0caf5; font-size:9pt; padding:0 6px; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#c0caf5; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; }
QLabel#VenvLabel { background:#1d3055; color:#9ece6a; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#3d59a1; color:#c0caf5; border:none; padding:7px 18px;
    border-radius:4px; font-size:10pt; }
QPushButton:hover  { background:#4a6bb5; }
QPushButton:pressed { background:#2a3f7a; }
QPushButton:disabled { background:#1f2335; color:#565f89; }
QLineEdit { background:#1f2335; color:#a9b1d6; border:1px solid #292e42; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#7aa2f7; }
QDialog    { background:#1f2335; color:#a9b1d6; }
QMessageBox { background:#1f2335; color:#a9b1d6; }
"""

# ══════════════════════════════════════════════════════════════
#  CATPPUCCIN MOCHA
# ══════════════════════════════════════════════════════════════
_CATPPUCCIN = _BASE + _TERMINALS + """
QMainWindow, QWidget { background:#1e1e2e; color:#cdd6f4;
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#313244; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#45475a; }
QToolTip { background:#181825; color:#cdd6f4; border-color:#313244; }

QSplitter#MainSplitter::handle { background:#313244; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#89b4fa; }

QWidget#PanelHeader { background:#181825; border-bottom:1px solid #11111b; }
QLabel#PanelTitle { color:#45475a; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#1e1e2e; border-bottom:1px solid #313244; }
QLabel#BreadcrumbDir  { color:#45475a; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#313244; font-size:10pt; }
QLabel#BreadcrumbFile { color:#cdd6f4; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#a6e3a1; font-size:8.5pt; font-weight:600;
    background:#0d1a0d; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#181825; color:#cdd6f4; border-bottom:1px solid #11111b; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#313244; color:#89b4fa; }
QMenu { background:#1e1e2e; color:#cdd6f4; border:1px solid #313244; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#313244; color:#89b4fa; }
QMenu::separator { height:1px; background:#313244; margin:4px 8px; }

QToolBar { background:#181825; border-bottom:1px solid #11111b; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#313244; width:1px; margin:5px 8px; }
QToolButton { color:#cdd6f4; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#313244; border-color:#45475a; }
QToolButton:pressed { background:#45475a; border-color:#89b4fa; }

QTabWidget#EditorTabs::pane { border:none; background:#1e1e2e; }
QTabWidget#EditorTabs QTabBar { background:#181825; }
QTabWidget#EditorTabs QTabBar::tab { background:#181825; color:#6c7086;
    padding:7px 16px 6px; border:none; border-right:1px solid #11111b;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#1e1e2e; color:#cdd6f4; border-top:2px solid #89b4fa; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#1e1e2e; color:#a6adc8; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }

QTabWidget#ResultTabs::pane { border:none; background:#1e1e2e; }
QTabWidget#ResultTabs QTabBar { background:#181825; }
QTabWidget#ResultTabs QTabBar::tab { background:#181825; color:#6c7086;
    padding:7px 14px; border:none; border-right:1px solid #11111b; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#1e1e2e; color:#a6e3a1;
    border-top:2px solid #a6e3a1; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#1e1e2e; color:#a6adc8; }

QPlainTextEdit { background:#1e1e2e; color:#cdd6f4; border:none;
    selection-background-color:#313244;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#1e1e2e; color:#cdd6f4; gridline-color:#313244; border:none;
    alternate-background-color:#181825; selection-background-color:#313244;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#181825; color:#6c7086;
    padding:7px 8px; border:none; border-right:1px solid #313244; border-bottom:2px solid #89b4fa;
    font-weight:700; font-size:8.5pt; }
QHeaderView::section { background:#181825; color:#6c7086; padding:6px 8px; border:none;
    border-right:1px solid #313244; border-bottom:2px solid #89b4fa; font-weight:700; }

QTreeWidget { background:#1e1e2e; color:#cdd6f4; border:none;
    alternate-background-color:#181825; font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#313244; color:#cdd6f4; }
QTreeWidget::item:hover { background:#181825; }
QTreeWidget QHeaderView::section { background:#181825; color:#6c7086; padding:6px 8px;
    border:none; border-right:1px solid #313244; border-bottom:2px solid #a6e3a1; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#313244; font-size:44px; }
QLabel#EmptyTitle { color:#45475a; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#313244; font-size:9px; margin-top:4px; }

QStatusBar { background:#181825; color:#cdd6f4; font-size:9pt; padding:0 6px; border-top:2px solid #89b4fa; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#cdd6f4; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; }
QLabel#VenvLabel { background:#0d1a0d; color:#a6e3a1; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#89b4fa; color:#1e1e2e; border:none; padding:7px 18px;
    border-radius:4px; font-size:10pt; font-weight:600; }
QPushButton:hover  { background:#74c7ec; }
QPushButton:pressed { background:#6c9cf5; }
QPushButton:disabled { background:#313244; color:#6c7086; }
QLineEdit { background:#313244; color:#cdd6f4; border:1px solid #45475a; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#89b4fa; }
QDialog    { background:#1e1e2e; color:#cdd6f4; }
QMessageBox { background:#1e1e2e; color:#cdd6f4; }
"""

# ══════════════════════════════════════════════════════════════
#  CYBER BLUE
# ══════════════════════════════════════════════════════════════
_CYBER_BLUE = _BASE + _TERMINALS + """
QMainWindow, QWidget { background:#07101e; color:#7ab8d4;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#0d2a4a; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#00b4d8; }
QToolTip { background:#0c1e38; color:#7ab8d4; border-color:#0d2a4a; }

QSplitter#MainSplitter::handle { background:#0d2a4a; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#00b4d8; }

QWidget#PanelHeader { background:#0a1628; border-bottom:2px solid #00b4d8; }
QLabel#PanelTitle { color:#00b4d8; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#07101e; border-bottom:1px solid #0d2a4a; }
QLabel#BreadcrumbDir  { color:#1a4a6a; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#0d2a4a; font-size:10pt; }
QLabel#BreadcrumbFile { color:#7ab8d4; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#00f5d4; font-size:8.5pt; font-weight:600;
    background:#004d30; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#0a1628; color:#7ab8d4; border-bottom:1px solid #0d2a4a; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#0a4a6e; color:#00b4d8; }
QMenu { background:#0c1e38; color:#7ab8d4; border:1px solid #0d2a4a; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#0a4a6e; color:#00b4d8; }
QMenu::separator { height:1px; background:#0d2a4a; margin:4px 8px; }

QToolBar { background:#0a1628; border-bottom:1px solid #0d2a4a; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#0d2a4a; width:1px; margin:5px 8px; }
QToolButton { color:#7ab8d4; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#0a2a4a; border-color:#00b4d8; color:#00b4d8; }
QToolButton:pressed { background:#0a4a6e; }

QTabWidget#EditorTabs::pane { border:none; background:#07101e; }
QTabWidget#EditorTabs QTabBar { background:#0a1628; }
QTabWidget#EditorTabs QTabBar::tab { background:#0c1e38; color:#4a7a9a;
    padding:7px 16px 6px; border:none; border-right:1px solid #0d2a4a;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#07101e; color:#00b4d8; border-top:2px solid #00b4d8; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#0a1e38; color:#6a9ab4; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }

QTabWidget#ResultTabs::pane { border:none; background:#07101e; }
QTabWidget#ResultTabs QTabBar { background:#0a1628; }
QTabWidget#ResultTabs QTabBar::tab { background:#0a1628; color:#4a7a9a;
    padding:7px 14px; border:none; border-right:1px solid #0d2a4a; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#07101e; color:#00b4d8;
    border-top:2px solid #00b4d8; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#0a1e38; color:#6a9ab4; }

QPlainTextEdit { background:#07101e; color:#7ab8d4; border:none;
    selection-background-color:#0a4a6e;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#07101e; color:#7ab8d4; gridline-color:#0d2a4a; border:none;
    alternate-background-color:#0c1e38; selection-background-color:#0a4a6e;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#0a1628; color:#4a7a9a;
    padding:7px 8px; border:none; border-right:1px solid #0d2a4a; border-bottom:2px solid #00b4d8;
    font-weight:700; font-size:8.5pt; }
QHeaderView::section { background:#0a1628; color:#4a7a9a; padding:6px 8px; border:none;
    border-right:1px solid #0d2a4a; border-bottom:2px solid #00b4d8; font-weight:700; }

QTreeWidget { background:#07101e; color:#7ab8d4; border:none;
    alternate-background-color:#0c1e38; font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#0a4a6e; color:#00b4d8; }
QTreeWidget::item:hover { background:#0a2a4a; }
QTreeWidget QHeaderView::section { background:#0a1628; color:#4a7a9a; padding:6px 8px;
    border:none; border-right:1px solid #0d2a4a; border-bottom:2px solid #00b4d8; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#0d2a4a; font-size:44px; }
QLabel#EmptyTitle { color:#1a4a6a; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#1a3a5a; font-size:9px; margin-top:4px; }

QStatusBar { background:#00476e; color:#00b4d8; font-size:9pt; padding:0 6px; border-top:1px solid #00b4d8; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#00b4d8; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; color:#48cae4; }
QLabel#VenvLabel { background:#003a5a; color:#00f5d4; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#00476e; color:#00b4d8; border:1px solid #00b4d8;
    padding:7px 18px; border-radius:4px; font-size:10pt; }
QPushButton:hover  { background:#0a5a7e; color:#48cae4; }
QPushButton:pressed { background:#0a4a6e; }
QPushButton:disabled { background:#0a1628; color:#1a4a6a; border-color:#0d2a4a; }
QLineEdit { background:#0c1e38; color:#7ab8d4; border:1px solid #0d2a4a; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#00b4d8; }
QDialog    { background:#0c1e38; color:#7ab8d4; }
QMessageBox { background:#0c1e38; color:#7ab8d4; }
"""

# ══════════════════════════════════════════════════════════════
#  MONOKAI (clásico de Sublime Text)
# ══════════════════════════════════════════════════════════════
_MONOKAI = _BASE + _TERMINALS + """
QMainWindow, QWidget { background:#272822; color:#f8f8f2;
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#3e3d32; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#75715e; }
QToolTip { background:#3e3d32; color:#f8f8f2; border-color:#75715e; }

QSplitter#MainSplitter::handle { background:#3e3d32; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#f92672; }

QWidget#PanelHeader { background:#1e1e1a; border-bottom:1px solid #1a1a16; }
QLabel#PanelTitle { color:#75715e; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#272822; border-bottom:1px solid #3e3d32; }
QLabel#BreadcrumbDir  { color:#75715e; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#3e3d32; font-size:10pt; }
QLabel#BreadcrumbFile { color:#f8f8f2; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#a6e22e; font-size:8.5pt; font-weight:600;
    background:#1a2a0a; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#1e1e1a; color:#f8f8f2; border-bottom:1px solid #1a1a16; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#3e3d32; color:#f92672; }
QMenu { background:#272822; color:#f8f8f2; border:1px solid #3e3d32; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#3e3d32; color:#f92672; }
QMenu::separator { height:1px; background:#3e3d32; margin:4px 8px; }

QToolBar { background:#1e1e1a; border-bottom:1px solid #1a1a16; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#3e3d32; width:1px; margin:5px 8px; }
QToolButton { color:#f8f8f2; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#3e3d32; border-color:#75715e; }
QToolButton:pressed { background:#49483e; border-color:#f92672; }

QTabWidget#EditorTabs::pane { border:none; background:#272822; }
QTabWidget#EditorTabs QTabBar { background:#1e1e1a; }
QTabWidget#EditorTabs QTabBar::tab { background:#1e1e1a; color:#75715e;
    padding:7px 16px 6px; border:none; border-right:1px solid #272822;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#272822; color:#f8f8f2; border-top:2px solid #f92672; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#3e3d32; color:#ccc; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }

QTabWidget#ResultTabs::pane { border:none; background:#272822; }
QTabWidget#ResultTabs QTabBar { background:#1e1e1a; }
QTabWidget#ResultTabs QTabBar::tab { background:#1e1e1a; color:#75715e;
    padding:7px 14px; border:none; border-right:1px solid #272822; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#272822; color:#a6e22e;
    border-top:2px solid #a6e22e; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#3e3d32; color:#ccc; }

QPlainTextEdit { background:#272822; color:#f8f8f2; border:none;
    selection-background-color:#49483e;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#272822; color:#f8f8f2; gridline-color:#3e3d32; border:none;
    alternate-background-color:#2d2e27; selection-background-color:#49483e;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#1e1e1a; color:#75715e;
    padding:7px 8px; border:none; border-right:1px solid #3e3d32; border-bottom:2px solid #f92672;
    font-weight:700; font-size:8.5pt; }
QHeaderView::section { background:#1e1e1a; color:#75715e; padding:6px 8px; border:none;
    border-right:1px solid #3e3d32; border-bottom:2px solid #f92672; font-weight:700; }

QTreeWidget { background:#272822; color:#f8f8f2; border:none;
    alternate-background-color:#2d2e27; font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#49483e; color:#f8f8f2; }
QTreeWidget::item:hover { background:#3e3d32; }
QTreeWidget QHeaderView::section { background:#1e1e1a; color:#75715e; padding:6px 8px;
    border:none; border-right:1px solid #3e3d32; border-bottom:2px solid #a6e22e; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#3e3d32; font-size:44px; }
QLabel#EmptyTitle { color:#49483e; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#3e3d32; font-size:9px; margin-top:4px; }

QStatusBar { background:#f92672; color:#f8f8f2; font-size:9pt; padding:0 6px; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#f8f8f2; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; }
QLabel#VenvLabel { background:#c0185a; color:#fff; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#f92672; color:#f8f8f2; border:none; padding:7px 18px;
    border-radius:4px; font-size:10pt; font-weight:600; }
QPushButton:hover  { background:#e0154e; }
QPushButton:pressed { background:#c01040; }
QPushButton:disabled { background:#3e3d32; color:#75715e; }
QLineEdit { background:#3e3d32; color:#f8f8f2; border:1px solid #75715e; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#f92672; }
QDialog    { background:#272822; color:#f8f8f2; }
QMessageBox { background:#272822; color:#f8f8f2; }
"""

# ══════════════════════════════════════════════════════════════
#  NORD (Arctic)
# ══════════════════════════════════════════════════════════════
_NORD = _BASE + _TERMINALS + """
QMainWindow, QWidget { background:#2e3440; color:#d8dee9;
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#3b4252; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background:#4c566a; }
QToolTip { background:#3b4252; color:#d8dee9; border-color:#4c566a; }

QSplitter#MainSplitter::handle { background:#3b4252; width:3px; }
QSplitter#MainSplitter::handle:hover { background:#88c0d0; }

QWidget#PanelHeader { background:#242933; border-bottom:1px solid #1e2228; }
QLabel#PanelTitle { color:#4c566a; font-size:8pt; font-weight:700; letter-spacing:2px; }

QWidget#FileBreadcrumb { background:#2e3440; border-bottom:1px solid #3b4252; }
QLabel#BreadcrumbDir  { color:#4c566a; font-size:9pt; }
QLabel#BreadcrumbSep  { color:#3b4252; font-size:10pt; }
QLabel#BreadcrumbFile { color:#eceff4; font-size:9pt; font-weight:600; }
QLabel#BreadcrumbBadge{ color:#a3be8c; font-size:8.5pt; font-weight:600;
    background:#1a2a1a; border-radius:3px; padding:1px 7px; }

QMenuBar { background:#242933; color:#d8dee9; border-bottom:1px solid #1e2228; padding:1px 4px; }
QMenuBar::item { padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected { background:#3b4252; color:#88c0d0; }
QMenu { background:#2e3440; color:#d8dee9; border:1px solid #3b4252; padding:4px 0; }
QMenu::item { padding:5px 28px 5px 16px; }
QMenu::item:selected { background:#3b4252; color:#88c0d0; }
QMenu::separator { height:1px; background:#3b4252; margin:4px 8px; }

QToolBar { background:#242933; border-bottom:1px solid #1e2228; spacing:1px; padding:3px 8px; }
QToolBar::separator { background:#3b4252; width:1px; margin:5px 8px; }
QToolButton { color:#d8dee9; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }
QToolButton:hover  { background:#3b4252; border-color:#4c566a; }
QToolButton:pressed { background:#4c566a; border-color:#88c0d0; }

QTabWidget#EditorTabs::pane { border:none; background:#2e3440; }
QTabWidget#EditorTabs QTabBar { background:#242933; }
QTabWidget#EditorTabs QTabBar::tab { background:#242933; color:#4c566a;
    padding:7px 16px 6px; border:none; border-right:1px solid #2e3440;
    min-width:80px; max-width:200px; font-size:9.5pt; }
QTabWidget#EditorTabs QTabBar::tab:selected { background:#2e3440; color:#eceff4; border-top:2px solid #88c0d0; }
QTabWidget#EditorTabs QTabBar::tab:hover:!selected { background:#3b4252; color:#d8dee9; }
QTabWidget#EditorTabs QTabBar::close-button { image:url(icons/x.svg);
    subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }

QTabWidget#ResultTabs::pane { border:none; background:#2e3440; }
QTabWidget#ResultTabs QTabBar { background:#242933; }
QTabWidget#ResultTabs QTabBar::tab { background:#242933; color:#4c566a;
    padding:7px 14px; border:none; border-right:1px solid #2e3440; font-size:9pt; min-width:70px; }
QTabWidget#ResultTabs QTabBar::tab:selected { background:#2e3440; color:#a3be8c;
    border-top:2px solid #a3be8c; font-weight:600; }
QTabWidget#ResultTabs QTabBar::tab:hover:!selected { background:#3b4252; color:#d8dee9; }

QPlainTextEdit { background:#2e3440; color:#d8dee9; border:none;
    selection-background-color:#3b4252;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }

QTableWidget#LexTable { background:#2e3440; color:#d8dee9; gridline-color:#3b4252; border:none;
    alternate-background-color:#2c3347; selection-background-color:#3b4252;
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTableWidget#LexTable::item { padding:3px 8px; }
QTableWidget#LexTable QHeaderView::section { background:#242933; color:#4c566a;
    padding:7px 8px; border:none; border-right:1px solid #3b4252; border-bottom:2px solid #88c0d0;
    font-weight:700; font-size:8.5pt; }
QHeaderView::section { background:#242933; color:#4c566a; padding:6px 8px; border:none;
    border-right:1px solid #3b4252; border-bottom:2px solid #88c0d0; font-weight:700; }

QTreeWidget { background:#2e3440; color:#d8dee9; border:none;
    alternate-background-color:#2c3347; font-family:'Menlo','Consolas',monospace; font-size:10pt; }
QTreeWidget::item { padding:3px 4px; }
QTreeWidget::item:selected { background:#3b4252; color:#eceff4; }
QTreeWidget::item:hover { background:#3b4252; }
QTreeWidget QHeaderView::section { background:#242933; color:#4c566a; padding:6px 8px;
    border:none; border-right:1px solid #3b4252; border-bottom:2px solid #a3be8c; font-weight:700; }

QWidget#EmptyState { background:transparent; }
QLabel#EmptyIcon  { color:#3b4252; font-size:44px; }
QLabel#EmptyTitle { color:#4c566a; font-size:13px; font-weight:600; margin-top:8px; }
QLabel#EmptySub   { color:#3b4252; font-size:9px; margin-top:4px; }

QStatusBar { background:#3b4252; color:#d8dee9; font-size:9pt; padding:0 6px; }
QStatusBar::item { border:none; }
QStatusBar QLabel { color:#d8dee9; padding:1px 8px; }
QLabel#StatusIndicator { font-weight:700; color:#88c0d0; }
QLabel#VenvLabel { background:#1a2a1a; color:#a3be8c; border-radius:3px;
    padding:1px 8px; font-size:8.5pt; font-weight:600; }

QPushButton { background:#5e81ac; color:#eceff4; border:none; padding:7px 18px;
    border-radius:4px; font-size:10pt; }
QPushButton:hover  { background:#6e91bc; }
QPushButton:pressed { background:#4c6f9a; }
QPushButton:disabled { background:#3b4252; color:#4c566a; }
QLineEdit { background:#3b4252; color:#d8dee9; border:1px solid #4c566a; padding:5px 10px;
    border-radius:4px; font-size:10pt; }
QLineEdit:focus { border-color:#88c0d0; }
QDialog    { background:#2e3440; color:#d8dee9; }
QMessageBox { background:#2e3440; color:#d8dee9; }
"""

# ══════════════════════════════════════════════════════════════
#  Temas clásicos (función auxiliar)
# ══════════════════════════════════════════════════════════════
def _classic(bg, panel, text, accent, sel_txt="white", edit_bg=None, menu_bg=None):
    eb = edit_bg or bg
    mb = menu_bg or panel
    return _BASE + _TERMINALS + f"""
QMainWindow, QWidget {{ background:{bg}; color:{text};
    font-family:'SF Pro Text',-apple-system,'Segoe UI',Arial,sans-serif; font-size:10pt; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{ background:{panel}; }}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{ background:{accent}; }}
QSplitter#MainSplitter::handle {{ background:{panel}; width:3px; }}
QSplitter#MainSplitter::handle:hover {{ background:{accent}; }}
QWidget#PanelHeader {{ background:{panel}; border-bottom:2px solid {accent}; }}
QLabel#PanelTitle {{ color:{text}; font-size:8pt; font-weight:700; letter-spacing:1.5px; opacity:0.5; }}
QWidget#FileBreadcrumb {{ background:{bg}; border-bottom:1px solid {panel}; }}
QLabel#BreadcrumbDir  {{ color:{text}; font-size:9pt; opacity:0.4; }}
QLabel#BreadcrumbSep  {{ color:{text}; font-size:10pt; opacity:0.3; }}
QLabel#BreadcrumbFile {{ color:{text}; font-size:9pt; font-weight:600; }}
QLabel#BreadcrumbBadge{{ color:{accent}; font-size:8.5pt; font-weight:600; border-radius:3px; padding:1px 7px; }}
QMenuBar {{ background:{mb}; color:{text}; border-bottom:1px solid {panel}; padding:1px 4px; }}
QMenuBar::item {{ padding:4px 10px; border-radius:3px; }}
QMenuBar::item:selected {{ background:{accent}; color:{sel_txt}; }}
QMenu {{ background:{panel}; color:{text}; border:1px solid {accent}; padding:4px 0; }}
QMenu::item {{ padding:5px 28px 5px 16px; }}
QMenu::item:selected {{ background:{accent}; color:{sel_txt}; }}
QMenu::separator {{ height:1px; background:{accent}; margin:4px 8px; opacity:0.3; }}
QToolBar {{ background:{panel}; border-bottom:1px solid {bg}; spacing:1px; padding:3px 8px; }}
QToolBar::separator {{ background:{text}; width:1px; margin:5px 8px; opacity:0.2; }}
QToolButton {{ color:{text}; background:transparent; border:1px solid transparent;
    border-radius:5px; padding:5px 10px; font-size:9pt; min-width:26px; }}
QToolButton:hover {{ background:{accent}; color:{sel_txt}; border-color:{accent}; }}
QToolButton:pressed {{ opacity:0.8; }}
QTabWidget#EditorTabs::pane {{ border:none; background:{bg}; }}
QTabWidget#EditorTabs QTabBar {{ background:{panel}; }}
QTabWidget#EditorTabs QTabBar::tab {{ background:{panel}; color:{text};
    padding:7px 16px 6px; border:none; border-right:1px solid {bg};
    min-width:80px; max-width:200px; font-size:9.5pt; opacity:0.7; }}
QTabWidget#EditorTabs QTabBar::tab:selected {{ background:{bg}; color:{sel_txt}; border-top:2px solid {accent}; opacity:1; }}
QTabWidget#EditorTabs QTabBar::close-button {{ image:url(icons/x.svg); subcontrol-position:right; padding:2px; border-radius:3px; margin-left:4px; }}
QTabWidget#ResultTabs::pane {{ border:none; background:{bg}; }}
QTabWidget#ResultTabs QTabBar {{ background:{panel}; }}
QTabWidget#ResultTabs QTabBar::tab {{ background:{panel}; color:{text};
    padding:7px 14px; border:none; border-right:1px solid {bg}; font-size:9pt; min-width:70px; opacity:0.7; }}
QTabWidget#ResultTabs QTabBar::tab:selected {{ background:{bg}; color:{accent}; border-top:2px solid {accent}; font-weight:600; opacity:1; }}
QPlainTextEdit {{ background:{eb}; color:{text}; border:none;
    font-family:'Menlo','SF Mono','Consolas',monospace; font-size:11pt; padding:4px 0; }}
QTableWidget#LexTable {{ background:{eb}; color:{text}; gridline-color:{panel}; border:none;
    alternate-background-color:{panel}; selection-background-color:{accent};
    font-family:'Menlo','Consolas',monospace; font-size:10pt; }}
QTableWidget#LexTable::item {{ padding:3px 8px; }}
QTableWidget#LexTable QHeaderView::section {{ background:{panel}; color:{text};
    padding:6px 8px; border:none; border-bottom:2px solid {accent}; font-weight:700; font-size:8.5pt; }}
QHeaderView::section {{ background:{panel}; color:{text};
    padding:6px 8px; border:none; border-bottom:2px solid {accent}; font-weight:700; }}
QTreeWidget {{ background:{eb}; color:{text}; border:none;
    alternate-background-color:{panel}; font-family:'Menlo','Consolas',monospace; font-size:10pt; }}
QTreeWidget::item {{ padding:3px 4px; }}
QTreeWidget::item:selected {{ background:{accent}; color:{sel_txt}; }}
QTreeWidget::item:hover {{ background:{panel}; }}
QTreeWidget QHeaderView::section {{ background:{panel}; color:{text};
    border:none; border-bottom:2px solid {accent}; padding:5px 8px; font-weight:700; }}
QWidget#EmptyState {{ background:transparent; }}
QStatusBar {{ background:{accent}; color:{sel_txt}; font-size:9pt; padding:0 6px; }}
QStatusBar::item {{ border:none; }}
QStatusBar QLabel {{ color:{sel_txt}; padding:1px 8px; }}
QLabel#StatusIndicator {{ font-weight:700; }}
QLabel#VenvLabel {{ color:{sel_txt}; border-radius:3px; padding:1px 8px; font-size:8.5pt; font-weight:600; }}
QPushButton {{ background:{accent}; color:{sel_txt}; border:none; padding:7px 18px; border-radius:4px; font-size:10pt; }}
QPushButton:hover {{ opacity:0.85; }}
QLineEdit {{ background:{panel}; color:{text}; border:1px solid {accent}; padding:5px 10px; border-radius:4px; font-size:10pt; }}
QDialog {{ background:{panel}; color:{text}; }}
QMessageBox {{ background:{panel}; color:{text}; }}
"""


_DRACULA  = _classic("#282a36", "#44475a", "#f8f8f2", "#bd93f9", "#282a36", menu_bg="#21222c")
_OCEAN    = _classic("#0f172a", "#1e293b", "#e2e8f0", "#3b82f6", "white",   menu_bg="#0f172a")
_SUNSET   = _classic("#2b1d1d", "#3a2a2a", "#ffe4d6", "#ff7b00", "#1a0a00", menu_bg="#2b1d1d")
_FOREST   = _classic("#0d1f1a", "#13332b", "#d1fae5", "#10b981", "#051a10", menu_bg="#0d1f1a")
_NEON     = _classic("#140021", "#1f0033", "#f5d0fe", "#c026d3", "white",   menu_bg="#140021")
_HACKER   = _classic("black",   "#001100", "#00ff00", "#00aa00", "#001100", edit_bg="black", menu_bg="black")


# ══════════════════════════════════════════════════════════════
#  ThemeManager
# ══════════════════════════════════════════════════════════════
class ThemeManager:

    _current = "dark_pro"

    _themes = {
        # Modernos
        "dark_pro":    _DARK_PRO,
        "pure_black":  _PURE_BLACK,
        "pure_white":  _PURE_WHITE,
        "light_pro":   _LIGHT_PRO,
        "cyber_blue":  _CYBER_BLUE,
        "tokyo_night": _TOKYO_NIGHT,
        "catppuccin":  _CATPPUCCIN,
        "monokai":     _MONOKAI,
        "nord":        _NORD,
        # Clásicos
        "dracula":  _DRACULA,
        "ocean":    _OCEAN,
        "sunset":   _SUNSET,
        "forest":   _FOREST,
        "neon":     _NEON,
        "hacker":   _HACKER,
    }

    _labels = {
        "dark_pro":    "Dark Professional",
        "pure_black":  "Pure Black",
        "pure_white":  "Pure White",
        "light_pro":   "Light Professional",
        "cyber_blue":  "Cyber Blue",
        "tokyo_night": "Tokyo Night",
        "catppuccin":  "Catppuccin Mocha",
        "monokai":     "Monokai",
        "nord":        "Nord Arctic",
        "dracula":     "Dracula",
        "ocean":       "Ocean Blue",
        "sunset":      "Sunset",
        "forest":      "Forest",
        "neon":        "Neon Purple",
        "hacker":      "Hacker Classic",
    }

    # Color de acento por tema (para el selector visual)
    _accents = {
        "dark_pro":    "#007acc",
        "pure_black":  "#ffffff",
        "pure_white":  "#111111",
        "light_pro":   "#0078d4",
        "cyber_blue":  "#00b4d8",
        "tokyo_night": "#7aa2f7",
        "catppuccin":  "#89b4fa",
        "monokai":     "#f92672",
        "nord":        "#88c0d0",
        "dracula":     "#bd93f9",
        "ocean":       "#3b82f6",
        "sunset":      "#ff7b00",
        "forest":      "#10b981",
        "neon":        "#c026d3",
        "hacker":      "#00aa00",
    }

    _bgs = {
        "dark_pro":    "#1e1e1e",
        "pure_black":  "#000000",
        "pure_white":  "#ffffff",
        "light_pro":   "#f3f3f3",
        "cyber_blue":  "#07101e",
        "tokyo_night": "#1a1b26",
        "catppuccin":  "#1e1e2e",
        "monokai":     "#272822",
        "nord":        "#2e3440",
        "dracula":     "#282a36",
        "ocean":       "#0f172a",
        "sunset":      "#2b1d1d",
        "forest":      "#0d1f1a",
        "neon":        "#140021",
        "hacker":      "#000000",
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
    def accent(cls, key: str) -> str:
        return cls._accents.get(key, "#007acc")

    @classmethod
    def bg(cls, key: str) -> str:
        return cls._bgs.get(key, "#1e1e1e")

    @classmethod
    def all_keys(cls) -> list:
        return list(cls._themes.keys())
