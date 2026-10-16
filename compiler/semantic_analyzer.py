# compiler/semantic_analyzer.py — Recorrido semántico del AST (Fase 3)
"""
Recibe el AST del parser, lo copia como árbol anotado (el original no se
modifica) y lo recorre calculando:

  Atributos SINTETIZADOS (suben):  inferred_type, const_value, conversion
  Atributos HEREDADOS   (bajan):   declared_type (el tipo de DECL_VAR se
                                   propaga a cada ID de la lista; en un uso,
                                   viene de la tabla de símbolos)

Relación AST ↔ tabla de símbolos:
  declaración → insert · uso de id → lookup · expresión → obtiene/propaga tipo
  · asignación → compara tipo del id con el de la expresión.

Recuperación de errores: nunca se aborta. Una expresión inválida toma el tipo
"error", que se propaga en silencio (no genera errores derivados), mientras
el recorrido continúa para reportar el resto.
"""
from __future__ import annotations
import sys
from typing import Optional

from compiler.ast_nodes import ASTNode
from compiler.annotated_ast import AnnotatedNode, copy_ast
from compiler.symbol_table import SymbolTable
from compiler import semantic_errors as E
from compiler.semantic_errors import SemanticError
from compiler import type_checker as T
from compiler.type_checker import INT, FLOAT, BOOL, STRING, ERROR


class SemanticAnalyzer:

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: list[SemanticError] = []
        self.original_root: Optional[ASTNode] = None
        self.annotated_root: Optional[AnnotatedNode] = None
        self._reported_undeclared: set = set()

    # ── Entrada pública ───────────────────────────────────────────
    def analyze(self, ast: ASTNode) -> AnnotatedNode:
        self.symbol_table = SymbolTable()
        self.errors = []
        self._reported_undeclared = set()
        self.original_root = ast
        # Árboles muy profundos (expresiones de miles de términos) necesitan más pila.
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old_limit, 20000))
        try:
            root = copy_ast(ast)
            self.annotated_root = root
            self._visit(root)
        finally:
            sys.setrecursionlimit(old_limit)
        return root

    # ── Utilidades ────────────────────────────────────────────────
    def _error(self, category: str, message: str, node: AnnotatedNode,
               line=None, column=None):
        err = SemanticError(category, message,
                            line if line is not None else node.line,
                            column if column is not None else node.column)
        self.errors.append(err)
        node.sem_errors.append(str(err))
        node.is_valid = False

    def _report(self, result: T.CheckResult, node: AnnotatedNode):
        if result.has_error:
            self._error(result.category, result.message, node)

    def _undeclared(self, node: AnnotatedNode, ctx: str = "") -> None:
        """Reporta CADA uso no declarado (una vez por posición en el código)."""
        key = (node.value, node.line, node.column)
        if node.line is not None and key in self._reported_undeclared:
            node.is_valid = False
            return
        self._reported_undeclared.add(key)
        self._error(E.UNDECLARED,
                    f"Identificador '{node.value}' no declarado{ctx}.", node)

    # ── Despacho ──────────────────────────────────────────────────
    def _visit(self, node: AnnotatedNode) -> str:
        handler = getattr(self, "_v_" + node.node_type, None)
        if handler is None:
            self._visit_children(node)
            return node.inferred_type or ERROR
        handler(node)
        return node.inferred_type or ERROR

    def _visit_children(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

    def _block(self, node: AnnotatedNode):
        """Cuerpos de if / else / while / do: abren un ámbito propio."""
        label = f"{node.node_type}@L{node.line}" if node.line else node.node_type
        self.symbol_table.enter_scope(label)
        # Un cuerpo puede ejecutarse 0, 1 o N veces: los valores de lo que
        # asigna no se conocen al entrar (ni ramas hermanas ni iteraciones previas).
        self._invalidate_assigned(node)
        self._visit_children(node)
        self.symbol_table.exit_scope()

    def _invalidate_assigned(self, node: AnnotatedNode):
        """Olvida el valor de toda variable asignada (o leída con cin) dentro de `node`."""
        for n in node.walk():
            name = None
            if n.node_type == "ASIGNACION":
                name = n.value
            elif n.node_type == "ENTRADA":
                for ch in n.children:
                    if ch.node_type == "ID":
                        self._forget(ch.value)
                continue
            if name:
                self._forget(name)

    def _forget(self, name):
        entry = self.symbol_table.lookup(name) if name else None
        if entry is not None:
            entry.value = None

    def _control(self, node: AnnotatedNode):
        """if / while / do: los valores asignados dentro no son seguros ni durante
        ni después de la estructura (conservador)."""
        self._invalidate_assigned(node)
        self._visit_children(node)
        self._invalidate_assigned(node)

    def _v_HACER_MIENTRAS(self, node: AnnotatedNode):
        # hijos: [CUERPO, CONDICION]; la condición se evalúa tras el cuerpo
        self._invalidate_assigned(node)
        for ch in node.children:
            self._visit(ch)
            if ch.node_type == "CUERPO":
                self._invalidate_assigned(node)
        self._invalidate_assigned(node)

    def _statements(self, node: AnnotatedNode):
        """Lista de sentencias / programa: sintetiza tipo y valor de la última hija."""
        self._visit_children(node)
        if node.children:
            last = node.children[-1]
            node.inferred_type = last.inferred_type
            node.const_value = last.const_value

    # ── Estructura ────────────────────────────────────────────────
    _v_MAIN = _v_DECLARACIONES = _visit_children
    _v_PROGRAMA = _v_SENTENCIAS = _statements
    _v_IF = _v_MIENTRAS = _control
    _v_ENTONCES = _v_SINO = _v_CUERPO = _block

    # ── Declaraciones (atributo heredado dtype) ───────────────────
    def _v_DECL_VAR(self, node: AnnotatedNode):
        if not node.children:
            return
        tipo = node.children[0]
        dtype = T.normalize_type(tipo.value or "int")
        tipo.inferred_type = dtype
        node.declared_type = dtype           # heredado: baja a cada ID
        for ch in node.children[1:]:
            if ch.node_type != "ID":
                continue
            ch.declared_type = dtype
            ch.inferred_type = dtype
            inserted, entry = self.symbol_table.insert(
                ch.value, dtype, ch.line or 0, ch.column or 0)
            if not inserted:
                self._error(
                    E.DUPLICATE,
                    f"Identificador '{ch.value}' ya declarado en este ámbito "
                    f"(línea {entry.line}, col {entry.column}).", ch)

    # ── Identificador (uso) ───────────────────────────────────────
    def _v_ID(self, node: AnnotatedNode):
        entry = self.symbol_table.lookup(node.value) if node.value else None
        if entry is None:
            node.inferred_type = ERROR
            if node.value and node.value != "?":
                self._undeclared(node)
            return
        entry.add_reference(node.line, node.column)
        node.inferred_type = entry.dtype
        node.declared_type = entry.dtype
        node.const_value = entry.value       # el valor sale de la tabla de símbolos

    # ── Literales ─────────────────────────────────────────────────
    def _v_NUMERO(self, node: AnnotatedNode):
        node.inferred_type = INT
        try:
            node.const_value = int(node.value)
        except (ValueError, TypeError):
            pass

    def _v_REAL(self, node: AnnotatedNode):
        node.inferred_type = FLOAT
        try:
            node.const_value = float(node.value)
        except (ValueError, TypeError):
            pass

    def _v_BOOL(self, node: AnnotatedNode):
        node.inferred_type = BOOL
        node.const_value = str(node.value).lower() == "true"

    def _v_CADENA(self, node: AnnotatedNode):
        node.inferred_type = STRING

    # ── Asignación ────────────────────────────────────────────────
    def _v_ASIGNACION(self, node: AnnotatedNode):
        name = node.value
        lhs = node.children[0] if node.children and node.children[0].node_type == "ID" else None
        # Con AST parcial puede faltar el id destino: lo que quede se analiza igual.
        if lhs is not None:
            rhs = node.children[-1] if len(node.children) > 1 else None
        else:
            rhs = node.children[-1] if node.children else None

        target = ERROR
        if lhs is not None:
            self._v_ID(lhs)                  # el id destino también es un uso
            target = lhs.inferred_type
        elif name and name != "?":
            entry = self.symbol_table.lookup(name)
            target = entry.dtype if entry else ERROR

        source = self._visit(rhs) if rhs is not None else None
        node.declared_type = target if target != ERROR else None
        node.inferred_type = target

        entry = self.symbol_table.lookup(lhs.value if lhs is not None else name)
        if rhs is None or source is None:
            self._set_value(entry, lhs, node, None)
            return                            # `x = ;` — nada que comparar
        result = T.check_assignment(name, target, source)
        self._report(result, node)
        if 0 in result.convert:
            rhs.conversion = T.INT_TO_FLOAT
        value = None
        if not result.has_error and target != ERROR and source != ERROR:
            value = rhs.const_value
            if value is not None and target == FLOAT:
                value = float(value)
        self._set_value(entry, lhs, node, value)

    def _set_value(self, entry, lhs, node: AnnotatedNode, value):
        """Guarda el valor en la tabla de símbolos y lo sube al nodo de asignación."""
        if entry is not None:
            entry.value = value
        if lhs is not None:
            lhs.const_value = value
        node.const_value = value

    # ── Condiciones ───────────────────────────────────────────────
    def _v_CONDICION(self, node: AnnotatedNode):
        if not node.children:
            node.inferred_type = ERROR
            return
        expr = node.children[0]
        t = self._visit(expr)
        result = T.check_condition(t, "La condición")
        if result.has_error:
            self._error(result.category, result.message, node)
            node.inferred_type = ERROR
        else:
            node.inferred_type = result.result_type
            node.const_value = expr.const_value

    # ── E/S ───────────────────────────────────────────────────────
    def _v_ENTRADA(self, node: AnnotatedNode):
        for ch in node.children:
            if ch.node_type == "ID":
                self._v_ID(ch)
                self._forget(ch.value)       # el valor leído en cin no se conoce
                ch.const_value = None

    def _v_SALIDA(self, node: AnnotatedNode):
        for ch in node.children:             # CADENA es válida aquí
            self._visit(ch)

    # ── Operadores ────────────────────────────────────────────────
    def _operands(self, node: AnnotatedNode) -> list:
        return [self._visit(ch) for ch in node.children]

    def _apply_conversions(self, node: AnnotatedNode, result: T.CheckResult):
        for i in result.convert:
            if i < len(node.children):
                node.children[i].conversion = T.INT_TO_FLOAT

    def _binary_arith(self, node: AnnotatedNode):
        types = self._operands(node)
        if len(types) != 2:
            node.inferred_type = ERROR
            return
        op = node.value
        result = T.check_arithmetic(op, types[0], types[1])
        self._report(result, node)
        node.inferred_type = result.result_type
        if result.has_error or result.result_type == ERROR:
            return
        self._apply_conversions(node, result)
        a, b = node.children[0].const_value, node.children[1].const_value
        if op in ("/", "%") and T.is_zero(b):
            kind = "División" if op == "/" else "Módulo"
            self._error(E.DIVISION_BY_ZERO,
                        f"{kind} entre cero en una expresión constante "
                        f"('{op}' con divisor 0).", node)
            return                            # sin const_value
        node.const_value = T.fold_arithmetic(op, a, b, result.result_type)

    _v_OP_SUMA = _v_OP_MULT = _v_OP_POT = _binary_arith

    def _v_OP_REL(self, node: AnnotatedNode):
        types = self._operands(node)
        if len(types) != 2:
            node.inferred_type = ERROR
            return
        result = T.check_relational(node.value, types[0], types[1])
        self._report(result, node)
        node.inferred_type = result.result_type
        if result.has_error or result.result_type == ERROR:
            return
        self._apply_conversions(node, result)
        node.const_value = T.fold_relational(
            node.value, node.children[0].const_value, node.children[1].const_value)

    def _v_OP_LOGICO(self, node: AnnotatedNode):
        types = self._operands(node)
        expected = 1 if node.value == "!" else 2
        if len(types) != expected:
            node.inferred_type = ERROR
            return
        result = T.check_logical(node.value, types)
        self._report(result, node)
        node.inferred_type = result.result_type
        if result.has_error or result.result_type == ERROR:
            return
        node.const_value = T.fold_logical(
            node.value, [c.const_value for c in node.children])
