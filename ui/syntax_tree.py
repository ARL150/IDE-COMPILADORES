from PyQt6.QtWidgets import (
    QMainWindow,
    QTreeWidget,
    QTreeWidgetItem
)


class SyntaxTreeWindow(QMainWindow):

    def __init__(self, ast_root):

        super().__init__()

        # ventana
        self.setWindowTitle(
            "Árbol Sintáctico"
        )

        self.setGeometry(
            100,
            100,
            800,
            600
        )

        # árbol
        self.tree = QTreeWidget()

        self.tree.setHeaderLabel(
            "AST"
        )

        self.setCentralWidget(
            self.tree
        )

        # construir árbol
        self.build_tree(
            ast_root,
            self.tree.invisibleRootItem()
        )

    # =========================================
    # construir árbol recursivo
    # =========================================

    def build_tree(
        self,
        node,
        parent
    ):

        if node is None:
            return

        # texto del nodo
        if node.value is not None:

            item = QTreeWidgetItem([
                f"{node.node_type}: {node.value}"
            ])

        else:

            item = QTreeWidgetItem([
                node.node_type
            ])

        # agregar hijo
        parent.addChild(item)

        # recorrer hijos
        for child in node.children:

            self.build_tree(
                child,
                item
            )