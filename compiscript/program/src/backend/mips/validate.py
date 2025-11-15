from __future__ import annotations
from typing import Iterable
from src.ir.model import *

ALLOWED = (LabelInstr, Assign, UnaryOp, BinOp, IfGoto, Goto, Call, Return, Load, Store, GetProp, SetProp, NewObject, MakeClosure, CallClosure)

def _is_int_const(op: Operand) -> bool:
    return isinstance(op, Const) and isinstance(op.value, int)

def validate_program(prog: Program, *, allow_objects=True) -> None:
    for fn in prog.functions:
        for bb in fn.blocks:
            for ins in bb.instrs:
                if not isinstance(ins, ALLOWED):
                    raise ValueError(f"Instrucción TAC no soportada: {ins!r}")

                if isinstance(ins, Assign):
                    if not isinstance(ins.dst, (Temp, Name)):
                        raise ValueError("Assign.dst debe ser Temp|Name")

                if isinstance(ins, Call):
                    if not isinstance(ins.func, str):
                        raise ValueError("Call.func debe ser string")
                    # si no soportas objetos aún:
                    # if ins.func.startswith("__mcall__"): raise ValueError("Métodos no soportados en MVP")

                if isinstance(ins, (Load, Store)):
                    if isinstance(ins, Load):
                        arr, idx = ins.array, ins.index
                    else:
                        arr, idx = ins.array, ins.index
                    if not isinstance(idx, (Temp, Name)) and not _is_int_const(idx):
                        raise ValueError("Index debe ser int/Temp/Name entero")
                
                if isinstance(ins, MakeClosure):
                    if not isinstance(ins.dst, (Temp, Name)):
                        raise ValueError("MakeClosure.dst debe ser Temp|Name")
                    if not isinstance(ins.code, (Label, str)):
                        raise ValueError("MakeClosure.code debe ser Label|str")

                if isinstance(ins, CallClosure):
                    if ins.dst is not None and not isinstance(ins.dst, (Temp, Name)):
                        raise ValueError("CallClosure.dst debe ser Temp|Name|None")

                if not allow_objects and isinstance(ins, (GetProp, SetProp, NewObject)):
                    raise ValueError("Objetos no soportados en esta fase")
