# compiler/symbol_table.py — Tabla de símbolos con manejo de ámbitos (Fase 3)
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# Tamaño en memoria (bytes) de cada tipo.
# DIRECCIÓN / DESPLAZAMIENTO: cada variable recibe como dirección la suma de los
# tamaños de todas las variables declaradas antes que ella (asignación estática,
# en orden de declaración; la primera queda en 0). Una redeclaración no consume
# espacio y el espacio de un ámbito cerrado no se reutiliza.
TYPE_SIZES = {"int": 2, "float": 4, "bool": 1}


@dataclass
class SymbolEntry:
    name:    str
    dtype:   str                 # "int" | "float" | "bool"
    line:    int                 # línea de la declaración
    column:  int                 # columna de la declaración
    address: int = 0             # desplazamiento de memoria
    scope:   str = "global"      # nombre del ámbito donde se declaró
    # último valor conocido en compilación (None = desconocido / sin asignar)
    value: object = None
    # declaración + cada uso como (línea, columna): cada token una vez, sin deduplicar
    # por línea (y = y + 1 en la línea 9 -> "9, 9"). Una redeclaración no se registra.
    refs: list = field(default_factory=list)

    def add_reference(self, line: Optional[int], column: Optional[int] = None):
        """Registra la declaración o un uso. El mismo token no se repite."""
        if line is None:
            return
        ref = (line, column or 0)
        if ref not in self.refs:
            self.refs.append(ref)

    @property
    def lines(self) -> list:
        """Línea de cada aparición, en orden de aparición en el código fuente."""
        return [ln for ln, _ in sorted(self.refs)]

    def lines_display(self) -> str:
        """'2, 2, 3, 5'"""
        return ", ".join(str(ln) for ln in self.lines)

    def value_display(self) -> str:
        """Valor para mostrar en la tabla ('—' si no se conoce)."""
        v = self.value
        if v is None:
            return "—"
        if isinstance(v, bool):
            return "true" if v else "false"
        return repr(v)


class Scope:
    """Un ámbito: tabla nombre → SymbolEntry, con referencia al ámbito padre."""

    def __init__(self, name: str, parent: Optional["Scope"] = None):
        self.name = name
        self.parent = parent
        self.symbols: dict[str, SymbolEntry] = {}


class SymbolTable:
    """
    Tabla de símbolos real usada por el analizador semántico.

    - insert():  declaración → inserta en el ámbito actual
    - lookup():  uso de identificador → busca del ámbito actual hacia el global
    - exists():  verificación de existencia
    - enter_scope()/exit_scope(): manejo de ámbito (bloques)
    Los ámbitos cerrados se conservan para poder reportar toda la tabla.
    """

    def __init__(self):
        self._global = Scope("global")
        self._current = self._global
        self._all_scopes: list[Scope] = [self._global]
        self._next_addr = 0

    # ── Ámbitos ───────────────────────────────────────────────────
    @property
    def current_scope_name(self) -> str:
        return self._current.name

    def enter_scope(self, name: str):
        sc = Scope(name, parent=self._current)
        self._all_scopes.append(sc)
        self._current = sc

    def exit_scope(self):
        if self._current.parent is not None:
            self._current = self._current.parent

    # ── Inserción ─────────────────────────────────────────────────
    def insert(self, name: str, dtype: str, line: int, col: int):
        """
        Inserta el símbolo en el ámbito actual.
        Retorna (insertado, entrada): si ya existía en este ámbito,
        (False, entrada_previa); si no, (True, entrada_nueva).
        """
        prev = self._current.symbols.get(name)
        if prev is not None:
            return False, prev
        entry = SymbolEntry(name=name, dtype=dtype, line=line, column=col,
                            address=self._next_addr, scope=self._current.name)
        entry.add_reference(line, col)
        self._next_addr += TYPE_SIZES.get(dtype, 2)
        self._current.symbols[name] = entry
        return True, entry

    # ── Búsqueda ──────────────────────────────────────────────────
    def lookup(self, name: str) -> Optional[SymbolEntry]:
        sc = self._current
        while sc is not None:
            if name in sc.symbols:
                return sc.symbols[name]
            sc = sc.parent
        return None

    def lookup_current_scope(self, name: str) -> Optional[SymbolEntry]:
        return self._current.symbols.get(name)

    def exists(self, name: str) -> bool:
        return self.lookup(name) is not None

    # ── Consulta ──────────────────────────────────────────────────
    def all_entries(self) -> list[SymbolEntry]:
        """Todos los símbolos (de todos los ámbitos) en orden de dirección."""
        out = [e for sc in self._all_scopes for e in sc.symbols.values()]
        return sorted(out, key=lambda e: e.address)
