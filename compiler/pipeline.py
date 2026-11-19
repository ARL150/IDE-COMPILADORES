# compiler/pipeline.py — Compilación completa de un fuente a .ci / .tm
"""
Une las fases del compilador sin interfaz gráfica:

    léxico → sintáctico → semántico → código intermedio (.ci)
                                    → código TM (.tm)  → simulador TM

El .ci y el .tm salen por caminos paralelos del MISMO árbol anotado; el
simulador sólo recibe el texto .tm (nunca el fuente ni el .ci).
Lo usan los scripts de prueba (tests/run_ejercicios.py).
"""
from __future__ import annotations
import contextlib
import io
from dataclasses import dataclass, field

from compiler.codegen import CodeGenerator
from compiler.intermediate import IntermediateGenerator
from compiler.lexer import tokenize
from compiler.parser import Parser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.tm_simulator import SimResult, TMSimulator


@dataclass
class Compilation:
    lex_errors: list = field(default_factory=list)
    syntax_errors: list = field(default_factory=list)
    semantic_errors: list = field(default_factory=list)
    annotated: object = None
    ci_lines: list = field(default_factory=list)
    tm_lines: list = field(default_factory=list)
    extensions_used: list = field(default_factory=list)   # instrucciones no estándar del .tm

    @property
    def ok(self) -> bool:
        return not (self.lex_errors or self.syntax_errors or self.semantic_errors)

    @property
    def tm_text(self) -> str:
        return "\n".join(self.tm_lines)

    @property
    def ci_text(self) -> str:
        return "\n".join(self.ci_lines)

    def errors(self) -> list[str]:
        return ([f"léxico: {e}" for e in self.lex_errors]
                + [f"sintáctico: {e}" for e in self.syntax_errors]
                + [f"semántico: {e}" for e in self.semantic_errors])


def compile_source(code: str, standard: bool | None = None) -> Compilation:
    """Compila el fuente. Si hay errores igualmente genera código del árbol parcial.

    standard=None → TM estándar salvo que el programa use reales/cadenas;
    standard=False → fuerza el modo extendido (MOD / OUTNL)."""
    out = Compilation()
    tokens, out.lex_errors = tokenize(code)
    parser = Parser(tokens)
    with contextlib.redirect_stdout(io.StringIO()):    # el parser imprime sus errores
        ast = parser.parse()
    out.syntax_errors = list(parser.errors)

    analyzer = SemanticAnalyzer()
    out.annotated = analyzer.analyze(ast)
    out.semantic_errors = list(analyzer.errors)

    out.ci_lines = IntermediateGenerator().generate(out.annotated)
    cg = CodeGenerator(analyzer.symbol_table, standard)
    out.tm_lines = cg.generate(out.annotated)
    out.extensions_used = cg.extensions_used
    return out


def run_tm(tm_text: str, inputs: list | None = None) -> SimResult:
    """Ejecuta el texto .tm en el simulador."""
    return TMSimulator().run(tm_text, input_values=inputs or [])
