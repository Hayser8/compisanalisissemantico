from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Union

# ---------- Operandos ----------

@dataclass(frozen=True)
class Operand:
    pass

@dataclass(frozen=True)
class Temp(Operand):
    name: str                  # p.ej. "t0"
    type_hint: Optional[str] = None

@dataclass(frozen=True)
class Name(Operand):
    name: str                  # nombre estable (var/param/global/campo)
    type_hint: Optional[str] = None

@dataclass(frozen=True)
class Const(Operand):
    value: Union[int, float, str, bool, None]
    type_hint: Optional[str] = None

@dataclass(frozen=True)
class Label(Operand):
    name: str                  # p.ej. "L0"

# ---------- Instrucciones ----------

@dataclass
class Instr:
    pass

@dataclass
class LabelInstr(Instr):
    label: Label               # Impresa como 'Lk:'

@dataclass
class Assign(Instr):
    dst: Operand               # Temp|Name
    src: Operand               # Temp|Name|Const

@dataclass
class UnaryOp(Instr):
    dst: Operand
    op: str                    # '-', '!'
    value: Operand

@dataclass
class BinOp(Instr):
    dst: Operand
    op: str                    # '+', '-', '*', '/', '%', '==', '!=', '<', '<=', '>', '>=', '&&', '||'
    left: Operand
    right: Operand

@dataclass
class IfGoto(Instr):
    cond: Operand              # boolean temp/name
    target: Label

@dataclass
class Goto(Instr):
    target: Label

@dataclass
class Call(Instr):
    dst: Optional[Operand]     # None si call es 'void'
    func: str                  # nombre o callee resuelto
    args: List[Operand] = field(default_factory=list)

@dataclass
class Return(Instr):
    value: Optional[Operand] = None

# Arrays
@dataclass
class Load(Instr):
    dst: Operand
    array: Operand             # ref a arreglo
    index: Operand             # índice integer

@dataclass
class Store(Instr):
    array: Operand
    index: Operand
    value: Operand

# Objetos / campos
@dataclass
class GetProp(Instr):
    dst: Operand
    obj: Operand
    prop: str

@dataclass
class SetProp(Instr):
    obj: Operand
    prop: str
    value: Operand

@dataclass
class NewObject(Instr):
    dst: Operand
    class_name: str
    args: List[Operand] = field(default_factory=list)

# ---------- Bloques / Funciones / Programa ----------

@dataclass
class BasicBlock:
    label: Label
    instrs: List[Instr] = field(default_factory=list)

    def add(self, instr: Instr) -> None:
        self.instrs.append(instr)

@dataclass
class Function:
    name: str
    params: List[str] = field(default_factory=list)
    blocks: List[BasicBlock] = field(default_factory=list)

    # metadata opcional para backend
    frame_size: int = 0

    def new_block(self, label: Label) -> BasicBlock:
        bb = BasicBlock(label=label)
        self.blocks.append(bb)
        return bb

    def entry_block(self) -> BasicBlock:
        if not self.blocks:
            self.new_block(Label("L0"))
        return self.blocks[0]

@dataclass
class Program:
    functions: List[Function] = field(default_factory=list)

    def add_function(self, fn: Function) -> None:
        self.functions.append(fn)
