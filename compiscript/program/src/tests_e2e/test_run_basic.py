import re, pytest
from src.ir.model import Program, Function, Temp, Name, Const
from src.ir.model import Label, Assign, Return, Call  # según tu IR
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.runner import have_any_sim, run_asm
from src.backend.mips.objects import LayoutRegistry
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.string_pool import StringPool  # o el que uses
from src.backend.mips.globals_table import GlobalsTable  # o el que uses

def _plan(params=None, locals=None, need_param_homes=0):
    params = params or []
    locals = locals or []
    return FramePlan(func_name="main", param_names=params,
                     local_names=locals, need_param_homes=need_param_homes).build()

@pytest.mark.skipif(not have_any_sim(), reason="No MIPS simulator (set MARS_JAR or install spim)")
def test_run_print_and_exit():
    # main: print 7; exit
    prog = Program()
    main = Function("main", [])
    bb = main.blocks[0]
    # Intrínseco __print_int(7)
    bb.add(Call(dst=None, func="__print_int", args=[Const(7)]))
    # newline para que SPIM/MARS dejen claro el output
    bb.add(Call(dst=None, func="__print_int", args=[Const(10)]))  # imprime '\n' como 10 (LF)
    bb.add(Call(dst=None, func="__exit", args=[]))
    prog.functions.append(main)

    asm = emit_full_program(
        prog, pool=StringPool(), gtab=GlobalsTable(),
        plan_for_fn=lambda fn: _plan(), layouts=None
    )

    rc, out, err = run_asm(asm)
    # Normalizamos: en SPIM hay banners; buscamos el '7' aislado en línea
    assert rc == 0
    assert re.search(r"(?m)^\s*7\s*$", out.replace("\r", "")) is not None

@pytest.mark.skipif(not have_any_sim(), reason="No MIPS simulator")
def test_run_nested_calls_sum():
    # f(): return 40 + 2
    f = Function("f", [])
    bbf = f.blocks[0]
    t0 = Temp("t0")
    from src.ir.model import BinOp
    bbf.add(BinOp(dst=t0, op="+", left=Const(40), right=Const(2)))
    bbf.add(Return(t0))

    # g(x): return x + 5
    g = Function("g", ["x"])
    bbg = g.blocks[0]
    t1 = Temp("t1")
    bbg.add(BinOp(dst=t1, op="+", left=Name("x"), right=Const(5)))
    bbg.add(Return(t1))

    # main:
    #   tA = call f()
    #   tB = call g(tA)
    #   print tB (=47); exit
    main = Function("main", [])
    bbm = main.blocks[0]
    tA, tB = Temp("tA"), Temp("tB")
    bbm.add(Call(dst=tA, func="f", args=[]))
    bbm.add(Call(dst=tB, func="g", args=[tA]))
    bbm.add(Call(dst=None, func="__print_int", args=[tB]))
    bbm.add(Call(dst=None, func="__print_int", args=[Const(10)]))
    bbm.add(Call(dst=None, func="__exit", args=[]))

    prog = Program()
    prog.functions.extend([f, g, main])

    def plan_for_fn(fn):
        if fn.name == "g":
            return FramePlan(func_name="g", param_names=["x"], local_names=[], need_param_homes=1).build()
        return FramePlan(func_name=fn.name, param_names=[], local_names=[], need_param_homes=0).build()

    asm = emit_full_program(prog, pool=StringPool(), gtab=GlobalsTable(), plan_for_fn=plan_for_fn, layouts=None)
    rc, out, err = run_asm(asm)
    assert rc == 0
    assert "47" in out
