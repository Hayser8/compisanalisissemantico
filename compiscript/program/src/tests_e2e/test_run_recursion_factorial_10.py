from src.ir.model import Program, Function, Label, LabelInstr, BinOp, Return, Call, Const, Temp, Name, IfGoto
from src.backend.mips.emitter import emit_full_program
from src.tests_e2e._util_mars import pools_and_gtab, run_in_mars, last_int, _plan_for

def test_e2e_recursion_factorial_10():
    prog = Program()

    # fact(n): if (n <= 1) return 1; else return n * fact(n-1)
    fact = Function("fact", ["n"])
    b = fact.new_block(Label("L0"))
    Lbase = Label("Lbase")
    t0 = Temp("t0"); t1 = Temp("t1"); t2 = Temp("t2"); t3 = Temp("t3")
    b.add(LabelInstr(Label("L0")))
    b.add(BinOp(dst=t0, op="<=", left=Name("n"), right=Const(1)))
    b.add(IfGoto(cond=t0, target=Lbase))
    b.add(BinOp(dst=t1, op="-", left=Name("n"), right=Const(1)))
    b.add(Call(dst=t2, func="fact", args=[t1]))
    b.add(BinOp(dst=t3, op="*", left=Name("n"), right=t2))
    b.add(Return(t3))
    b.add(LabelInstr(Lbase))
    b.add(Return(Const(1)))
    prog.functions.append(fact)

    # main: print(fact(10)) -> 3628800
    main = Function("main", [])
    m = main.new_block(Label("M0"))
    t5 = Temp("t5")
    m.add(LabelInstr(Label("M0")))
    m.add(Call(dst=t5, func="fact", args=[Const(10)]))
    m.add(Call(dst=None, func="__print_int", args=[t5]))
    m.add(Return(Const(0)))
    prog.functions.append(main)

    pool, gtab = pools_and_gtab()
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_plan_for, layouts=None)
    out = run_in_mars(asm)
    assert last_int(out) == 3628800
