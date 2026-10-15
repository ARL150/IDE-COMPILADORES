# compiler/semantic.py — Fase 3: Análisis Semántico (fachada)
"""
Fachada de compatibilidad. La lógica vive en módulos separados:

  semantic_errors.py    categorías y SemanticError
  symbol_table.py       SymbolEntry, Scope, SymbolTable (ámbitos)
  type_checker.py       reglas de tipos, conversiones y plegado de constantes
  annotated_ast.py      AnnotatedNode y copia del AST
  semantic_analyzer.py  SemanticAnalyzer (recorrido)
  semantic_report.py    árbol anotado / tabla de símbolos / reporte en texto
"""
from compiler.semantic_errors import SemanticError                       # noqa: F401
from compiler.symbol_table import SymbolEntry, SymbolTable, Scope        # noqa: F401
from compiler.annotated_ast import AnnotatedNode, copy_ast               # noqa: F401
from compiler.semantic_analyzer import SemanticAnalyzer                  # noqa: F401
