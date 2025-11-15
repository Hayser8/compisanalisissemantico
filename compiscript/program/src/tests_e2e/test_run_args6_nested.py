# -*- coding: utf-8 -*-
from __future__ import annotations
from src.ir.model import Program, Function, Label, LabelInstr, Assign, BinOp, Return, Temp, Name, Const, Call
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.frame_plan import FramePlan
from src.tests_e2e._util_mars import run_in_mars, last_int, pools_and_gtab

def _plan_for(fn: Function) -> FramePlan:
    if fn.name == "sum6":
        return FramePlan(func_name="sum6", param_names=["a","b","c","d","e","f"], local_names=[], need_param_homes=6).build()
    return FramePlan(func_name="main", param_names=[], local_names=["keep"], need_param_homes=0).build()

def test_e2e_args6_and_nested_calls():
    prog = Program()

    # sum6(a,b,c,d,e,f) = a+b+c+d+e+f
    sum6 = Function("sum6", ["a","b","c","d","e","f"])
    sb = sum6.new_block(Label("S0"))
    t0=Temp("t0"); t1=Temp("t1"); t2=Temp("t2"); t3=Temp("t3"); t4=Temp("t4")
    sb.add(LabelInstr(Label("S0")))
    sb.add(BinOp(dst=t0, op="+", left=Name("a"), right=Name("b")))
    sb.add(BinOp(dst=t1, op="+", left=t0, right=Name("c")))
    sb.add(BinOp(dst=t2, op="+", left=t1, right=Name("d")))
    sb.add(BinOp(dst=t3, op="+", left=t2, right=Name("e")))
    sb.add(BinOp(dst=t4, op="+", left=t3, right=Name("f")))
    sb.add(Return(t4))
    prog.functions.append(sum6)

    # main: t = sum6(1..6)=21; r = sum6(t,1,1,1,1,1)=26; print(r)
    main = Function("main", [])
    mb = main.new_block(Label("M0"))
    tA=Temp("tA"); tB=Temp("tB")
    mb.add(LabelInstr(Label("M0")))
    mb.add(Call(dst=tA, func="sum6", args=[Const(1),Const(2),Const(3),Const(4),Const(5),Const(6)]))
    mb.add(Assign(dst=Name("keep"), src=tA))  # fuerza callee-save en main
    mb.add(Call(dst=tB, func="sum6", args=[Name("keep"),Const(1),Const(1),Const(1),Const(1),Const(1)]))
    mb.add(Call(dst=None, func="__print_int", args=[tB]))
    mb.add(Return(Const(0)))
    prog.functions.append(main)

    pool, gtab = pools_and_gtab()
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_plan_for, layouts=None)
    out = run_in_mars(asm)
    assert last_int(out) == 26
