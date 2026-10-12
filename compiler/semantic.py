# compiler/semantic.py — Fase 3: Análisis Semántico
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from compiler.ast_nodes import ASTNode


# ─────────────────────────────────────────────────────────────────
# SymbolEntry / SymbolTable
# ─────────────────────────────────────────────────────────────────

@dataclass
class SymbolEntry:
    name:    str
    dtype:   str        # "int" | "float" | "bool"
    line:    int
    column:  int
    address: int = 0    # offset de memoria (se asigna al insertar)


class SymbolTable:
    def __init__(self):
        self._symbols: dict[str, SymbolEntry] = {}
        self._next_addr = 0

    # ── Insert ────────────────────────────────────────────────────
    def insert(self, name: str, dtype: str, line: int, col: int) -> Optional[str]:
        """Inserta símbolo. Retorna mensaje de error si ya existe, else None."""
        if name in self._symbols:
            prev = self._symbols[name]
            return (f"Variable '{name}' declarada previamente "
                    f"(línea {prev.line}, columna {prev.column}).")
        entry = SymbolEntry(name=name, dtype=dtype, line=line, column=col,
                            address=self._next_addr)
        self._next_addr += 4 if dtype == "float" else 2
        self._symbols[name] = entry
        return None

    # ── Lookup ────────────────────────────────────────────────────
    def lookup(self, name: str) -> Optional[SymbolEntry]:
        return self._symbols.get(name)

    def all_entries(self) -> list[SymbolEntry]:
        return list(self._symbols.values())


# ─────────────────────────────────────────────────────────────────
# SemanticError
# ─────────────────────────────────────────────────────────────────

@dataclass
class SemanticError:
    category: str   # "UNDECLARED" | "DUPLICATE" | "TYPE_MISMATCH" | etc.
    message:  str
    line:     Optional[int]   = None
    column:   Optional[int]   = None

    def __str__(self):
        loc = ""
        if self.line is not None:
            loc = f" [línea {self.line}"
            if self.column is not None:
                loc += f", col {self.column}"
            loc += "]"
        return f"[{self.category}]{loc} {self.message}"


# ─────────────────────────────────────────────────────────────────
# AnnotatedNode — copia decorada del AST original
# ─────────────────────────────────────────────────────────────────

class AnnotatedNode:
    def __init__(self, source: ASTNode):
        self.node_type   = source.node_type
        self.value       = source.value
        self.line        = source.line
        self.column      = source.column
        self.children:   list[AnnotatedNode] = []
        # Atributos semánticos
        self.inferred_type:  Optional[str]  = None   # sintetizado
        self.declared_type:  Optional[str]  = None   # heredado
        self.const_value     = None                   # valor si constante
        self.conversion:     Optional[str]  = None   # "int_to_float"
        self.sem_errors:     list[str]      = []
        self.is_valid:       bool           = True


def _copy_tree(node: ASTNode) -> AnnotatedNode:
    an = AnnotatedNode(node)
    for ch in node.children:
        if ch is not None:
            an.children.append(_copy_tree(ch))
    return an


# ─────────────────────────────────────────────────────────────────
# SemanticAnalyzer
# ─────────────────────────────────────────────────────────────────

_NUMERIC = {"int", "float"}


def _normalize_type(t: str) -> str:
    """Normaliza 'real' → 'float'."""
    return "float" if t in ("real", "REAL_KW") else t


def _coerce(t1: str, t2: str) -> Optional[str]:
    """
    Retorna el tipo resultante de combinar t1 y t2 aritméticamente,
    o None si la combinación es inválida.
    """
    if t1 == t2 == "int":
        return "int"
    if t1 in _NUMERIC and t2 in _NUMERIC:
        return "float"
    return None


class SemanticAnalyzer:

    def __init__(self):
        self.symbol_table  = SymbolTable()
        self.errors:       list[SemanticError] = []
        self._annotated_root: Optional[AnnotatedNode] = None

    # ── Entrada pública ───────────────────────────────────────────

    def analyze(self, ast: ASTNode) -> AnnotatedNode:
        """Analiza el AST y retorna el árbol anotado."""
        self.symbol_table  = SymbolTable()
        self.errors        = []
        root = _copy_tree(ast)
        self._visit(root, inherited_type=None)
        self._annotated_root = root
        return root

    # ── Despacho principal ────────────────────────────────────────

    def _visit(self, node: AnnotatedNode, inherited_type: Optional[str] = None):
        nt = node.node_type

        if nt == "PROGRAMA":
            self._visit_children(node)

        elif nt == "MAIN":
            self._visit_children(node)

        elif nt == "DECLARACIONES":
            self._visit_children(node)

        elif nt == "SENTENCIAS":
            self._visit_children(node)

        elif nt == "DECL_VAR":
            self._visit_decl(node)

        elif nt == "ASIGNACION":
            self._visit_assign(node)

        elif nt in ("IF", "MIENTRAS", "HACER_MIENTRAS"):
            self._visit_children(node)

        elif nt in ("CONDICION",):
            self._visit_condition(node)

        elif nt in ("ENTONCES", "SINO", "CUERPO"):
            self._visit_children(node)

        elif nt == "ENTRADA":
            self._visit_input(node)

        elif nt == "SALIDA":
            self._visit_children(node)

        elif nt in ("OP_SUMA", "OP_MULT", "OP_POT"):
            self._visit_arithmetic(node)

        elif nt == "OP_REL":
            self._visit_relational(node)

        elif nt == "OP_LOGICO":
            self._visit_logical(node)

        elif nt == "ID":
            self._visit_id(node, inherited_type)

        elif nt == "NUMERO":
            node.inferred_type = "int"
            try:
                node.const_value = int(node.value)
            except (ValueError, TypeError):
                pass

        elif nt == "REAL":
            node.inferred_type = "float"
            try:
                node.const_value = float(node.value)
            except (ValueError, TypeError):
                pass

        elif nt == "BOOL":
            node.inferred_type = "bool"
            node.const_value = node.value in ("true", "True", True)

        elif nt == "CADENA":
            node.inferred_type = "string"

        else:
            # Nodo desconocido: visitar hijos por si acaso
            self._visit_children(node)

    def _visit_children(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

    # ── Declaración de variables ───────────────────────────────────

    def _visit_decl(self, node: AnnotatedNode):
        """
        DECL_VAR → primer hijo TIPO, resto ID
        """
        if not node.children:
            return

        tipo_node = node.children[0]
        raw_type  = tipo_node.value or tipo_node.node_type
        dtype = _normalize_type(raw_type.lower() if raw_type else "int")
        tipo_node.inferred_type = dtype
        node.declared_type      = dtype

        for ch in node.children[1:]:
            if ch.node_type == "ID":
                ch.declared_type  = dtype
                ch.inferred_type  = dtype
                err = self.symbol_table.insert(
                    ch.value, dtype, ch.line or 0, ch.column or 0
                )
                if err:
                    sem_err = SemanticError("DUPLICATE", err, ch.line, ch.column)
                    self.errors.append(sem_err)
                    ch.sem_errors.append(str(sem_err))
                    ch.is_valid = False

    # ── Asignación ────────────────────────────────────────────────

    def _visit_assign(self, node: AnnotatedNode):
        """
        ASIGNACION con value=nombre_variable, hijo 0 = expresión rhs
        """
        var_name = node.value
        entry = self.symbol_table.lookup(var_name) if var_name else None

        if var_name and not entry:
            sem_err = SemanticError(
                "UNDECLARED",
                f"Variable '{var_name}' no declarada.",
                node.line, node.column
            )
            self.errors.append(sem_err)
            node.sem_errors.append(str(sem_err))
            node.is_valid = False

        # Visitar la expresión del lado derecho (no el ID lhs si lo hay como hijo)
        rhs = None
        for ch in node.children:
            # Si el hijo es el ID de la misma variable lhs, no re-visitar como expr
            if ch.node_type == "ID" and ch.value == var_name:
                ch.inferred_type = entry.dtype if entry else None
                ch.declared_type = entry.dtype if entry else None
                continue
            self._visit(ch)
            rhs = ch

        # Tomar el último hijo como rhs inferido
        expr_node = node.children[-1] if node.children else None
        expr_type = expr_node.inferred_type if expr_node else None
        node.inferred_type = expr_type

        if entry and expr_type:
            lhs_type = entry.dtype
            if lhs_type == expr_type:
                pass  # OK
            elif lhs_type == "float" and expr_type == "int":
                # int → float: conversión implícita permitida
                if expr_node:
                    expr_node.conversion = "int_to_float"
            elif lhs_type == "int" and expr_type == "float":
                sem_err = SemanticError(
                    "TYPE_MISMATCH",
                    f"Asignación: variable '{var_name}' es 'int' "
                    f"pero la expresión es 'float'. Pérdida de precisión.",
                    node.line, node.column
                )
                self.errors.append(sem_err)
                node.sem_errors.append(str(sem_err))
                node.is_valid = False
            elif lhs_type == "bool" and expr_type != "bool":
                sem_err = SemanticError(
                    "TYPE_MISMATCH",
                    f"Asignación: variable '{var_name}' es 'bool' "
                    f"pero la expresión es '{expr_type}'.",
                    node.line, node.column
                )
                self.errors.append(sem_err)
                node.sem_errors.append(str(sem_err))
                node.is_valid = False
            elif lhs_type != "bool" and expr_type == "bool":
                sem_err = SemanticError(
                    "TYPE_MISMATCH",
                    f"Asignación: variable '{var_name}' es '{lhs_type}' "
                    f"pero la expresión es 'bool'.",
                    node.line, node.column
                )
                self.errors.append(sem_err)
                node.sem_errors.append(str(sem_err))
                node.is_valid = False

    # ── Condición ─────────────────────────────────────────────────

    def _visit_condition(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)
            expr_type = ch.inferred_type
            if expr_type and expr_type not in ("bool", "int", "float"):
                sem_err = SemanticError(
                    "INVALID_CONDITION",
                    f"Condición debe ser booleana o numérica, se obtuvo '{expr_type}'.",
                    ch.line, ch.column
                )
                self.errors.append(sem_err)
                node.sem_errors.append(str(sem_err))
                node.is_valid = False
        node.inferred_type = "bool"

    # ── Operaciones aritméticas ────────────────────────────────────

    def _visit_arithmetic(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

        types = [ch.inferred_type for ch in node.children if ch.inferred_type]
        if len(types) < 2:
            # Unario (negativo)
            node.inferred_type = types[0] if types else "int"
            return

        t1, t2 = types[0], types[1]
        result = _coerce(t1, t2)
        if result is None:
            sem_err = SemanticError(
                "OPERATOR_MISUSE",
                f"Operación aritmética inválida entre '{t1}' y '{t2}'.",
                node.line, node.column
            )
            self.errors.append(sem_err)
            node.sem_errors.append(str(sem_err))
            node.is_valid = False
            node.inferred_type = "int"
        else:
            if t1 != t2:
                # marcar conversión en el hijo int
                for ch in node.children:
                    if ch.inferred_type == "int":
                        ch.conversion = "int_to_float"
            node.inferred_type = result

    # ── Operaciones relacionales ───────────────────────────────────

    def _visit_relational(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

        types = [ch.inferred_type for ch in node.children if ch.inferred_type]
        if len(types) >= 2:
            t1, t2 = types[0], types[1]
            if not (t1 in (*_NUMERIC, "bool") and t2 in (*_NUMERIC, "bool")):
                sem_err = SemanticError(
                    "OPERATOR_MISUSE",
                    f"Comparación inválida entre '{t1}' y '{t2}'.",
                    node.line, node.column
                )
                self.errors.append(sem_err)
                node.sem_errors.append(str(sem_err))
                node.is_valid = False

        node.inferred_type = "bool"

    # ── Operaciones lógicas ───────────────────────────────────────

    def _visit_logical(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

        op = node.value
        types = [ch.inferred_type for ch in node.children if ch.inferred_type]

        if op == "!":
            t = types[0] if types else None
            if t and t not in ("bool", "int", "float"):
                sem_err = SemanticError(
                    "OPERATOR_MISUSE",
                    f"Operador '!' aplicado a tipo '{t}' (se esperaba bool/int).",
                    node.line, node.column
                )
                self.errors.append(sem_err)
                node.sem_errors.append(str(sem_err))
                node.is_valid = False
        else:
            for t in types:
                if t and t not in ("bool", "int", "float"):
                    sem_err = SemanticError(
                        "OPERATOR_MISUSE",
                        f"Operador lógico '{op}' aplicado a tipo '{t}'.",
                        node.line, node.column
                    )
                    self.errors.append(sem_err)
                    node.sem_errors.append(str(sem_err))
                    node.is_valid = False
                    break

        node.inferred_type = "bool"

    # ── Identificador ─────────────────────────────────────────────

    def _visit_id(self, node: AnnotatedNode, inherited_type: Optional[str]):
        name = node.value
        if not name:
            return
        entry = self.symbol_table.lookup(name)
        if entry:
            node.inferred_type   = entry.dtype
            node.declared_type   = entry.dtype
        else:
            # Solo reportar error si no es contexto de declaración
            if inherited_type is None:
                sem_err = SemanticError(
                    "UNDECLARED",
                    f"Variable '{name}' utilizada sin declarar.",
                    node.line, node.column
                )
                self.errors.append(sem_err)
                node.sem_errors.append(str(sem_err))
                node.is_valid = False

    # ── Entrada (cin) ─────────────────────────────────────────────

    def _visit_input(self, node: AnnotatedNode):
        for ch in node.children:
            if ch.node_type == "ID":
                entry = self.symbol_table.lookup(ch.value)
                if entry:
                    ch.inferred_type = entry.dtype
                else:
                    sem_err = SemanticError(
                        "UNDECLARED",
                        f"Variable '{ch.value}' en 'cin' no declarada.",
                        ch.line, ch.column
                    )
                    self.errors.append(sem_err)
                    ch.sem_errors.append(str(sem_err))
                    ch.is_valid = False
