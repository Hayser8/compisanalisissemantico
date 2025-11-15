from src.ir.model import Program, Function, Label, LabelInstr, BinOp, Return, Call, Const, Temp, Name
from src.backend.mips.emitter import emit_full_program
from src.tests_e2e._util_mars import pools_and_gtab, run_in_mars, last_int, _plan_for

def test_e2e_call_chain_three_funcs():
    prog = Program()

    # h(x) = x * 2
    h = Function("h", ["x"])
    hb = h.new_block(Label("H0"))
    ht = Temp("ht")
    hb.add(LabelInstr(Label("H0")))
    hb.add(BinOp(dst=ht, op="*", left=Name("x"), right=Const(2)))
    hb.add(Return(ht))
    prog.functions.append(h)

    # g(x) = h(x) + 3
    g = Function("g", ["x"])
    gb = g.new_block(Label("G0"))
    gt1 = Temp("gt1"); gt2 = Temp("gt2")
    gb.add(LabelInstr(Label("G0")))
    gb.add(Call(dst=gt1, func="h", args=[Name("x")]))
    gb.add(BinOp(dst=gt2, op="+", left=gt1, right=Const(3)))
    gb.add(Return(gt2))
    prog.functions.append(g)

    # f(x) = g(x) + 4
    f = Function("f", ["x"])
    fb = f.new_block(Label("F0"))
    ft1 = Temp("ft1"); ft2 = Temp("ft2")
    fb.add(LabelInstr(Label("F0")))
    fb.add(Call(dst=ft1, func="g", args=[Name("x")]))
    fb.add(BinOp(dst=ft2, op="+", left=ft1, right=Const(4)))
    fb.add(Return(ft2))
    prog.functions.append(f)

    # main: print(f(5)) -> 17
    main = Function("main", [])
    mb = main.new_block(Label("M0"))
    tr = Temp("tr")
    mb.add(LabelInstr(Label("M0")))
    mb.add(Call(dst=tr, func="f", args=[Const(5)]))
    mb.add(Call(dst=None, func="__print_int", args=[tr]))
    mb.add(Return(Const(0)))
    prog.functions.append(main)

    pool, gtab = pools_and_gtab()
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_plan_for, layouts=None)
    out = run_in_mars(asm)
    assert last_int(out) == 17
