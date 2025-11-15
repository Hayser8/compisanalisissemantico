# -*- coding: utf-8 -*-
from __future__ import annotations
from src.ir.model import Program, Function, Label, LabelInstr, Assign, BinOp, Return, Temp, Name, Const, Call
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.frame_plan import FramePlan
from src.tests_e2e._util_mars import run_in_mars, last_int, pools_and_gtab

def _plan_for(fn: Function) -> FramePlan:
    return FramePlan(func_name="main", param_names=[], local_names=["a","b"], need_param_homes=0).build()

def test_e2e_io_and_shifts_arith():
    prog = Program()

    main = Function("main", [])
    mb = main.new_block(Label("M0"))
    tA=Temp("tA"); tB=Temp("tB"); tC=Temp("tC"); tD=Temp("tD")

    mb.add(LabelInstr(Label("M0")))
    # a = read(); b = read();
    mb.add(Call(dst=tA, func="__read_int", args=[]))
    mb.add(Assign(dst=Name("a"), src=tA))
    mb.add(Call(dst=tB, func="__read_int", args=[]))
    mb.add(Assign(dst=Name("b"), src=tB))
    # c = (a << 1) + (b >> 1)
    mb.add(BinOp(dst=tC, op="<<", left=Name("a"), right=Const(1)))
    mb.add(BinOp(dst=tD, op=">>", left=Name("b"), right=Const(1)))
    mb.add(BinOp(dst=tC, op="+", left=tC, right=tD))
    mb.add(Call(dst=None, func="__print_int", args=[tC]))
    mb.add(Return(Const(0)))
    prog.functions.append(main)

    pool, gtab = pools_and_gtab()
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_plan_for, layouts=None)

    # Entrada 8 y 5 -> (8<<1)=16, (5>>1)=2, total=18
    out = run_in_mars(asm, stdin="8\n5\n")
    assert last_int(out) == 18
