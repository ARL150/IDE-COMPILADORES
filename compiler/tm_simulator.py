# compiler/tm_simulator.py — Simulador de la Máquina TM (Tiny Machine)
"""
Ejecuta el archivo .tm producido por el generador de código.

Instrucciones estándar de la TM:
  RO (registro–registro):
    ADD r,s,t  →  r = s + t
    SUB r,s,t  →  r = s - t
    MUL r,s,t  →  r = s * t
    DIV r,s,t  →  r = s / t  (entero, trunca hacia cero; t=0 → error)
    MOD r,s,t  →  r = s % t  (signo del dividendo, como en C; t=0 → error)
    IN  r,0,0  →  r = siguiente valor de entrada (entero)
    OUT r,0,0  →  imprime reg[r] (entero)
    HALT 0,0,0 →  detiene la máquina

  RM (registro–memoria):
    LD  r,d(s) →  r = Mem[reg[s]+d]
    LDA r,d(s) →  r = reg[s]+d          (load address)
    LDC r,d(s) →  r = d                  (load constant; s ignorado)
    ST  r,d(s) →  Mem[reg[s]+d] = r

    JLT r,d(s) →  if reg[r]<0:  pc = reg[s]+d
    JLE r,d(s) →  if reg[r]<=0: pc = reg[s]+d
    JGT r,d(s) →  if reg[r]>0:  pc = reg[s]+d
    JGE r,d(s) →  if reg[r]>=0: pc = reg[s]+d
    JEQ r,d(s) →  if reg[r]==0: pc = reg[s]+d
    JNE r,d(s) →  if reg[r]!=0: pc = reg[s]+d

Extensiones didácticas (la TM original sólo tiene IN/OUT enteros; estas tres
cubren los reales y el texto del lenguaje y están documentadas en el README):
    INF   r,0,0 →  r = siguiente entrada leída como REAL, en punto fijo
                   (1.5 → 15000; ver compiler/fixed_point.py)
    OUTF  r,0,0 →  imprime reg[r] como real (15000 → 1.5)
    OUTC  r,0,0 →  imprime el carácter con código reg[r] (texto de cout)
    OUTNL 0,0,0 →  termina el renglón de salida actual

Salida: si el programa contiene OUTNL (modo extendido), OUT / OUTF / OUTC agregan
texto al renglón en curso y OUTNL lo cierra (el generador emite un OUTNL al final de
cada cout). Si NO contiene OUTNL (modo TM estándar), cada OUT es su propio renglón,
como en el tm.c de Louden.

Estado inicial (igual que el tm.c de Louden):
  todos los registros = 0, dMem[0] = MEMSIZE–1 y el resto de la memoria = 0.
  El programa generado comienza con  LD 6,0(0) / ST 0,0(0)  para fijar mp.

Registros:
  0–4  de propósito general   (ac=0, ac1=1)
  5    gp  (global pointer)   0
  6    mp  (memory pointer)   0 al arrancar; el prólogo lo carga con MEMSIZE–1
  7    pc  (program counter)  0

Parámetros de la máquina:
  MEMSIZE = 1024
  REGS    = 8
  MAX_STEPS = 5_000_000  (guarda contra bucles infinitos)

Los enteros del simulador no desbordan (Python); una TM real usaría 32 bits.
"""
from __future__ import annotations
import re

from compiler.fixed_point import format_fixed, to_fixed, to_int

MEMSIZE   = 1024
REGS      = 8
MAX_STEPS = 5_000_000
PC = 7
MP = 6
GP = 5

# Formatos de instrucción
_RM_OPS = {"LD", "LDA", "LDC", "ST", "JLT", "JLE", "JGT", "JGE", "JEQ", "JNE"}
_RO_OPS = {"HALT", "ADD", "SUB", "MUL", "DIV", "MOD", "IN", "INF", "OUT",
           "OUTF", "OUTC", "OUTNL", "NOP"}


# ── Clase de resultado ────────────────────────────────────────────

class SimResult:
    def __init__(self):
        self.output: list[str] = []   # líneas de salida
        self.inputs_used: list[str] = []
        self.steps: int = 0
        self.error: str | None = None
        self.halted: bool = False
        self.trace: list[str] = []    # opcional (vacío por defecto)


# ── Simulador ─────────────────────────────────────────────────────

class TMSimulator:

    # ── Parseo de instrucciones ───────────────────────────────────
    def load(self, tm_text: str) -> list[tuple]:
        """
        Carga el texto del archivo .tm y devuelve una lista indexada de
        instrucciones: list[(formato, op, a, b, c)]  donde el índice = dirección.
          RM → ("RM", op, r, d, s)      RO → ("RO", op, r, s, t)
        """
        prog: dict[int, tuple] = {}
        for raw in tm_text.splitlines():
            line = raw.strip()
            if not line or line.startswith("*") or line.startswith(";"):
                continue
            # Extraer número de instrucción
            m_addr = re.match(r"^\s*(\d+)\s*:", line)
            if not m_addr:
                continue
            addr = int(m_addr.group(1))
            rest = line[m_addr.end():]

            m_ro = re.match(
                r"\s*(\w+)\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", rest, re.IGNORECASE)
            m_rm = re.match(
                r"\s*(\w+)\s+(\d+)\s*,\s*(-?\d+)\s*\(\s*(\d+)\s*\)", rest, re.IGNORECASE)

            if m_rm:
                prog[addr] = ("RM", m_rm.group(1).upper(), int(m_rm.group(2)),
                              int(m_rm.group(3)), int(m_rm.group(4)))
            elif m_ro:
                prog[addr] = ("RO", m_ro.group(1).upper(), int(m_ro.group(2)),
                              int(m_ro.group(3)), int(m_ro.group(4)))

        # Convertir a lista (huecos → NOP)
        if not prog:
            return []
        max_addr = max(prog.keys())
        return [prog.get(i, ("RO", "NOP", 0, 0, 0)) for i in range(max_addr + 1)]

    # ── Ejecución ─────────────────────────────────────────────────
    def run(self, tm_text: str,
            input_values: list | None = None,
            trace: bool = False,
            max_steps: int = MAX_STEPS) -> SimResult:
        """
        Ejecuta el programa TM.

        Parameters
        ----------
        tm_text      : contenido completo del archivo .tm
        input_values : valores (int, float o texto '1.5') que IN / INF consumen
                       en orden; si se agotan se lee 0.
        trace        : si True, registra cada instrucción ejecutada
        """
        prog = self.load(tm_text)
        res  = SimResult()

        if not prog:
            res.error = "Programa vacío o sin instrucciones válidas."
            return res

        # Estado
        regs = [0] * REGS
        mem  = [0] * MEMSIZE
        mem[0] = MEMSIZE - 1          # como tm.c: el prólogo LD 6,0(0) lo lee
        # ¿Modo estándar? sin OUTNL cada OUT cierra su propio renglón
        auto_newline = not any(i[1] == "OUTNL" for i in prog)

        input_idx = 0
        in_vals   = input_values or []
        line_buf: list[str] = []      # renglón de salida en curso
        n_prog = len(prog)

        def next_input() -> tuple:
            """(texto usado, valor) de la siguiente entrada."""
            nonlocal input_idx
            if input_idx < len(in_vals):
                raw = in_vals[input_idx]
                input_idx += 1
                return str(raw), raw
            res.inputs_used.append("0 (sin entrada)")
            return None, 0

        step = 0
        while step < max_steps:
            pc_now = regs[PC]
            if pc_now < 0 or pc_now >= n_prog:
                res.error = f"PC fuera de rango: {pc_now}"
                break

            kind, op, a, b, c = prog[pc_now]
            regs[PC] = pc_now + 1   # auto-incremento antes de ejecutar
            step += 1

            if trace:
                res.trace.append(
                    f"[{step - 1:5d}] pc={pc_now}  {op}  regs={list(regs[:4])}")

            if kind == "RM":
                r, d, s = a, b, c
                if op == "LD":
                    addr = regs[s] + d
                    if 0 <= addr < MEMSIZE:
                        regs[r] = mem[addr]
                    else:
                        res.error = f"LD fuera de memoria: addr={addr} en paso {step - 1}"
                        break
                elif op == "ST":
                    addr = regs[s] + d
                    if 0 <= addr < MEMSIZE:
                        mem[addr] = regs[r]
                    else:
                        res.error = f"ST fuera de memoria: addr={addr} en paso {step - 1}"
                        break
                elif op == "LDC":
                    regs[r] = d              # r = d (constante)
                elif op == "LDA":
                    regs[r] = regs[s] + d    # r = s + d (sin acceso a memoria)
                elif op in _RM_OPS:          # saltos condicionales
                    v = regs[r]
                    if ((op == "JLT" and v <  0) or (op == "JLE" and v <= 0) or
                        (op == "JGT" and v >  0) or (op == "JGE" and v >= 0) or
                        (op == "JEQ" and v == 0) or (op == "JNE" and v != 0)):
                        regs[PC] = regs[s] + d
                else:
                    res.error = f"Instrucción desconocida '{op}' en pc={pc_now}"
                    break
                continue

            # ── formato RO ──
            r, s, t = a, b, c
            if op == "ADD":
                regs[r] = regs[s] + regs[t]
            elif op == "SUB":
                regs[r] = regs[s] - regs[t]
            elif op == "MUL":
                regs[r] = regs[s] * regs[t]
            elif op == "DIV" or op == "MOD":
                num, den = regs[s], regs[t]
                if den == 0:
                    what = "División" if op == "DIV" else "Módulo"
                    res.error = (f"{what} por cero en paso {step - 1} (pc={pc_now})")
                    break
                q = abs(num) // abs(den)
                if (num < 0) != (den < 0):
                    q = -q
                regs[r] = q if op == "DIV" else num - den * q
            elif op == "HALT":
                res.halted = True
                break
            elif op == "IN" or op == "INF":
                used, raw = next_input()
                if used is not None:
                    res.inputs_used.append(used)
                regs[r] = to_int(raw) if op == "IN" else to_fixed(raw)
                shown = str(regs[r]) if op == "IN" else format_fixed(regs[r])
                res.output.append(f"[Entrada] → {shown}")
            elif op == "OUT":
                line_buf.append(str(regs[r]))
                if auto_newline:
                    res.output.append("".join(line_buf))
                    line_buf.clear()
            elif op == "OUTF":
                line_buf.append(format_fixed(regs[r]))
            elif op == "OUTC":
                line_buf.append(chr(regs[r]) if 0 <= regs[r] <= 0x10FFFF else "?")
            elif op == "OUTNL":
                res.output.append("".join(line_buf))
                line_buf.clear()
            elif op == "NOP":
                pass
            else:
                res.error = f"Instrucción desconocida '{op}' en pc={pc_now}"
                break
        else:
            res.error = (f"Límite de {max_steps} pasos alcanzado "
                         f"(posible bucle infinito).")

        if line_buf:                      # salida pendiente sin OUTNL final
            res.output.append("".join(line_buf))
        res.steps = step
        return res
