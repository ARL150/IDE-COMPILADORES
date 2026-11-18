# compiler/intermediate.py — Generador de código intermedio de tres direcciones
"""
Recorre el árbol anotado y produce código de tres direcciones (representación
didáctica .ci).  No modifica el árbol; retorna una lista de cadenas.

Formato de salida:
  t0 = READ
  A  = t0
  t1 = t2 + t3
  IF_FALSE t4 GOTO L2
  GOTO L1
  L1:
  WRITE t5
"""
from __future__ import annotations
from compiler.annotated_ast import AnnotatedNode


class IntermediateGenerator:

    def __init__(self):
        self._code: list[str] = []
        self._counter = 0

    # ── API pública ───────────────────────────────────────────────
    def generate(self, root: AnnotatedNode) -> list[str]:
        self._code = []
        self._counter = 0
        self._gen(root)
        return self._code

    # ── Helpers ───────────────────────────────────────────────────
    def _tmp(self) -> str:
        name = f"t{self._counter}"
        self._counter += 1
        return name

    def _label(self) -> str:
        name = f"L{self._counter}"
        self._counter += 1
        return name

    def _emit(self, s: str):
        self._code.append(s)

    # ── Generador recursivo ───────────────────────────────────────
    def _gen(self, node: AnnotatedNode | None) -> str | None:
        if node is None:
            return None
        nt = node.node_type

        if nt in ("PROGRAMA", "DECLARACIONES", "SENTENCIAS",
                  "ENTONCES", "SINO", "CUERPO", "MAIN"):
            for ch in node.children:
                self._gen(ch)
            return None

        if nt == "DECL_VAR":
            return None  # sólo reserva espacio — no emite código

        if nt == "ASIGNACION":
            rhs = node.children[1] if len(node.children) > 1 else None
            if rhs is None:
                return node.value
            t = self._gen(rhs)
            self._emit(f"{node.value} = {t}")
            return node.value

        if nt == "ENTRADA":
            for ch in node.children:
                if ch.node_type == "ID":
                    t = self._tmp()
                    self._emit(f"{t} = READ")
                    self._emit(f"{ch.value} = {t}")
            return None

        if nt == "SALIDA":
            for ch in node.children:
                t = self._gen(ch)
                if t is not None:
                    self._emit(f"WRITE {t}")
            return None

        if nt == "IF":
            cond_node = node.children[0] if node.children else None
            then_node = node.children[1] if len(node.children) > 1 else None
            else_node = node.children[2] if len(node.children) > 2 else None

            t_cond = self._gen(cond_node)
            L_else = self._label()
            L_end  = self._label()

            self._emit(f"IF_FALSE {t_cond} GOTO {L_else}")
            if then_node:
                self._gen(then_node)
            self._emit(f"GOTO {L_end}")
            self._emit(f"{L_else}:")
            if else_node:
                self._gen(else_node)
            self._emit(f"{L_end}:")
            return None

        if nt == "MIENTRAS":
            L_test = self._label()
            L_end  = self._label()
            cond_node = node.children[0] if node.children else None
            body_node = node.children[1] if len(node.children) > 1 else None

            self._emit(f"{L_test}:")
            t_cond = self._gen(cond_node)
            self._emit(f"IF_FALSE {t_cond} GOTO {L_end}")
            if body_node:
                self._gen(body_node)
            self._emit(f"GOTO {L_test}")
            self._emit(f"{L_end}:")
            return None

        if nt == "HACER_MIENTRAS":
            L_body = self._label()
            cond_node = node.children[-1] if node.children else None
            body_node = node.children[0] if node.children else None

            self._emit(f"{L_body}:")
            if body_node:
                self._gen(body_node)
            t_cond = self._gen(cond_node)
            self._emit(f"IF_TRUE {t_cond} GOTO {L_body}")
            return None

        if nt == "CONDICION":
            expr = node.children[0] if node.children else None
            return self._gen(expr)

        if nt in ("OP_SUMA", "OP_MULT", "OP_POT"):
            left  = self._gen(node.children[0]) if len(node.children) > 0 else "?"
            right = self._gen(node.children[1]) if len(node.children) > 1 else "?"
            t = self._tmp()
            self._emit(f"{t} = {left} {node.value} {right}")
            return t

        if nt == "OP_REL":
            left  = self._gen(node.children[0]) if len(node.children) > 0 else "?"
            right = self._gen(node.children[1]) if len(node.children) > 1 else "?"
            t = self._tmp()
            self._emit(f"{t} = {left} {node.value} {right}")
            return t

        if nt == "OP_LOGICO":
            if node.value == "!":
                operand = self._gen(node.children[0]) if node.children else "?"
                t = self._tmp()
                self._emit(f"{t} = ! {operand}")
                return t
            left  = self._gen(node.children[0]) if len(node.children) > 0 else "?"
            right = self._gen(node.children[1]) if len(node.children) > 1 else "?"
            t = self._tmp()
            self._emit(f"{t} = {left} {node.value} {right}")
            return t

        if nt == "ID":
            return node.value

        if nt == "NUMERO":
            return str(node.value)

        if nt == "REAL":
            return str(node.value)

        if nt == "BOOL":
            return str(node.value)

        if nt == "CADENA":
            v = node.value or ""
            return f'"{v}"'

        # nodo desconocido — recorrer hijos
        for ch in node.children:
            self._gen(ch)
        return None
