# ruta: program/src/ir/adapter.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Any, Optional, Dict

from .model import Program
from .context import IRGenContext
from .temps import TempAllocator, LabelAllocator
from .gen_stmt import gen_stmt
from src.runtime.frame import FrameLayout

# tipos de tuplas que usan gen_expr/gen_stmt
Expr = Tuple[Any, ...]
Stmt = Tuple[Any, ...]


@dataclass
class IRAdapter:
    """
    adaptador: el visitor del ast arma tuplas y aquí las volvemos ir.
    también guardamos un frame por función.
    """
    program: Program
    ctx: IRGenContext
    frames: Dict[str, FrameLayout] = field(default_factory=dict)

    @classmethod
    def new(cls) -> IRAdapter:
        prog = Program()
        ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
        return cls(program=prog, ctx=ctx)

    def emit_function(
        self,
        name: str,
        params: List[str],
        body: Stmt | Tuple[str, List[Stmt]],
        *,
        locals: Optional[List[str]] = None,   # lista de locales opcional
    ) -> None:
        """
        crea la función y emite el cuerpo en tuplas.

        body puede ser:
          - ('block', [...])
          - o una lista de statements

        'locals' permite adjuntar un frame con offsets.
        """
        # arma el frame si mandas locals
        if locals is None:
            locals = []

        if name not in self.frames:
            fl = FrameLayout(name=name)
            for p in params:
                fl.add_param(p)
            for v in locals:
                fl.add_local(v)
            fl.seal()
            self.frames[name] = fl

        # emite el ir
        self.ctx.begin_function(name, params)
        if body and isinstance(body, tuple) and body[0] == 'block':
            gen_stmt(body, self.ctx)
        else:
            gen_stmt(('block', body if isinstance(body, list) else [body]), self.ctx)
        self.ctx.end_function()


def lower_program(functions: List[Tuple[str, List[str], Stmt]]) -> Program:
    """
    helper para tests: recibe (name, params, body) y devuelve el program con el ir.
    """
    adapter = IRAdapter.new()
    for name, params, body in functions:
        adapter.emit_function(name, params, body)
    return adapter.program
