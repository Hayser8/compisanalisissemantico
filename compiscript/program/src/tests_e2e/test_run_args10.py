from src.ir.model import Program, Function, Label, LabelInstr, BinOp, Return, Call, Temp, Name, Const
from src.backend.mips.emitter import emit_full_program
from src.tests_e2e._util_mars import pools_and_gtab, run_in_mars, last_int, _plan_for

def test_e2e_args10_sum():
    prog = Program()

    # sum10(a..j) = a+b+...+j
    sum10 = Function("sum10", ["a","b","c","d","e","f","g","h","i","j"])
    sb = sum10.new_block(Label("S0"))
    t = [Temp(f"t{i}") for i in range(10)]
    sb.add(LabelInstr(Label("S0")))
    sb.add(BinOp(dst=t[0], op="+", left=Name("a"), right=Name("b")))
    sb.add(BinOp(dst=t[1], op="+", left=t[0], right=Name("c")))
    sb.add(BinOp(dst=t[2], op="+", left=t[1], right=Name("d")))
    sb.add(BinOp(dst=t[3], op="+", left=t[2], right=Name("e")))
    sb.add(BinOp(dst=t[4], op="+", left=t[3], right=Name("f")))
    sb.add(BinOp(dst=t[5], op="+", left=t[4], right=Name("g")))
    sb.add(BinOp(dst=t[6], op="+", left=t[5], right=Name("h")))
    sb.add(BinOp(dst=t[7], op="+", left=t[6], right=Name("i")))
    sb.add(BinOp(dst=t[8], op="+", left=t[7], right=Name("j")))
    sb.add(Return(t[8]))
    prog.functions.append(sum10)

    # main: print(sum10(1..10)) -> 55
    main = Function("main", [])
    mb = main.new_block(Label("M0"))
    tr = Temp("tr")
    mb.add(LabelInstr(Label("M0")))
    mb.add(Call(dst=tr, func="sum10", args=[Const(i) for i in range(1, 11)]))
    mb.add(Call(dst=None, func="__print_int", args=[tr]))
    mb.add(Return(Const(0)))
    prog.functions.append(main)

    pool, gtab = pools_and_gtab()
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_plan_for, layouts=None)
    out = run_in_mars(asm)
    assert last_int(out) == 55
