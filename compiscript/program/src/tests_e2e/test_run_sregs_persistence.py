# -*- coding: utf-8 -*-
from __future__ import annotations
from src.ir.model import Program, Function, Label, LabelInstr, Assign, BinOp, Return, Temp, Name, Const, Call
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.frame_plan import FramePlan
from src.tests_e2e._util_mars import run_in_mars, last_int, pools_and_gtab

def _plan_for(fn: Function) -> FramePlan:
    if fn.name == "add":
        return FramePlan(func_name="add", param_names=["x","y"], local_names=[], need_param_homes=2).build()
    return FramePlan(func_name="main", param_names=[], local_names=["x"], need_param_homes=0).build()

def test_e2e_callee_saved_sregs_persistence():
    prog = Program()

    # add(x,y) = x+y
    add = Function("add", ["x","y"])
    ab = add.new_block(Label("A0"))
    t0 = Temp("t0")
    ab.add(LabelInstr(Label("A0")))
    ab.add(BinOp(dst=t0, op="+", left=Name("x"), right=Name("y")))
    ab.add(Return(t0))
    prog.functions.append(add)

    # main: x=7; t=add(x,5); print(x+1) -> 8 si $s* se preservó
    main = Function("main", [])
    mb = main.new_block(Label("M0"))
    tx = Temp("tx"); tprint = Temp("tprint")
    mb.add(LabelInstr(Label("M0")))
    mb.add(Assign(dst=Name("x"), src=Const(7)))
    mb.add(Call(dst=tx, func="add", args=[Name("x"), Const(5)]))
    mb.add(BinOp(dst=tprint, op="+", left=Name("x"), right=Const(1)))
    mb.add(Call(dst=None, func="__print_int", args=[tprint]))
    mb.add(Return(Const(0)))
    prog.functions.append(main)

    pool, gtab = pools_and_gtab()
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_plan_for, layouts=None)
    out = run_in_mars(asm)
    assert last_int(out) == 8
