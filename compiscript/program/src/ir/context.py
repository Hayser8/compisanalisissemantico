# program/src/ir/context.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from .model import Program, Function, BasicBlock, Label, Instr, LabelInstr
from .temps import TempAllocator, LabelAllocator


@dataclass
class IRGenContext:
    program: Program
    temp_alloc: TempAllocator
    label_alloc: LabelAllocator

    current_function: Optional[Function] = None
    current_block: Optional[BasicBlock] = None

    # Pila de bucles para break/continue: (label_break, label_continue)
    _loop_stack: List[Tuple[Label, Label]] = field(default_factory=list)

    # ---- helpers de creación ----
    def begin_function(self, name: str, params: Optional[List[str]] = None) -> Function:
        fn = Function(name=name, params=list(params or []))
        self.program.add_function(fn)
        self.current_function = fn
        # crear primer bloque por defecto (con label emitido explícitamente)
        self.new_block(self.label_alloc.new_label())
        return fn

    def end_function(self) -> None:
        self.current_function = None
        self.current_block = None
        self._loop_stack.clear()

    def new_block(self, label: Optional[Label] = None) -> BasicBlock:
        if self.current_function is None:
            raise RuntimeError("No hay función activa para crear bloque")
        lab = label or self.label_alloc.new_label()
        bb = self.current_function.new_block(lab)
        # Cada bloque empieza con su LabelInstr
        bb.add(LabelInstr(lab))
        self.current_block = bb
        return bb

    def emit(self, instr: Instr) -> None:
        if self.current_block is None:
            raise RuntimeError("No hay bloque activo para emitir instrucciones")
        self.current_block.add(instr)

    # ---- bucles: break/continue ----
    def push_loop(self, label_break: Label, label_continue: Label) -> None:
        self._loop_stack.append((label_break, label_continue))

    def pop_loop(self) -> None:
        if self._loop_stack:
            self._loop_stack.pop()

    def current_break_label(self) -> Label:
        if not self._loop_stack:
            raise RuntimeError("`break` fuera de un bucle")
        return self._loop_stack[-1][0]

    def current_continue_label(self) -> Label:
        if not self._loop_stack:
            raise RuntimeError("`continue` fuera de un bucle")
        return self._loop_stack[-1][1]
