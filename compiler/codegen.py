# compiler/codegen.py — Generador de código TM (Tiny Machine)
"""
Recorre el árbol anotado y emite instrucciones para la máquina TM.

Registros TM:
  pc  = 7   contador de programa (auto-incrementado)
  mp  = 6   puntero de pila temporal (crece hacia abajo; inicia en MEMSIZE-1)
  gp  = 5   puntero a variables globales (Memory[gp+offset])
  ac  = 0   acumulador principal
  ac1 = 1   acumulador secundario
  r2,r3,r4  auxiliares (potencia y reescalado de reales)

Instrucciones:
  emitRO:  op  r,s,t       (p.ej. ADD 0,1,0 → r0 = r1 + r0)
  emitRM:  op  r,d(s)      (p.ej. LD 0,2(5) → r0 = Mem[r5+2])

Convenciones de direccionamiento:
  - Variables → una palabra por variable, offset 0-based relativo a gp, en orden
    de declaración. Cada ámbito de bloque (then/else/while/do) abre su propio
    espacio de nombres, así que una variable interna puede ocultar a una externa.
  - Temporales en pila → ST 0,0(6) / LDA 6,-1(6) para push
                       → LDA 6,1(6) / LD 1,0(6)  para pop into r1
  - Saltos relativos:  LDA 7,d(7) → pc += d  (d = target - curr - 1)
  - Saltos condicionales: JLT/JLE/JGT/JGE/JEQ/JNE  r,d(7)

Tipos:
  - int / bool → entero tal cual (bool: 0 = false, 1 = true).
  - float → punto fijo con factor SCALE (ver compiler/fixed_point.py). El
    análisis semántico anota `conversion = int_to_float` en los operandos
    enteros de operaciones mixtas; aquí se materializa como  n * SCALE.
      +, -, comparaciones   → directo
      *                     → a*b / SCALE
      /                     → a*SCALE / b
      ^ (exponente entero)  → multiplicaciones sucesivas con reescalado
  - cin float → INF (lee decimal en punto fijo); cout float → OUTF.
  - cout con texto → LDC + OUTC por carácter; cada cout termina con OUTNL.
  (INF, OUTF, OUTC y OUTNL son extensiones didácticas de tm_simulator.py.)

Modo TM estándar / extendido:
  - ESTÁNDAR (por defecto): sólo emite las instrucciones del tm.c de Louden
    (HALT IN OUT ADD SUB MUL DIV LD ST LDA LDC JLT JLE JGT JGE JEQ JNE). No
    emite OUTNL (Louden imprime cada OUT en su renglón) y expande  a % b  como
    a - (a/b)*b.
  - EXTENDIDO: se usa automáticamente si el programa usa reales o cadenas
    (INF/OUTF/OUTC/OUTNL) o si se pide con standard=False (entonces % es MOD).
  `extensions_used` lista las instrucciones no estándar del último .tm generado.
  Ambos modos comienzan con el prólogo de Louden:  LD 6,0(0) / ST 0,0(0).
"""
from __future__ import annotations
from compiler.annotated_ast import AnnotatedNode
from compiler.fixed_point import SCALE, to_fixed
from compiler.symbol_table import SymbolTable
from compiler.type_checker import FLOAT, INT_TO_FLOAT, normalize_type


# TM register aliases
AC  = 0
AC1 = 1
GP  = 5
MP  = 6
PC  = 7
R2, R3, R4 = 2, 3, 4      # auxiliares

# Instrucciones que NO existen en el tm.c de Louden (sólo las ejecuta el simulador del IDE)
EXT_OPS = frozenset({"INF", "OUTF", "OUTC", "OUTNL", "MOD"})


class _Inst:
    __slots__ = ("addr", "op", "args", "comment")
    def __init__(self, addr, op, args, comment=""):
        self.addr = addr
        self.op = op
        self.args = args
        self.comment = comment

    def render(self) -> str:
        if self.comment:
            return f"{self.addr:4d}: {self.op:<6} {self.args:<18} * {self.comment}"
        return f"{self.addr:4d}: {self.op:<6} {self.args}"


class CodeGenerator:

    def __init__(self, symbol_table: SymbolTable | None = None,
                 standard: bool | None = None):
        """standard=None → automático (estándar salvo que haga falta una extensión);
        standard=False → fuerza el modo extendido (MOD y OUTNL aunque no hagan falta)."""
        self._standard = standard
        # La tabla de símbolos del análisis queda como respaldo: identificadores
        # que el árbol usa sin declarar (árbol parcial) toman su tipo de ahí.
        self._symbols = symbol_table
        self._insts: list[_Inst] = []
        self._loc: int = 0                       # próxima dirección disponible
        self._scopes: list[dict] = [{}]          # pila de ámbitos: nombre → (offset, tipo)
        self._slots: int = 0                     # próximas palabras de memoria libres
        self._extended: bool = standard is False # ¿se emiten extensiones (MOD, OUTNL)?
        self._ext_found: set = set()             # extensiones emitidas en la pasada actual
        self._needs_ext: bool = False            # el programa exige modo extendido

    @property
    def extensions_used(self) -> list[str]:
        """Instrucciones no estándar presentes en el último .tm generado."""
        return sorted(self._ext_found)

    # ── Variables y ámbitos ───────────────────────────────────────
    def _declare(self, name: str, dtype: str, scope: dict | None = None) -> tuple:
        scope = self._scopes[-1] if scope is None else scope
        if name not in scope:                    # redeclaración: se ignora (error semántico)
            scope[name] = (self._slots, dtype)
            self._slots += 1
        return scope[name]

    def _resolve(self, name: str, fallback_type: str | None = None) -> tuple:
        """(offset, tipo) de la variable visible más interna con ese nombre."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        entry = self._symbols.lookup(name) if self._symbols is not None else None
        dtype = entry.dtype if entry else normalize_type(fallback_type or "int")
        return self._declare(name, dtype, self._scopes[0])

    def _push_scope(self):
        self._scopes.append({})

    def _pop_scope(self):
        self._scopes.pop()

    # ── Emisión de instrucciones ──────────────────────────────────
    def _emitRO(self, op: str, r: int, s: int, t: int, comment: str = "") -> int:
        if op in EXT_OPS:
            self._ext_found.add(op)
        addr = self._loc
        self._insts.append(_Inst(addr, op, f"{r},{s},{t}", comment))
        self._loc += 1
        return addr

    def _emitRM(self, op: str, r: int, d: int, s: int, comment: str = "") -> int:
        addr = self._loc
        self._insts.append(_Inst(addr, op, f"{r},{d}({s})", comment))
        self._loc += 1
        return addr

    def _skip(self) -> int:
        """Reserva una instrucción vacía (NOP) para relleno posterior."""
        addr = self._loc
        self._insts.append(_Inst(addr, "LDA", f"7,0(7)", "placeholder"))
        self._loc += 1
        return addr

    def _fill_jump(self, addr: int, target: int, cond: str = "LDA",
                   reg: int = AC, comment: str = ""):
        """Rellena la instrucción en `addr` con un salto hacia `target`."""
        d = target - (addr + 1)
        inst = self._insts[addr]
        inst.op = cond
        inst.args = f"{reg},{d}({PC})" if cond != "LDA" else f"{PC},{d}({PC})"
        if comment:
            inst.comment = comment

    def _jump_back(self, target: int, comment: str = ""):
        """Salto incondicional hacia una dirección ya emitida."""
        self._emitRM("LDA", PC, target - (self._loc + 1), PC, comment)

    # ── Pila de temporales ────────────────────────────────────────
    def _push_ac(self, comment: str = "push ac"):
        """ST 0,0(6); LDA 6,-1(6)"""
        self._emitRM("ST", AC, 0, MP, comment)
        self._emitRM("LDA", MP, -1, MP, "mp--")

    def _pop_ac1(self, comment: str = "pop into ac1"):
        """LDA 6,1(6); LD 1,0(6)"""
        self._emitRM("LDA", MP, 1, MP, "mp++")
        self._emitRM("LD", AC1, 0, MP, comment)

    # ── Punto de entrada ─────────────────────────────────────────
    def generate(self, root: AnnotatedNode) -> list[str]:
        self._extended = self._standard is False
        self._emit_program(root)
        if not self._extended and self._needs_ext:
            # reales o cadenas: no caben en la TM estándar → segunda pasada extendida
            self._extended = True
            self._emit_program(root)
        return [inst.render() for inst in self._insts]

    def _emit_program(self, root: AnnotatedNode):
        self._insts = []
        self._loc = 0
        self._scopes = [{}]
        self._slots = 0
        self._ext_found = set()
        self._needs_ext = False
        # Prólogo de Louden: mp = dMem[0] (= último address) y se limpia dMem[0]
        self._emitRM("LD", MP, 0, AC, "mp = dMem[0] (tope de memoria)")
        self._emitRM("ST", AC, 0, AC, "limpia dMem[0]")
        self._cgen(root)
        self._emitRO("HALT", 0, 0, 0, "fin del programa")

    # ── Generador recursivo (sentencias) ─────────────────────────
    def _cgen(self, node: AnnotatedNode | None):
        if node is None:
            return
        nt = node.node_type

        if nt in ("PROGRAMA", "DECLARACIONES", "SENTENCIAS", "MAIN"):
            for ch in node.children:
                self._cgen(ch)

        elif nt in ("ENTONCES", "SINO", "CUERPO"):
            self._push_scope()                   # ámbito de bloque
            for ch in node.children:
                self._cgen(ch)
            self._pop_scope()

        elif nt == "DECL_VAR":
            self._cgen_decl(node)

        elif nt == "ASIGNACION":
            self._cgen_assign(node)

        elif nt == "ENTRADA":
            self._cgen_entrada(node)

        elif nt == "SALIDA":
            self._cgen_salida(node)

        elif nt == "IF":
            self._cgen_if(node)

        elif nt == "MIENTRAS":
            self._cgen_while(node)

        elif nt == "HACER_MIENTRAS":
            self._cgen_do_while(node)

        else:
            # Nodo de expresión suelto — generar de todos modos
            for ch in node.children:
                self._cgen(ch)

    # ── Declaración: reserva una palabra por variable ─────────────
    def _cgen_decl(self, node: AnnotatedNode):
        if not node.children:
            return
        dtype = normalize_type(node.children[0].value)
        for ch in node.children[1:]:
            if ch.node_type == "ID":
                self._declare(ch.value, dtype)

    # ── Asignación ────────────────────────────────────────────────
    def _cgen_assign(self, node: AnnotatedNode):
        var = node.value
        rhs = node.children[1] if len(node.children) > 1 else None
        if rhs is None:
            return
        self._cgen_expr(rhs)
        off, _ = self._resolve(var, node.inferred_type)
        self._emitRM("ST", AC, off, GP, f"store {var}")

    # ── Entrada (cin) ─────────────────────────────────────────────
    def _cgen_entrada(self, node: AnnotatedNode):
        for ch in node.children:
            if ch.node_type == "ID":
                off, dtype = self._resolve(ch.value, ch.inferred_type)
                if dtype == FLOAT:
                    self._needs_ext = True
                    self._emitRO("INF", AC, 0, 0, f"read real → {ch.value} (x{SCALE})")
                else:
                    self._emitRO("IN", AC, 0, 0, f"read → {ch.value}")
                self._emitRM("ST", AC, off, GP, f"store {ch.value}")

    # ── Salida (cout) ─────────────────────────────────────────────
    def _cgen_salida(self, node: AnnotatedNode):
        prev_number = False
        for ch in node.children:
            if ch.node_type == "CADENA":
                self._needs_ext = True            # el texto exige OUTC/OUTNL
                self._emit_string(ch.value)
                prev_number = False
                continue
            if prev_number and self._extended:    # dos números seguidos → un espacio
                self._emitRM("LDC", AC, ord(" "), 0, "char ' '")
                self._emitRO("OUTC", AC, 0, 0, "write char")
            self._cgen_expr(ch)
            if self._is_float(ch):
                self._needs_ext = True
                self._emitRO("OUTF", AC, 0, 0, "write real")
            else:
                self._emitRO("OUT", AC, 0, 0, "write ac")
            prev_number = True
        if self._extended:                        # Louden no tiene OUTNL: cada OUT ya es un renglón
            self._emitRO("OUTNL", 0, 0, 0, "fin de renglón")

    def _emit_string(self, raw: str | None):
        """Texto de cout: un LDC + OUTC por carácter (el .tm es autocontenido)."""
        text = raw or ""
        if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
            text = text[1:-1]
        i = 0
        while i < len(text):
            two = text[i:i + 2]
            if two == "\\n":
                self._emitRO("OUTNL", 0, 0, 0, "newline (\\n)")
                i += 2
                continue
            if two == "\\t":
                ch, i = "\t", i + 2
            else:
                ch, i = text[i], i + 1
            shown = ch if ch.isprintable() else repr(ch)
            self._emitRM("LDC", AC, ord(ch), 0, f"char '{shown}'")
            self._emitRO("OUTC", AC, 0, 0, "write char")

    # ── IF ────────────────────────────────────────────────────────
    def _cgen_if(self, node: AnnotatedNode):
        cond_node = node.children[0] if node.children else None
        then_node = node.children[1] if len(node.children) > 1 else None
        else_node = node.children[2] if len(node.children) > 2 else None

        # Evalúa condición → ac
        self._cgen_condition(cond_node)

        # Reserva salto hacia else
        jmp_else = self._skip()

        # Then block
        if then_node:
            self._cgen(then_node)

        if else_node:
            # Salto al final (from end of then)
            jmp_end = self._skip()
            # Rellena salto a else
            self._fill_jump(jmp_else, self._loc, "JEQ", AC,
                            "if false → else")
            # Else block
            self._cgen(else_node)
            # Rellena salto a end
            self._fill_jump(jmp_end, self._loc, "LDA", comment="jump past else")
        else:
            # Sin else: rellenar salto al final
            self._fill_jump(jmp_else, self._loc, "JEQ", AC,
                            "if false → end")

    # ── WHILE ─────────────────────────────────────────────────────
    def _cgen_while(self, node: AnnotatedNode):
        cond_node = node.children[0] if node.children else None
        body_node = node.children[1] if len(node.children) > 1 else None

        loop_start = self._loc

        # Evalúa condición → ac
        self._cgen_condition(cond_node)

        # Salto a fin si condición falsa
        jmp_end = self._skip()

        # Cuerpo
        if body_node:
            self._cgen(body_node)

        # Salto incondicional al inicio
        self._jump_back(loop_start, "back to loop test")

        # Rellena salto al final
        self._fill_jump(jmp_end, self._loc, "JEQ", AC, "while false → end")

    # ── DO-WHILE / DO-UNTIL ───────────────────────────────────────
    def _cgen_do_while(self, node: AnnotatedNode):
        body_node = node.children[0] if node.children else None
        cond_node = node.children[-1] if len(node.children) > 1 else None

        loop_start = self._loc
        if body_node:
            self._cgen(body_node)

        # Evalúa condición → ac (1 = verdadero, 0 = falso)
        self._cgen_condition(cond_node)

        if node.value == "until":
            # do ... until(c): repite mientras c sea FALSA
            d = loop_start - (self._loc + 1)
            self._emitRM("JEQ", AC, d, PC, "do-until: if false → body")
        else:
            # do ... while(c): repite mientras c sea VERDADERA
            d = loop_start - (self._loc + 1)
            self._emitRM("JNE", AC, d, PC, "do-while: if true → body")

    # ── Condiciones ───────────────────────────────────────────────
    def _cgen_condition(self, cond_node: AnnotatedNode | None):
        """Evalúa una CONDICION (o expresión); deja 0 en ac si es FALSA, ≠0 si VERDADERA."""
        node = cond_node
        if node is not None and node.node_type == "CONDICION":
            node = node.children[0] if node.children else None
        if node is None:
            self._emitRM("LDC", AC, 0, 0, "null condition → false")
            return
        self._cgen_cond_expr(node)

    def _bool_from_jump(self, jmp_op: str, comment: str):
        """
        Convierte un salto condicional sobre ac en 0/1:
            <jmp_op> ac → true ; ac = 0 ; salta fin ; true: ac = 1
        """
        jmp_true  = self._skip()
        self._emitRM("LDC", AC, 0, 0, "false")
        jmp_after = self._skip()
        true_loc = self._loc
        self._emitRM("LDC", AC, 1, 0, "true")
        end_loc = self._loc
        self._fill_jump(jmp_true, true_loc, jmp_op, AC, comment)
        self._fill_jump(jmp_after, end_loc, "LDA", comment="skip true")

    def _cgen_cond_expr(self, node: AnnotatedNode | None):
        """
        Evalúa una expresión booleana/relacional.
        Deja 1 (verdadero) ó 0 (falso) en ac.
        """
        if node is None:
            self._emitRM("LDC", AC, 0, 0, "null → false")
            return

        nt = node.node_type

        if nt == "OP_REL":
            left  = node.children[0] if len(node.children) > 0 else None
            right = node.children[1] if len(node.children) > 1 else None
            self._cgen_expr(left)   # ac = left
            self._push_ac("save left")
            self._cgen_expr(right)  # ac = right
            self._pop_ac1("restore left into ac1")
            self._emitRO("SUB", AC, AC1, AC, "left - right")
            jmp_op = {
                "<":  "JLT", "<=": "JLE",
                ">":  "JGT", ">=": "JGE",
                "==": "JEQ", "!=": "JNE",
            }.get(node.value, "JNE")
            self._bool_from_jump(jmp_op, f"rel {node.value} → true")

        elif nt == "OP_LOGICO":
            if node.value == "!":
                self._cgen_cond_expr(node.children[0] if node.children else None)
                self._bool_from_jump("JEQ", "not: 0→true")
            elif node.value == "&&":
                self._cgen_cond_expr(node.children[0] if len(node.children) > 0 else None)
                jmp_false = self._skip()
                self._cgen_cond_expr(node.children[1] if len(node.children) > 1 else None)
                jmp_after = self._skip()
                false_loc = self._loc
                self._emitRM("LDC", AC, 0, 0, "and false")
                end_loc = self._loc
                self._fill_jump(jmp_false, false_loc, "JEQ", AC, "&& short-circuit")
                self._fill_jump(jmp_after, end_loc, "LDA", comment="and done")
            elif node.value == "||":
                self._cgen_cond_expr(node.children[0] if len(node.children) > 0 else None)
                jmp_true = self._skip()
                self._cgen_cond_expr(node.children[1] if len(node.children) > 1 else None)
                jmp_after = self._skip()
                true_loc = self._loc
                self._emitRM("LDC", AC, 1, 0, "or true")
                end_loc = self._loc
                self._fill_jump(jmp_true, true_loc, "JNE", AC, "|| short-circuit")
                self._fill_jump(jmp_after, end_loc, "LDA", comment="or done")
            else:
                self._cgen_expr(node)
        else:
            # ID / literal booleano / CONDICION anidada: ≠0 es verdadero
            self._cgen_expr(node)

    # ── Expresiones ───────────────────────────────────────────────
    @staticmethod
    def _is_float(node: AnnotatedNode | None) -> bool:
        """¿El valor que deja `node` en ac está en punto fijo (ya convertido)?"""
        return node is not None and (node.inferred_type == FLOAT
                                     or node.conversion == INT_TO_FLOAT)

    def _cgen_expr(self, node: AnnotatedNode | None):
        """Evalúa la expresión y deja el resultado en ac (aplicando int→float)."""
        self._expr(node)
        if (node is not None and node.conversion == INT_TO_FLOAT
                and node.node_type != "NUMERO"):       # NUMERO ya se carga escalado
            self._emitRM("LDC", AC1, SCALE, 0, "scale factor")
            self._emitRO("MUL", AC, AC, AC1, "int → float")

    def _expr(self, node: AnnotatedNode | None):
        if node is None:
            self._emitRM("LDC", AC, 0, 0, "null expr")
            return

        nt = node.node_type

        if nt == "NUMERO":
            try:
                val = int(node.value)
            except (ValueError, TypeError):
                val = 0
            if node.conversion == INT_TO_FLOAT:
                self._emitRM("LDC", AC, val * SCALE, 0, f"const {val} → float")
            else:
                self._emitRM("LDC", AC, val, 0, f"const {val}")

        elif nt == "REAL":
            val = to_fixed(node.value)
            self._emitRM("LDC", AC, val, 0, f"const float {node.value} (x{SCALE})")

        elif nt == "BOOL":
            val = 1 if str(node.value).lower() == "true" else 0
            self._emitRM("LDC", AC, val, 0, f"bool {node.value}")

        elif nt == "ID":
            off, _ = self._resolve(node.value, node.inferred_type)
            self._emitRM("LD", AC, off, GP, f"load {node.value}")

        elif nt in ("OP_SUMA", "OP_MULT", "OP_POT"):
            self._cgen_arith(node)

        elif nt in ("OP_REL", "OP_LOGICO"):
            self._cgen_cond_expr(node)

        elif nt == "CADENA":
            self._emitRM("LDC", AC, 0, 0, "string (solo válida en cout)")

        elif nt == "CONDICION":
            self._cgen_condition(node)

        else:
            # Nodo desconocido
            self._emitRM("LDC", AC, 0, 0, f"unknown {nt}")

    def _cgen_arith(self, node: AnnotatedNode):
        left  = node.children[0] if len(node.children) > 0 else None
        right = node.children[1] if len(node.children) > 1 else None
        op = node.value or {"OP_POT": "^"}.get(node.node_type, node.node_type)
        self._cgen_expr(left)
        self._push_ac(f"push left of {op}")
        self._cgen_expr(right)
        self._pop_ac1(f"pop left → ac1 for {op}")

        is_float = node.inferred_type == FLOAT

        if op == "^":
            self._emit_power(is_float)
        elif is_float and op == "*":
            self._emitRO("MUL", AC, AC1, AC, "ac1 * ac")
            self._emitRM("LDC", R4, SCALE, 0, "scale factor")
            self._emitRO("DIV", AC, AC, R4, "rescale: / SCALE")
        elif is_float and op == "/":
            self._emitRM("LDC", R4, SCALE, 0, "scale factor")
            self._emitRO("MUL", AC1, AC1, R4, "ac1 * SCALE")
            self._emitRO("DIV", AC, AC1, AC, "(ac1 * SCALE) / ac")
        elif op == "%" and not self._extended:
            # a % b = a - (a/b)*b  con sólo DIV/MUL/SUB (a en ac1, b en ac; r2 temporal)
            self._emitRO("DIV", R2, AC1, AC, "r2 = a / b")
            self._emitRO("MUL", R2, R2, AC, "r2 = (a / b) * b")
            self._emitRO("SUB", AC, AC1, R2, "ac = a - (a/b)*b  (a % b)")
        else:
            tm_op = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD"}.get(op, "ADD")
            self._emitRO(tm_op, AC, AC1, AC, f"ac1 {op} ac → ac")

    def _emit_power(self, is_float: bool):
        """
        ac1 ^ ac  (base en ac1, exponente en ac) por multiplicaciones sucesivas.
        r2 = contador, r3 = acumulado. Exponente ≤ 0 → resultado 1.
        En float el exponente (escalado) se trunca a su parte entera.
        """
        if is_float:
            self._emitRM("LDC", R4, SCALE, 0, "scale factor")
            self._emitRO("DIV", R2, AC, R4, "r2 = exponente (entero)")
            self._emitRM("LDC", R3, SCALE, 0, "r3 = 1.0 (resultado)")
        else:
            self._emitRM("LDA", R2, 0, AC, "r2 = exponente")
            self._emitRM("LDC", R3, 1, 0, "r3 = 1 (resultado)")
        loop = self._loc
        jmp_end = self._skip()
        self._emitRO("MUL", R3, R3, AC1, "r3 = r3 * base")
        if is_float:
            self._emitRO("DIV", R3, R3, R4, "rescale: / SCALE")
        self._emitRM("LDA", R2, -1, R2, "exp--")
        self._jump_back(loop, "repetir potencia")
        self._fill_jump(jmp_end, self._loc, "JLE", R2, "exp<=0 → fin potencia")
        self._emitRM("LDA", AC, 0, R3, "ac = resultado")
