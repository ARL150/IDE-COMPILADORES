# compiler/semantic_errors.py — Errores del análisis semántico (Fase 3)
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

# Categorías de error semántico
UNDECLARED         = "UNDECLARED"           # identificador no declarado
DUPLICATE          = "DUPLICATE"            # declaración duplicada en el mismo ámbito
TYPE_MISMATCH      = "TYPE_MISMATCH"        # incompatibilidad de tipos (asignación / comparación)
INVALID_CONVERSION = "INVALID_CONVERSION"   # conversión de tipos no válida (p. ej. float → int)
OPERATOR_MISUSE    = "OPERATOR_MISUSE"      # operador con operandos de tipo inválido
INVALID_CONDITION  = "INVALID_CONDITION"    # condición que no es bool
DIVISION_BY_ZERO   = "DIVISION_BY_ZERO"     # división / módulo entre cero constante

ALL_CATEGORIES = (
    UNDECLARED, DUPLICATE, TYPE_MISMATCH, INVALID_CONVERSION,
    OPERATOR_MISUSE, INVALID_CONDITION, DIVISION_BY_ZERO,
)


@dataclass
class SemanticError:
    category: str
    message:  str
    line:     Optional[int] = None
    column:   Optional[int] = None

    def location(self) -> str:
        if self.line is None:
            return ""
        loc = f"línea {self.line}"
        if self.column is not None:
            loc += f", col {self.column}"
        return loc

    def __str__(self):
        loc = self.location()
        return f"[{self.category}]" + (f" [{loc}]" if loc else "") + f" {self.message}"
