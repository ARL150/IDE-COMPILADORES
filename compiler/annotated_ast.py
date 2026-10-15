# compiler/annotated_ast.py — Copia anotada del AST (Fase 3)
from __future__ import annotations
from typing import Optional, Iterator
from compiler.ast_nodes import ASTNode


class AnnotatedNode:
    """
    Nodo del árbol anotado. Es una COPIA del nodo del AST: el AST original
    nunca se modifica (se conserva en `.original` para compararlos).

    Atributos semánticos:
      inferred_type  sintetizado: tipo resultante del nodo ("error" si es inválido)
      declared_type  heredado: tipo propagado desde la declaración / tabla de símbolos
      const_value    valor si es constante calculable en compilación (None si no)
      conversion     conversión implícita aplicada a este nodo ("int_to_float")
      sem_errors     mensajes de error semántico asociados al nodo
    """

    def __init__(self, source: ASTNode):
        self.original:  ASTNode = source
        self.node_type  = source.node_type
        self.value      = source.value
        self.line       = source.line
        self.column     = source.column
        self.children:  list[AnnotatedNode] = []
        self.inferred_type: Optional[str] = None
        self.declared_type: Optional[str] = None
        self.const_value = None
        self.conversion:  Optional[str] = None
        self.sem_errors:  list[str] = []
        self.is_valid:    bool = True

    def walk(self) -> Iterator["AnnotatedNode"]:
        yield self
        for ch in self.children:
            yield from ch.walk()

    def __repr__(self):
        return f"<AnnotatedNode {self.node_type} {self.value!r} :{self.inferred_type}>"


def copy_ast(node: ASTNode) -> AnnotatedNode:
    """Copia profunda del AST como árbol anotado (ignora hijos None)."""
    an = AnnotatedNode(node)
    for ch in node.children:
        if ch is not None:
            an.children.append(copy_ast(ch))
    return an
