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

ERR = "error"   # tipo especial: se propaga sin reportar errores adicionales


class AnnotatedNode:
    def __init__(self, source: ASTNode):
        self.node_type   = source.node_type
        self.value       = source.value
        self.line        = source.line
        self.column      = source.column
        self.children:   list[AnnotatedNode] = []
        # Atributos semánticos
        self.inferred_type:  Optional[str]  = None   # sintetizado (type)
        self.declared_type:  Optional[str]  = None   # heredado (dtype)
        self.const_value     = None                   # sintetizado (val), solo si es constante
        self.conversion:     Optional[str]  = None   # sintetizado (conv): "int_to_float"
        self.sem_errors:     list[str]      = []
        self.is_valid:       bool           = True
        # Nodo que el parser inserta por azúcar sintáctico (NUMERO '1' de x++/x--,
        # NUMERO '0' del menos unario): no existe en el código fuente.
        self.synthetic:      bool           = False


def _copy_tree(node: ASTNode) -> AnnotatedNode:
    an = AnnotatedNode(node)
    for ch in node.children:
        if ch is not None:
            an.children.append(_copy_tree(ch))
    _mark_synthetic(an)
    return an


def _mark_synthetic(an: AnnotatedNode):
    """
    El parser construye '-x' como OP_SUMA('-', NUMERO '0', x) y 'x++' como
    OP_SUMA('+', ID, NUMERO '1'), y a esos NUMERO les pone la posición del
    OPERADOR. Un operando real nunca ocupa la posición de su propio operador,
    así que coincidir en (línea, columna) identifica al nodo sintético.
    """
    if an.node_type != "OP_SUMA" or len(an.children) != 2:
        return
    left, right = an.children
    if (left.node_type == "NUMERO" and left.value == "0" and an.value == "-"
            and (left.line, left.column) == (an.line, an.column)):
        left.synthetic = True
    elif (right.node_type == "NUMERO" and right.value == "1"
            and (right.line, right.column) == (an.line, an.column)):
        right.synthetic = True


# ─────────────────────────────────────────────────────────────────
# Utilidades de tipos y plegado de constantes
# ─────────────────────────────────────────────────────────────────

_NUMERIC = {"int", "float"}


def _normalize_type(t: str) -> str:
    """Normaliza 'real' → 'float'."""
    return "float" if t in ("real", "REAL_KW") else t


def _is_num(t) -> bool:
    return t in _NUMERIC


def _trunc_div(a: int, b: int) -> int:
    """División entera truncando hacia cero (estilo C), exacta para enteros grandes."""
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def _fold_arith(op: str, a, b, rtype: str):
    """Evalúa una operación aritmética constante. None si no es evaluable."""
    try:
        if op == "+":
            r = a + b
        elif op == "-":
            r = a - b
        elif op == "*":
            r = a * b
        elif op == "/":
            if b == 0:
                return None
            r = _trunc_div(a, b) if rtype == "int" else a / b
        elif op == "%":
            if b == 0:
                return None
            r = a - b * _trunc_div(a, b)          # signo del dividendo, como C
        elif op == "^":
            if rtype == "int":
                if b < 0 or (abs(a) > 1 and b > 4096):
                    return None
                r = a ** b
            else:
                r = float(a) ** float(b)
                if isinstance(r, complex):
                    return None
        else:
            return None
        return float(r) if rtype == "float" else r
    except (OverflowError, ZeroDivisionError, ValueError):
        return None


def _fold_rel(op: str, a, b):
    return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b,
            "==": a == b, "!=": a != b}[op]


# ─────────────────────────────────────────────────────────────────
# SemanticAnalyzer
# ─────────────────────────────────────────────────────────────────

class SemanticAnalyzer:
    """
    Análisis semántico de una pasada sobre el AST (recorrido en profundidad).

    Reglas de tipos (resumen):
      * Condiciones de if/while/do: solo bool.
      * && || !: operandos bool, resultado bool.
      * < <= > >=: numéricos. == !=: numérico/numérico o bool/bool. Resultado bool.
      * + - *: numéricos (int,int→int; con float→float). /: igual, pero int/int
        trunca hacia cero. %: solo int. ^: int^int→int, en otro caso float.
      * Asignación: igual tipo, o int→float (conversión implícita anotada).
      * Tipo especial "error": se propaga sin reportar errores en cascada.
    """

    def __init__(self):
        self.symbol_table  = SymbolTable()
        self.errors:       list[SemanticError] = []
        self._annotated_root: Optional[AnnotatedNode] = None
        self._seen_errors: set = set()

    # ── Entrada pública ───────────────────────────────────────────

    def analyze(self, ast: ASTNode) -> AnnotatedNode:
        """Analiza el AST y retorna el árbol anotado."""
        self.symbol_table  = SymbolTable()
        self.errors        = []
        self._seen_errors  = set()
        root = _copy_tree(ast)
        self._visit(root)
        self._annotated_root = root
        return root

    # ── Reporte de errores ────────────────────────────────────────

    def _report(self, node: AnnotatedNode, category: str, message: str,
                line=None, col=None):
        """Registra un error semántico (sin duplicados exactos) y marca el nodo."""
        line = node.line if line is None else line
        col  = node.column if col is None else col
        key = (category, line, col, message)
        if key in self._seen_errors:
            return
        self._seen_errors.add(key)
        err = SemanticError(category, message, line, col)
        self.errors.append(err)
        node.sem_errors.append(str(err))
        node.is_valid = False

    def _set_type(self, node: AnnotatedNode, t: Optional[str]):
        node.inferred_type = t

    # ── Despacho principal ────────────────────────────────────────

    def _visit(self, node: AnnotatedNode, inherited_type: Optional[str] = None):
        nt = node.node_type

        if nt in ("PROGRAMA", "MAIN", "DECLARACIONES", "SENTENCIAS",
                  "ENTONCES", "SINO", "CUERPO"):
            self._visit_children(node)

        elif nt == "DECL_VAR":
            self._visit_decl(node)

        elif nt == "ASIGNACION":
            self._visit_assign(node)

        elif nt in ("IF", "MIENTRAS", "HACER_MIENTRAS"):
            self._visit_control(node)

        elif nt == "CONDICION":          # solo si aparece fuera de un control
            self._visit_condition(node, "condición")

        elif nt == "ENTRADA":
            self._visit_input(node)

        elif nt == "SALIDA":
            self._visit_output(node)

        elif nt in ("OP_SUMA", "OP_MULT", "OP_POT"):
            self._visit_arithmetic(node)

        elif nt == "OP_REL":
            self._visit_relational(node)

        elif nt == "OP_LOGICO":
            self._visit_logical(node)

        elif nt == "ID":
            self._visit_id(node, inherited_type)

        elif nt == "NUMERO":
            self._set_type(node, "int")
            try:
                node.const_value = int(node.value)
            except (ValueError, TypeError):
                pass

        elif nt == "REAL":
            self._set_type(node, "float")
            try:
                node.const_value = float(node.value)
            except (ValueError, TypeError):
                pass

        elif nt == "BOOL":
            self._set_type(node, "bool")
            node.const_value = node.value in ("true", "True", True)

        elif nt == "CADENA":
            self._set_type(node, "string")

        else:
            # Nodo desconocido: visitar hijos por si acaso
            self._visit_children(node)

    def _visit_children(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

    # ── Sentencias de control ─────────────────────────────────────

    _CONTROL_NAME = {"IF": "if", "MIENTRAS": "while", "HACER_MIENTRAS": "do"}

    def _visit_control(self, node: AnnotatedNode):
        kind = self._CONTROL_NAME[node.node_type]
        for ch in node.children:
            if ch.node_type == "CONDICION":
                self._visit_condition(ch, kind)
            else:
                self._visit(ch)

    def _visit_condition(self, node: AnnotatedNode, kind: str):
        """Condición de if / while / do: debe ser bool."""
        if not node.children:               # condición vacía (error sintáctico)
            self._set_type(node, ERR)
            return
        for ch in node.children:
            self._visit(ch)
        t = node.children[0].inferred_type
        if t in (None, ERR):
            self._set_type(node, ERR)
        elif t == "bool":
            self._set_type(node, "bool")
        else:
            ch = node.children[0]
            self._report(
                node, "INVALID_CONDITION",
                f"La condición del '{kind}' debe ser bool, se obtuvo '{t}'.",
                ch.line, ch.column)
            self._set_type(node, ERR)

    # ── Declaración de variables ───────────────────────────────────

    def _visit_decl(self, node: AnnotatedNode):
        """DECL_VAR → primer hijo TIPO, resto ID."""
        if not node.children:
            return

        tipo_node = node.children[0]
        raw_type  = tipo_node.value or tipo_node.node_type
        dtype = _normalize_type(raw_type.lower() if raw_type else "int")
        self._set_type(tipo_node, dtype)

        for ch in node.children[1:]:
            if ch.node_type == "ID":
                ch.declared_type = dtype
                self._set_type(ch, dtype)
                err = self.symbol_table.insert(
                    ch.value, dtype, ch.line or 0, ch.column or 0
                )
                if err:
                    self._report(ch, "DUPLICATE", err)

    # ── Asignación ────────────────────────────────────────────────

    def _visit_assign(self, node: AnnotatedNode):
        """
        ASIGNACION con value=nombre_variable. children[0] = ID (lhs),
        children[1] = expresión (ausente en 'x = ;').
        """
        var_name = node.value
        entry = self.symbol_table.lookup(var_name) if var_name else None
        lhs = node.children[0] if (node.children and node.children[0].node_type == "ID") else None
        rhs = node.children[1] if len(node.children) > 1 else None

        if var_name and not entry:
            self._report(node, "UNDECLARED", f"Variable '{var_name}' no declarada.")
        if lhs is not None:
            self._set_type(lhs, entry.dtype if entry else ERR)

        if rhs is None:
            # 'x = ;' — el sintáctico ya lo acepta/reporta; no hay tipos que comparar
            return
        self._visit(rhs)
        expr_type = rhs.inferred_type
        self._set_type(node, expr_type)

        if entry is None or expr_type in (None, ERR):
            return                          # error ya reportado o propagado

        lhs_type = entry.dtype
        if lhs_type == expr_type:
            node.const_value = rhs.const_value
        elif lhs_type == "float" and expr_type == "int":
            node.conversion = "int_to_float"
            if not rhs.synthetic:
                rhs.conversion = "int_to_float"
            node.const_value = (float(rhs.const_value)
                                if rhs.const_value is not None else None)
        elif lhs_type == "int" and expr_type == "float":
            self._report(
                node, "TYPE_MISMATCH",
                f"Conversión no válida: no se puede asignar 'float' a la variable "
                f"'{var_name}' de tipo 'int' (pérdida de precisión).")
        else:
            self._report(
                node, "TYPE_MISMATCH",
                f"Asignación incompatible: la variable '{var_name}' es '{lhs_type}' "
                f"pero la expresión es '{expr_type}'.")

    # ── Operaciones aritméticas ────────────────────────────────────

    def _promote(self, a: AnnotatedNode, b: AnnotatedNode):
        """Si se mezclan int y float, anota int_to_float en el operando int."""
        if {a.inferred_type, b.inferred_type} == {"int", "float"}:
            for ch in (a, b):
                if ch.inferred_type == "int" and not ch.synthetic:
                    ch.conversion = "int_to_float"

    def _visit_arithmetic(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

        op = node.value
        kids = node.children
        if len(kids) != 2:                  # operando faltante (error sintáctico)
            self._set_type(node, ERR)
            return
        left, right = kids
        t1, t2 = left.inferred_type, right.inferred_type

        # Menos unario (-x) y postfijo (x++ / x--): el parser los codifica con
        # un operando sintético; se tratan como operadores de un solo operando.
        if left.synthetic or right.synthetic:
            operand = right if left.synthetic else left
            t = operand.inferred_type
            sym = f"unario '{op}'" if left.synthetic else f"'{op}{op}'"
            if t in (None, ERR):
                self._set_type(node, ERR)
            elif not _is_num(t):
                self._report(node, "OPERATOR_MISUSE",
                             f"Operador {sym} no aplicable a tipo '{t}'.")
                self._set_type(node, ERR)
            else:
                self._set_type(node, t)
                if left.synthetic and operand.const_value is not None:
                    node.const_value = -operand.const_value
            for s in (left, right):
                if s.synthetic:
                    self._set_type(s, "int")
            return

        if t1 in (None, ERR) or t2 in (None, ERR):
            self._set_type(node, ERR)
            return

        # Validación de tipos por operador
        if op == "%":
            if t1 != "int" or t2 != "int":
                self._report(node, "OPERATOR_MISUSE",
                             f"El operador '%' solo se aplica a enteros, "
                             f"se obtuvo '{t1}' y '{t2}'.")
                self._set_type(node, ERR)
                return
        elif not (_is_num(t1) and _is_num(t2)):
            self._report(node, "OPERATOR_MISUSE",
                         f"Operación aritmética '{op}' inválida entre '{t1}' y '{t2}'.")
            self._set_type(node, ERR)
            return

        rtype = "int" if (t1 == "int" and t2 == "int") else "float"
        if rtype == "float":
            self._promote(left, right)
        self._set_type(node, rtype)

        # División (o módulo) entre cero constante
        if op in ("/", "%") and right.const_value is not None and right.const_value == 0:
            self._report(node, "OPERATOR_MISUSE", "Error: división entre cero.")
            return

        a, b = left.const_value, right.const_value
        if a is not None and b is not None:
            node.const_value = _fold_arith(op, a, b, rtype)

    # ── Operaciones relacionales ───────────────────────────────────

    def _visit_relational(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

        kids = node.children
        if len(kids) != 2:
            self._set_type(node, ERR)
            return
        left, right = kids
        t1, t2 = left.inferred_type, right.inferred_type
        if t1 in (None, ERR) or t2 in (None, ERR):
            self._set_type(node, ERR)
            return

        op = node.value
        if op in ("==", "!="):
            ok = (_is_num(t1) and _is_num(t2)) or (t1 == t2 == "bool")
        else:
            ok = _is_num(t1) and _is_num(t2)
        if not ok:
            self._report(node, "OPERATOR_MISUSE",
                         f"Comparación '{op}' inválida entre '{t1}' y '{t2}'.")
        else:
            self._promote(left, right)
            if left.const_value is not None and right.const_value is not None:
                node.const_value = _fold_rel(op, left.const_value, right.const_value)
        self._set_type(node, "bool")

    # ── Operaciones lógicas ───────────────────────────────────────

    def _visit_logical(self, node: AnnotatedNode):
        for ch in node.children:
            self._visit(ch)

        op = node.value
        kids = node.children
        expected = 1 if op == "!" else 2
        if len(kids) != expected:
            self._set_type(node, ERR)
            return
        types = [ch.inferred_type for ch in kids]
        if any(t in (None, ERR) for t in types):
            self._set_type(node, ERR)
            return

        bad = [t for t in types if t != "bool"]
        if bad:
            if op == "!":
                msg = f"El operador '!' requiere un operando bool, se obtuvo '{bad[0]}'."
            else:
                msg = (f"El operador '{op}' requiere operandos bool, "
                       f"se obtuvo '{types[0]}' y '{types[1]}'.")
            self._report(node, "OPERATOR_MISUSE", msg)
        else:
            vals = [ch.const_value for ch in kids]
            if all(v is not None for v in vals):
                if op == "!":
                    node.const_value = not vals[0]
                elif op == "&&":
                    node.const_value = vals[0] and vals[1]
                else:
                    node.const_value = vals[0] or vals[1]
        self._set_type(node, "bool")

    # ── Identificador ─────────────────────────────────────────────

    def _visit_id(self, node: AnnotatedNode, inherited_type: Optional[str] = None):
        name = node.value
        if not name:
            self._set_type(node, ERR)
            return
        entry = self.symbol_table.lookup(name)
        if entry:
            self._set_type(node, entry.dtype)
        else:
            self._report(node, "UNDECLARED", f"Variable '{name}' no declarada.")
            self._set_type(node, ERR)

    # ── Entrada / salida ──────────────────────────────────────────

    def _visit_input(self, node: AnnotatedNode):
        for ch in node.children:
            if ch.node_type == "ID":
                entry = self.symbol_table.lookup(ch.value)
                if entry:
                    self._set_type(ch, entry.dtype)
                else:
                    self._report(ch, "UNDECLARED",
                                 f"Variable '{ch.value}' no declarada (en 'cin').")
                    self._set_type(ch, ERR)

    def _visit_output(self, node: AnnotatedNode):
        """cout: cada hijo se tipa; una CADENA es válida."""
        for ch in node.children:
            self._visit(ch)
