# compiler/fixed_point.py — Representación de reales en punto fijo
"""
La máquina TM (y su simulador) sólo opera con enteros. Los valores `float`
del lenguaje se representan como enteros escalados:

    valor_real  =  entero_almacenado / SCALE        (SCALE = 10 000)

  · 1.5      se guarda como  15000
  · 3.1416   se guarda como  31416      (4 decimales de precisión)
  · 0.3048   se guarda como   3048

Reglas de aritmética (las emite codegen.py con instrucciones TM normales):
  a + b , a - b    →  directo (ambos ya escalados)
  a * b            →  a * b / SCALE      (se trunca hacia cero)
  a / b            →  a * SCALE / b      (se trunca hacia cero)
  int → float      →  n * SCALE

Formato de salida (OUTF): hasta 4 decimales, sin ceros finales y con al
menos un decimal:   100.0   3.048   45.4545   -0.5

Este módulo lo comparten el generador (constantes), el simulador (IN real /
OUT real) y la interfaz (para leer las entradas), de modo que la conversión
exista en un solo lugar.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

DECIMALS = 4
SCALE = 10 ** DECIMALS


def to_fixed(value) -> int:
    """Convierte un número (int, float, str '1.5', Decimal) a punto fijo.

    Redondea al 4.º decimal (mitad hacia arriba). Texto inválido → 0.
    """
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return 0
    return int((d * SCALE).to_integral_value(rounding=ROUND_HALF_UP))


def to_int(value) -> int:
    """Convierte la entrada a entero (trunca decimales). Texto inválido → 0."""
    try:
        return int(Decimal(str(value).strip()))
    except (InvalidOperation, ValueError):
        return 0


def format_fixed(scaled: int) -> str:
    """Formatea un entero escalado como real: 1000000 → '100.0'."""
    sign = "-" if scaled < 0 else ""
    mag = abs(int(scaled))
    whole, frac = divmod(mag, SCALE)
    frac_txt = f"{frac:0{DECIMALS}d}".rstrip("0") or "0"
    return f"{sign}{whole}.{frac_txt}"
