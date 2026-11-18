# compiler/codegen.py — Generador de código TM (Tiny Machine)
"""
Recorre el árbol anotado y emite instrucciones para la máquina TM.

Registros TM:
  pc  = 7   contador de programa (auto-incrementado)
  mp  = 6   puntero de pila temporal (crece hacia abajo; inicia en MEMSIZE-1)
  gp  = 5   puntero a variables globales (Memory[gp+offset])
  ac  = 0   acumulador principal
  ac1 = 1   acumulador secundario

Instrucciones:
  emitRO:  op  r,s,t       (p.ej. ADD 0,1,0 → r0 = r1 + r0)
  emitRM:  op  r,d(s)      (p.ej. LD 0,2(5) → r0 = Mem[r5+2])

Convenciones de direccionamiento:
  - Variables globales → offset 0-based relativo a gp (una palabra por var)
  - Temporales en pila → ST 0,0(6) / LDA 6,-1(6) para push
                       → LDA 6,1(6) / LD 1,0(6)  para pop into r1
  - Saltos relativos:  LDA 7,d(7) → pc += d  (d = target - curr - 1)
  - Saltos condicionales: JLT/JLE/JGT/JGE/JEQ/JNE  r,d(7)
"""
from __future__ import annotations
from compiler.annotated_ast import AnnotatedNode
from compiler.symbol_table import SymbolTable


# TM register aliases
AC  = 0
AC1 = 1
GP  = 5
MP  = 6
PC  = 7


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

    def __init__(self, symbol_table: SymbolTable):
        self._insts: list[_Inst] = []
        self._loc: int = 0          # próxima dirección disponible
        self._var: dict[str, int] = {}  # nombre → offset desde gp
        self._build_var_map(symbol_table)

    # ── Mapa de variables ─────────────────────────────────────────
    def _build_var_map(self, st: SymbolTable):
        for idx, entry in enumerate(st.all_entries()):
            self._var[entry.name] = idx

    def _var_offset(self, name: str) -> int:
        return self._var.get(name, 0)

    # ── Emisión de instrucciones ──────────────────────────────────
    def _emitRO(self, op: str, r: int, s: int, t: int, comment: str = "") -> int:
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
        self._insts = []
        self._loc = 0
        self._cgen(root)
        self._emitRO("HALT", 0, 0, 0, "fin del programa")
        return [inst.render() for inst in self._insts]

    # ── Generador recursivo ───────────────────────────────────────
    def _cgen(self, node: AnnotatedNode | None):
        if node is None:
            return
        nt = node.node_type

        if nt in ("PROGRAMA", "DECLARACIONES", "SENTENCIAS",
                  "ENTONCES", "SINO", "CUERPO", "MAIN"):
            for ch in node.children:
                self._cgen(ch)

        elif nt == "DECL_VAR":
            pass  # espacio ya reservado en el mapa

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

    # ── Asignación ────────────────────────────────────────────────
    def _cgen_assign(self, node: AnnotatedNode):
        var = node.value
        rhs = node.children[1] if len(node.children) > 1 else None
        if rhs is None:
            return
        self._cgen_expr(rhs)
        off = self._var_offset(var)
        self._emitRM("ST", AC, off, GP, f"store {var}")

    # ── Entrada (cin) ─────────────────────────────────────────────
    def _cgen_entrada(self, node: AnnotatedNode):
        for ch in node.children:
            if ch.node_type == "ID":
                self._emitRO("IN", AC, 0, 0, f"read → {ch.value}")
                off = self._var_offset(ch.value)
                self._emitRM("ST", AC, off, GP, f"store {ch.value}")

    # ── Salida (cout) ─────────────────────────────────────────────
    def _cgen_salida(self, node: AnnotatedNode):
        for ch in node.children:
            if ch.node_type == "CADENA":
                # TM no soporta strings — ignorar o emitir comentario
                self._emitRO("OUTNL", 0, 0, 0, f"string: {ch.value}")
                continue
            self._cgen_expr(ch)
            self._emitRO("OUT", AC, 0, 0, "write ac")

    # ── IF ────────────────────────────────────────────────────────
    def _cgen_if(self, node: AnnotatedNode):
        cond_node = node.children[0] if node.children else None
        then_node = node.children[1] if len(node.children) > 1 else None
        else_node = node.children[2] if len(node.children) > 2 else None

        # Evalúa condición → ac
        self._cgen_condition(cond_node, node.children[0].children[0]
                             if cond_node and cond_node.children else None)

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
        self._cgen_condition(cond_node,
                             cond_node.children[0] if cond_node and cond_node.children else None)

        # Salto a fin si condición falsa
        jmp_end = self._skip()

        # Cuerpo
        if body_node:
            self._cgen(body_node)

        # Salto incondicional al inicio
        d = loop_start - (self._loc + 1)
        self._emitRM("LDA", PC, d, PC, "back to loop test")

        # Rellena salto al final
        self._fill_jump(jmp_end, self._loc, "JEQ", AC, "while false → end")

    # ── DO-WHILE ──────────────────────────────────────────────────
    def _cgen_do_while(self, node: AnnotatedNode):
        body_node = node.children[0] if node.children else None
        cond_node = node.children[-1] if len(node.children) > 1 else None

        loop_start = self._loc
        if body_node:
            self._cgen(body_node)

        # Evalúa condición → ac (1 = verdadero, 0 = falso)
        expr = cond_node.children[0] if cond_node and cond_node.children else None
        if expr is not None:
            self._cgen_cond_expr(expr)

        # Si condición verdadera (ac != 0), volver al inicio
        d = loop_start - (self._loc + 1)
        self._emitRM("JNE", AC, d, PC, "do-while: if true → body")

    # ── Expresión de condición ────────────────────────────────────
    def _cgen_condition(self, cond_node, expr_node):
        """Evalúa la condición; deja 0 en ac si es FALSA, ≠0 si VERDADERA."""
        node = expr_node or (cond_node.children[0]
                             if cond_node and cond_node.children else cond_node)
        if node is None:
            self._emitRM("LDC", AC, 0, 0, "null condition → false")
            return
        self._cgen_cond_expr(node)

    def _cgen_cond_expr(self, node: AnnotatedNode):
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

            op = node.value
            # Reservamos 3 instrucciones: condicional, false-case, salto-after
            jmp_true  = self._skip()   # salto condicional a true-case
            # false-case
            self._emitRM("LDC", AC, 0, 0, "false")
            jmp_after = self._skip()   # salto al final
            # true-case
            true_loc = self._loc
            self._emitRM("LDC", AC, 1, 0, "true")
            end_loc = self._loc

            # Rellena el salto condicional
            cond_map = {
                "<":  "JLT", "<=": "JLE",
                ">":  "JGT", ">=": "JGE",
                "==": "JEQ", "!=": "JNE",
            }
            jmp_op = cond_map.get(op, "JNE")
            self._fill_jump(jmp_true, true_loc, jmp_op, AC,
                            f"rel {op} → true")
            self._fill_jump(jmp_after, end_loc, "LDA", comment="skip true")

        elif nt == "OP_LOGICO":
            if node.value == "!":
                self._cgen_cond_expr(node.children[0] if node.children else None)
                # NOT: (ac == 0) → 1, else 0
                jmp_true  = self._skip()
                self._emitRM("LDC", AC, 0, 0, "not false")
                jmp_after = self._skip()
                true_loc = self._loc
                self._emitRM("LDC", AC, 1, 0, "not true")
                end_loc = self._loc
                self._fill_jump(jmp_true, true_loc, "JEQ", AC, "not: 0→true")
                self._fill_jump(jmp_after, end_loc, "LDA", comment="not done")
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
            # Expresión aritmética/ID/número: evalúa como entero; ≠0 es verdadero
            self._cgen_expr(node)

    # ── Expresión aritmética ──────────────────────────────────────
    def _cgen_expr(self, node: AnnotatedNode | None):
        """Evalúa la expresión y deja el resultado en ac."""
        if node is None:
            self._emitRM("LDC", AC, 0, 0, "null expr")
            return

        nt = node.node_type

        if nt == "NUMERO":
            try:
                val = int(node.value)
            except (ValueError, TypeError):
                val = 0
            self._emitRM("LDC", AC, val, 0, f"const {val}")

        elif nt == "REAL":
            try:
                val = int(float(node.value))
            except (ValueError, TypeError):
                val = 0
            self._emitRM("LDC", AC, val, 0, f"const float {node.value}")

        elif nt == "BOOL":
            val = 1 if str(node.value).lower() == "true" else 0
            self._emitRM("LDC", AC, val, 0, f"bool {node.value}")

        elif nt == "ID":
            off = self._var_offset(node.value)
            self._emitRM("LD", AC, off, GP, f"load {node.value}")

        elif nt in ("OP_SUMA", "OP_MULT", "OP_POT"):
            left  = node.children[0] if len(node.children) > 0 else None
            right = node.children[1] if len(node.children) > 1 else None
            self._cgen_expr(left)
            self._push_ac(f"push left of {node.value}")
            self._cgen_expr(right)
            self._pop_ac1(f"pop left → ac1 for {node.value}")
            op_map = {
                "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
                "%": "MOD", "^": "MUL",   # ^ aproximado con MUL
            }
            tm_op = op_map.get(node.value, "ADD")
            self._emitRO(tm_op, AC, AC1, AC, f"ac1 {node.value} ac → ac")

        elif nt == "OP_REL":
            self._cgen_cond_expr(node)

        elif nt == "OP_LOGICO":
            self._cgen_cond_expr(node)

        elif nt == "CADENA":
            self._emitRM("LDC", AC, 0, 0, "string (not supported)")

        elif nt == "CONDICION":
            inner = node.children[0] if node.children else None
            self._cgen_cond_expr(inner)

        else:
            # Nodo desconocido
            self._emitRM("LDC", AC, 0, 0, f"unknown {nt}")
