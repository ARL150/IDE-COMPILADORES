# compiler/ast_nodes.py


class ASTNode:

    def __init__(self, node_type, value=None, line=None, column=None):
        self.node_type = node_type
        self.value = value
        self.line = line
        self.column = column
        self.children = []

    def add_child(self, child):
        if child:
            self.children.append(child)

    def __repr__(self):
        parts = [self.node_type]
        if self.value is not None:
            parts.append(f"={self.value!r}")
        if self.line is not None:
            parts.append(f"@{self.line}:{self.column}")
        return " ".join(parts)
