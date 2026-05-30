# compiler/ast_nodes.py

class ASTNode:

    def __init__(self, node_type, value=None):

        self.node_type = node_type
        self.value = value
        self.children = []

    def add_child(self, child):

        if child:
            self.children.append(child)

    def __repr__(self):

        return f"{self.node_type}: {self.value}"