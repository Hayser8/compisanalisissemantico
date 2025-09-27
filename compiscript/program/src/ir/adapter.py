from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Any, Optional

from .model import Program
from .context import IRGenContext
from .temps import TempAllocator, LabelAllocator
from .gen_stmt import gen_stmt

# Tipos de las “tuplas” que ya usan gen_expr/gen_stmt
Expr = Tuple[Any, ...]
Stmt = Tuple[Any, ...]


@dataclass
class IRAdapter:
    """
    Adaptador muy fino: tu visitor semántico/AST traduce nodos reales a estas tuplas
    (Expr/Stmt) y llama a este adaptador para emitir el IR.

    — No conoce nada de ANTLR: sólo recibe las tuplas ya normalizadas.
    — Cuando integres, en tu visitor real (post type-check), por cada constructo:
        * Expresión → construyes ('const'...), ('name'...), ('bin',...), etc.
        * Sentencia  → ('if', ...), ('while', ...), ('switch', ...), etc.
      y llamas a emit_function(...) con las sentencias del cuerpo.
    """
    program: Program
    ctx: IRGenContext

    @classmethod
    def new(cls) -> IRAdapter:
        prog = Program()
        ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
        return cls(program=prog, ctx=ctx)

    def emit_function(self, name: str, params: List[str], body: Stmt | Tuple[str, List[Stmt]]) -> None:
        """
        Crea una función y emite el cuerpo ya en forma de tuplas Stmt.

        body puede ser:
          - Un único ('block', [...])
          - O directamente esa lista de statements: ('block', [ ... ]) equivalente
        """
        self.ctx.begin_function(name, params)
        if body and isinstance(body, tuple) and body[0] == 'block':
            gen_stmt(body, self.ctx)
        else:
            gen_stmt(('block', body if isinstance(body, list) else [body]), self.ctx)
        # No hacemos end_function para preservar el último bloque abierto si el caller
        # quiere seguir emitiendo; cerramos aquí por simplicidad.
        self.ctx.end_function()


def lower_program(functions: List[Tuple[str, List[str], Stmt]]) -> Program:
    """
    Helper para tests: recibe una lista de (name, params, body_stmt_en_tuplas)
    y devuelve el Program con el IR completito.
    """
    adapter = IRAdapter.new()
    for name, params, body in functions:
        adapter.emit_function(name, params, body)
    return adapter.program
