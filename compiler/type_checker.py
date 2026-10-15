# compiler/type_checker.py — Reglas de tipos del lenguaje (Fase 3)
"""
Reglas puras de tipos (no recorren el árbol; el recorrido está en
semantic_analyzer.py).

TIPOS:  int, float (alias: real), bool.  Internos: string (solo literales de
cout) y error (resultado de una expresión inválida; evita errores en cascada).

OPERADORES
  + - * /     int/float. int∘int → int (la división entera trunca); si algún
              operando es float → float.
  %           solo int ∘ int → int.
  ^           int/float. int^int → int; si hay float → float.
  < <= > >=   solo numéricos → bool.
  == !=       numérico con numérico, o bool con bool → bool.
  && || !     solo bool → bool.
  Una CADENA solo es válida como argumento de cout.

CONVERSIONES
  Válida:    int → float (implícita), en operandos mixtos y en asignación.
             Se registra en el árbol anotado como conversion="int_to_float".
  Inválidas: float → int sin cast (el lenguaje no tiene cast)  → INVALID_CONVERSION
             bool ↔ int/float en asignación                    → TYPE_MISMATCH
             bool en operadores aritméticos                    → OPERATOR_MISUSE
             comparar bool con int/float (== !=)               → TYPE_MISMATCH

CONDICIONES (if / while / do-while): deben ser bool → INVALID_CONDITION.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from compiler import semantic_errors as E

INT, FLOAT, BOOL, STRING, ERROR = "int", "float", "bool", "string", "error"
NUMERIC = (INT, FLOAT)

ARITH_OPS   = ("+", "-", "*", "/", "%", "^")
ORDER_OPS   = ("<", "<=", ">", ">=")
EQUALITY_OPS = ("==", "!=")

INT_TO_FLOAT = "int_to_float"


def normalize_type(raw) -> str:
    """Normaliza el lexema de tipo: 'real' → 'float'."""
    t = (raw or "").lower()
    return FLOAT if t in ("real", "real_kw") else t


@dataclass
class CheckResult:
    result_type: str
    category: Optional[str] = None     # None → sin error nuevo (puede ser ERROR "silencioso")
    message:  Optional[str] = None
    convert:  tuple = ()               # índices de operandos que requieren int→float

    @property
    def has_error(self) -> bool:
        return self.category is not None


def _silent() -> CheckResult:
    return CheckResult(ERROR)


def _string_misuse(op: str) -> CheckResult:
    return CheckResult(
        ERROR, E.OPERATOR_MISUSE,
        f"Una cadena no es válida como operando de '{op}'; "
        f"solo se permite como argumento de cout.")


# ── Aritméticos ───────────────────────────────────────────────────
def check_arithmetic(op: str, t1: str, t2: str) -> CheckResult:
    if ERROR in (t1, t2):
        return _silent()
    if STRING in (t1, t2):
        return _string_misuse(op)
    if BOOL in (t1, t2):
        return CheckResult(
            ERROR, E.OPERATOR_MISUSE,
            f"El operador aritmético '{op}' no admite operandos 'bool' "
            f"(operandos: '{t1}' y '{t2}').")
    if op == "%" and FLOAT in (t1, t2):
        return CheckResult(
            ERROR, E.OPERATOR_MISUSE,
            f"El operador '%' solo admite operandos 'int' "
            f"(operandos: '{t1}' y '{t2}').")
    if t1 == INT and t2 == INT:
        return CheckResult(INT)
    convert = tuple(i for i, t in enumerate((t1, t2)) if t == INT)
    return CheckResult(FLOAT, convert=convert)


# ── Relacionales ──────────────────────────────────────────────────
def check_relational(op: str, t1: str, t2: str) -> CheckResult:
    if ERROR in (t1, t2):
        return _silent()
    if STRING in (t1, t2):
        return _string_misuse(op)
    if op in ORDER_OPS:
        if BOOL in (t1, t2):
            return CheckResult(
                ERROR, E.OPERATOR_MISUSE,
                f"El operador relacional '{op}' solo admite operandos numéricos "
                f"(operandos: '{t1}' y '{t2}').")
    else:  # == !=
        if (t1 == BOOL) != (t2 == BOOL):
            return CheckResult(
                ERROR, E.TYPE_MISMATCH,
                f"No se puede comparar '{t1}' con '{t2}' usando '{op}'.")
    convert = ()
    if t1 != t2 and t1 in NUMERIC and t2 in NUMERIC:
        convert = tuple(i for i, t in enumerate((t1, t2)) if t == INT)
    return CheckResult(BOOL, convert=convert)


# ── Lógicos ───────────────────────────────────────────────────────
def check_logical(op: str, types: list) -> CheckResult:
    if ERROR in types:
        return _silent()
    for t in types:
        if t == STRING:
            return _string_misuse(op)
    bad = [t for t in types if t != BOOL]
    if bad:
        return CheckResult(
            ERROR, E.OPERATOR_MISUSE,
            f"El operador lógico '{op}' requiere operandos 'bool', "
            f"se obtuvo '{bad[0]}'.")
    return CheckResult(BOOL)


# ── Asignación ────────────────────────────────────────────────────
def check_assignment(name: str, target: str, source: str) -> CheckResult:
    if ERROR in (target, source) or target == source:
        return CheckResult(target if target != ERROR else source)
    if target == FLOAT and source == INT:
        return CheckResult(FLOAT, convert=(0,))
    if target == INT and source == FLOAT:
        return CheckResult(
            ERROR, E.INVALID_CONVERSION,
            f"Conversión no válida: no se puede asignar 'float' a '{name}' "
            f"(tipo 'int') sin conversión explícita; se perdería precisión.")
    return CheckResult(
        ERROR, E.TYPE_MISMATCH,
        f"Incompatibilidad de tipos en la asignación: '{name}' es '{target}' "
        f"pero la expresión es '{source}'.")


# ── Condiciones ───────────────────────────────────────────────────
def check_condition(t: str, what: str = "La condición") -> CheckResult:
    if t in (BOOL, ERROR):
        return CheckResult(BOOL if t == BOOL else ERROR)
    return CheckResult(
        ERROR, E.INVALID_CONDITION,
        f"{what} debe ser de tipo 'bool', se obtuvo '{t}'.")


# ── Plegado de constantes ─────────────────────────────────────────
MAX_CONST_EXPONENT = 1024


def is_zero(value) -> bool:
    return value is not None and not isinstance(value, bool) and value == 0


def _trunc_div(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def fold_arithmetic(op: str, a, b, result_type: str):
    """
    Calcula a∘b en compilación. Retorna None si no se puede calcular
    (división/módulo entre cero, exponente negativo/enorme, desbordamiento…).
    Nunca lanza excepciones.
    """
    if a is None or b is None or result_type not in NUMERIC:
        return None
    try:
        if result_type == FLOAT:
            a, b = float(a), float(b)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                return None
            return a / b if result_type == FLOAT else _trunc_div(a, b)
        if op == "%":
            if b == 0 or result_type != INT:
                return None
            return a - b * _trunc_div(a, b)
        if op == "^":
            if result_type == INT:
                if b < 0 or b > MAX_CONST_EXPONENT:
                    return None
                return a ** b
            r = a ** b
            return None if isinstance(r, complex) else r
    except (ArithmeticError, ValueError, TypeError):
        return None
    return None


def fold_relational(op: str, a, b):
    if a is None or b is None:
        return None
    return {
        "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b,
        "==": a == b, "!=": a != b,
    }.get(op)


def fold_logical(op: str, values: list):
    if any(v is None for v in values):
        return None
    if op == "!":
        return (not values[0]) if values else None
    if len(values) < 2:
        return None
    return (values[0] and values[1]) if op == "&&" else (values[0] or values[1])
