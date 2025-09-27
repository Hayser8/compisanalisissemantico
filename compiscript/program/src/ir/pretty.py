from __future__ import annotations
from typing import List
from .model import (
    Program, Function, BasicBlock, Instr,
    LabelInstr, Assign, UnaryOp, BinOp, IfGoto, Goto, Call, Return,
    Load, Store, GetProp, SetProp, NewObject,
    Operand, Temp, Name, Const, Label
)

def _p_oprnd(o: Operand) -> str:
    if isinstance(o, Temp):
        return o.name
    if isinstance(o, Name):
        return o.name
    if isinstance(o, Const):
        v = o.value
        if isinstance(v, str):
            return f"\"{v}\""
        if v is True:
            return "true"
        if v is False:
            return "false"
        if v is None:
            return "null"
        return str(v)
    if isinstance(o, Label):
        return o.name
    return str(o)

def _p_instr(i: Instr) -> List[str]:
    if isinstance(i, LabelInstr):
        return [f"{i.label.name}:"]
    if isinstance(i, Assign):
        return [f"{_p_oprnd(i.dst)} = {_p_oprnd(i.src)}"]
    if isinstance(i, UnaryOp):
        return [f"{_p_oprnd(i.dst)} = {i.op} {_p_oprnd(i.value)}"]
    if isinstance(i, BinOp):
        return [f"{_p_oprnd(i.dst)} = {_p_oprnd(i.left)} {i.op} {_p_oprnd(i.right)}"]
    if isinstance(i, IfGoto):
        return [f"if {_p_oprnd(i.cond)} goto {i.target.name}"]
    if isinstance(i, Goto):
        return [f"goto {i.target.name}"]
    if isinstance(i, Call):
        args = ", ".join(_p_oprnd(a) for a in i.args)
        if i.dst is None:
            return [f"call {i.func}, {args}"] if args else [f"call {i.func}"]
        return [f"{_p_oprnd(i.dst)} = call {i.func}, {args}"] if args else [f"{_p_oprnd(i.dst)} = call {i.func}"]
    if isinstance(i, Return):
        return ["return"] if i.value is None else [f"return {_p_oprnd(i.value)}"]
    if isinstance(i, Load):
        return [f"{_p_oprnd(i.dst)} = load {_p_oprnd(i.array)}[{_p_oprnd(i.index)}]"]
    if isinstance(i, Store):
        return [f"store {_p_oprnd(i.array)}[{_p_oprnd(i.index)}], {_p_oprnd(i.value)}"]
    if isinstance(i, GetProp):
        return [f"{_p_oprnd(i.dst)} = get {_p_oprnd(i.obj)}.{i.prop}"]
    if isinstance(i, SetProp):
        return [f"set {_p_oprnd(i.obj)}.{i.prop}, {_p_oprnd(i.value)}"]
    if isinstance(i, NewObject):
        args = ", ".join(_p_oprnd(a) for a in i.args)
        return [f"{_p_oprnd(i.dst)} = new {i.class_name}({args})"]
    return [f"; <unknown instr {i!r}>"]

def function_to_str(fn: Function) -> str:
    out: List[str] = []
    params = ", ".join(fn.params)
    out.append(f"function {fn.name}({params}):")
    for bb in fn.blocks:
        # asegurar que el label se emita (si no hay LabelInstr, lo agregamos virtual)
        has_label = any(isinstance(x, LabelInstr) for x in bb.instrs)
        if not has_label:
            out.append(f"{bb.label.name}:")
        for instr in bb.instrs:
            lines = _p_instr(instr)
            for ln in lines:
                if ln.endswith(":"):
                    out.append(ln)
                else:
                    out.append(f"  {ln}")
    return "\n".join(out)

def program_to_str(prog: Program) -> str:
    return "\n\n".join(function_to_str(fn) for fn in prog.functions)
