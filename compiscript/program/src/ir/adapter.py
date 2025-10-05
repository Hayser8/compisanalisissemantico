# program/src/ir/adapter.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Any, Optional, Dict

from .model import Program
from .context import IRGenContext
from .temps import TempAllocator, LabelAllocator
from .gen_stmt import gen_stmt
from src.runtime.frame import FrameLayout  # <-- NUEVO

# Tipos de las “tuplas” que ya usan gen_expr/gen_stmt
Expr = Tuple[Any, ...]
Stmt = Tuple[Any, ...]


@dataclass
class IRAdapter:
    """
    Adaptador fino: tu visitor semántico/AST traduce nodos a tuplas
    y llama a este adaptador para emitir IR.
    Además, aquí gestionamos un FrameLayout por función (opcional).
    """
    program: Program
    ctx: IRGenContext
    frames: Dict[str, FrameLayout] = field(default_factory=dict)   # <-- NUEVO

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
        locals: Optional[List[str]] = None,   # <-- NUEVO: lista de locales (opc.)
    ) -> None:
        """
        Crea una función y emite el cuerpo ya en forma de tuplas Stmt.

        body puede ser:
          - Un único ('block', [...])
          - O directamente esa lista de statements: ('block', [ ... ]) equivalente

        'locals' (opcional) permite adjuntar un FrameLayout con offsets.
        """
        # 1) Prepara el frame (si provees locals)
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

        # 2) Emitir IR
        self.ctx.begin_function(name, params)
        if body and isinstance(body, tuple) and body[0] == 'block':
            gen_stmt(body, self.ctx)
        else:
            gen_stmt(('block', body if isinstance(body, list) else [body]), self.ctx)
        self.ctx.end_function()
        # (Opcional) podrías usar self.frames[name].frame_size_bytes() para prolog/epilog en ASM.
        

def lower_program(functions: List[Tuple[str, List[str], Stmt]]) -> Program:
    """
    Helper para tests: recibe una lista de (name, params, body_stmt_en_tuplas)
    y devuelve el Program con el IR completito.
    """
    adapter = IRAdapter.new()
    for name, params, body in functions:
        adapter.emit_function(name, params, body)
    return adapter.program
