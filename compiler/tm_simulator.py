# compiler/tm_simulator.py — Simulador de la Máquina TM (Tiny Machine)
"""
Ejecuta el archivo .tm producido por el generador de código.

Instrucciones soportadas:
  RO (registro–registro):
    ADD r,s,t  →  r = s + t
    SUB r,s,t  →  r = s - t
    MUL r,s,t  →  r = s * t
    DIV r,s,t  →  r = s / t  (entero)
    MOD r,s,t  →  r = s % t
    IN  r,0,0  →  r = siguiente valor de entrada (entero)
    OUT r,0,0  →  imprime reg[r]
    OUTNL r,0,0 → imprime nueva línea (extensión didáctica)
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

Registros:
  0–4  de propósito general   (ac=0, ac1=1)
  5    gp  (global pointer)   inicializado en 0
  6    mp  (memory pointer)   inicializado en MEMSIZE–1
  7    pc  (program counter)  inicializado en 0

Parámetros de la máquina:
  MEMSIZE = 1024
  REGS    = 8
  MAX_STEPS = 100_000  (guarda contra bucles infinitos)
"""
from __future__ import annotations
import re

MEMSIZE   = 1024
REGS      = 8
MAX_STEPS = 100_000
PC = 7
MP = 6
GP = 5


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
    _RO_PAT = re.compile(
        r"^\s*\d+\s*:\s*(\w+)\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*",
        re.IGNORECASE
    )
    _RM_PAT = re.compile(
        r"^\s*\d+\s*:\s*(\w+)\s+(\d+)\s*,\s*(-?\d+)\s*\(\s*(\d+)\s*\)\s*",
        re.IGNORECASE
    )

    def load(self, tm_text: str) -> list[tuple]:
        """
        Carga el texto del archivo .tm y devuelve una lista indexada de
        instrucciones: list[(op, [args...])]  donde el índice = dirección.
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
                op = m_rm.group(1).upper()
                r  = int(m_rm.group(2))
                d  = int(m_rm.group(3))
                s  = int(m_rm.group(4))
                prog[addr] = ("RM", op, r, d, s)
            elif m_ro:
                op = m_ro.group(1).upper()
                r  = int(m_ro.group(2))
                s_ = int(m_ro.group(3))
                t  = int(m_ro.group(4))
                prog[addr] = ("RO", op, r, s_, t)

        # Convertir a lista (huecos → NOP)
        if not prog:
            return []
        max_addr = max(prog.keys())
        result: list[tuple] = []
        for i in range(max_addr + 1):
            result.append(prog.get(i, ("RO", "NOP", 0, 0, 0)))
        return result

    # ── Ejecución ─────────────────────────────────────────────────
    def run(self, tm_text: str,
            input_values: list[int] | None = None,
            trace: bool = False) -> SimResult:
        """
        Ejecuta el programa TM.

        Parameters
        ----------
        tm_text      : contenido completo del archivo .tm
        input_values : enteros a usar como entrada cuando IN se ejecute
                       (None → pedir al usuario interactivamente NO está soportado;
                        se usará 0 si no hay más valores)
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
        regs[GP] = 0
        regs[MP] = MEMSIZE - 1
        regs[PC] = 0

        input_idx = 0
        in_vals   = input_values or []

        for step in range(MAX_STEPS):
            pc_now = regs[PC]
            if pc_now < 0 or pc_now >= len(prog):
                res.error = f"PC fuera de rango: {pc_now}"
                break

            inst = prog[pc_now]
            regs[PC] += 1   # auto-incremento antes de ejecutar

            kind = inst[0]
            op   = inst[1]

            if trace:
                res.trace.append(f"[{step:5d}] pc={pc_now}  {op}  regs={list(regs[:4])}")

            if kind == "RO":
                _, _, r, s, t = inst
                if op == "HALT":
                    res.halted = True
                    break
                elif op == "ADD":
                    regs[r] = regs[s] + regs[t]
                elif op == "SUB":
                    regs[r] = regs[s] - regs[t]
                elif op == "MUL":
                    regs[r] = regs[s] * regs[t]
                elif op == "DIV":
                    if regs[t] == 0:
                        res.error = f"División por cero en paso {step} (pc={pc_now})"
                        break
                    regs[r] = regs[s] // regs[t]
                elif op == "MOD":
                    if regs[t] == 0:
                        res.error = f"Módulo por cero en paso {step} (pc={pc_now})"
                        break
                    regs[r] = regs[s] % regs[t]
                elif op == "IN":
                    if input_idx < len(in_vals):
                        regs[r] = int(in_vals[input_idx])
                        res.inputs_used.append(str(in_vals[input_idx]))
                        input_idx += 1
                    else:
                        regs[r] = 0
                        res.inputs_used.append("0 (sin entrada)")
                    res.output.append(f"[Entrada] → {regs[r]}")
                elif op == "OUT":
                    val = regs[r]
                    res.output.append(str(val))
                elif op in ("OUTNL", "NOP"):
                    pass   # no-op o newline
                else:
                    # Instrucción RO desconocida — ignorar
                    pass

            elif kind == "RM":
                _, _, r, d, s = inst
                addr = regs[s] + d

                if op == "LD":
                    if 0 <= addr < MEMSIZE:
                        regs[r] = mem[addr]
                    else:
                        res.error = f"LD fuera de memoria: addr={addr} en paso {step}"
                        break
                elif op == "LDA":
                    regs[r] = regs[s] + d    # r = s + d (no hay acceso a memoria)
                elif op == "LDC":
                    regs[r] = d              # r = d (constante)
                elif op == "ST":
                    if 0 <= addr < MEMSIZE:
                        mem[addr] = regs[r]
                    else:
                        res.error = f"ST fuera de memoria: addr={addr} en paso {step}"
                        break
                elif op in ("JLT", "JLE", "JGT", "JGE", "JEQ", "JNE"):
                    taken = False
                    v = regs[r]
                    if   op == "JLT" and v <  0: taken = True
                    elif op == "JLE" and v <= 0: taken = True
                    elif op == "JGT" and v >  0: taken = True
                    elif op == "JGE" and v >= 0: taken = True
                    elif op == "JEQ" and v == 0: taken = True
                    elif op == "JNE" and v != 0: taken = True
                    if taken:
                        regs[PC] = regs[s] + d
                else:
                    pass  # instrucción RM desconocida — ignorar

            res.steps = step + 1

        else:
            res.error = f"Límite de {MAX_STEPS} pasos alcanzado (posible bucle infinito)."

        return res
