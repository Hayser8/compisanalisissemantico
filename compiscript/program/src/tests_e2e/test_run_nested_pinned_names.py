from src.ir.model import Program, Function, Label, LabelInstr, BinOp, Return, Call, Assign, Name, Temp, Const
from src.backend.mips.emitter import emit_full_program
from src.tests_e2e._util_mars import pools_and_gtab, run_in_mars, last_int, _plan_for

def test_e2e_pinned_names_survive_nested_calls():
    prog = Program()

    # bump(x) = x + 1
    bump = Function("bump", ["x"])
    bb = bump.new_block(Label("B0"))
    t0 = Temp("t0")
    bb.add(LabelInstr(Label("B0")))
    bb.add(BinOp(dst=t0, op="+", left=Name("x"), right=Const(1)))
    bb.add(Return(t0))
    prog.functions.append(bump)

    # twice(y) = bump(bump(y))
    twice = Function("twice", ["y"])
    tb = twice.new_block(Label("T0"))
    t1 = Temp("t1"); t2 = Temp("t2")
    tb.add(LabelInstr(Label("T0")))
    tb.add(Call(dst=t1, func="bump", args=[Name("y")]))
    tb.add(Call(dst=t2, func="bump", args=[t1]))
    tb.add(Return(t2))
    prog.functions.append(twice)

    # main: a=7; keep=a; r=twice(keep); print(a) -> 7 (verifica preservación de $s*)
    main = Function("main", [])
    mb = main.new_block(Label("M0"))
    r = Temp("r")
    mb.add(LabelInstr(Label("M0")))
    mb.add(Assign(dst=Name("a"), src=Const(7)))
    mb.add(Assign(dst=Name("keep"), src=Name("a")))  # fuerza pin de 'keep' a $s*
    mb.add(Call(dst=r, func="twice", args=[Name("keep")]))
    mb.add(Call(dst=None, func="__print_int", args=[Name("a")]))
    mb.add(Return(Const(0)))
    prog.functions.append(main)

    pool, gtab = pools_and_gtab()
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_plan_for, layouts=None)
    out = run_in_mars(asm)
    assert last_int(out) == 7
