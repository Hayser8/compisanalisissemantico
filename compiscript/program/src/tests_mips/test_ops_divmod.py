import re
from src.ir.model import Function, BasicBlock, Label, Temp, Name, Const, BinOp, Return
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.emitter import emit_function

def _mk_bb(lbl="L0"):
    return BasicBlock(label=Label(lbl))

def _plan(name="f", params=None, locals_=None, need_param_homes=0):
    params = params or []
    locals_ = locals_ or []
    return FramePlan(
        func_name=name, 
        param_names=params, 
        local_names=locals_,
        need_param_homes=need_param_homes
    ).build()

def test_div_and_mod_basic_patterns():
    fn = Function("divmod1", [])
    bb = _mk_bb()

    t_div = Temp("t_div")
    t_mod = Temp("t_mod")

    # t_div = 7 / 3
    bb.add(BinOp(dst=t_div, op="/", left=Const(7), right=Const(3)))
    # t_mod = 7 % 3
    bb.add(BinOp(dst=t_mod, op="%", left=Const(7), right=Const(3)))
    bb.add(Return())

    fn.blocks.append(bb)
    asm = emit_function(fn, plan=_plan("divmod1"))

    # Debe usar 'div' para ambas y mflo/mfhi para recoger cociente y resto
    assert re.search(r"\bdiv\s+\$t\d,\s*\$t\d", asm)
    assert re.search(r"\bmflo\s+\$t\d\b", asm)
    assert re.search(r"\bmfhi\s+\$t\d\b", asm)

def test_div_and_mod_with_names_and_negatives():
    fn = Function("divmod2", [])
    bb = _mk_bb()

    a = Name("a"); b = Name("b")
    tq = Temp("tq"); tr = Temp("tr")

    # locals a,b (para forzar loads desde home y uso normal de RA)
    # tq = a / (-b)
    bb.add(BinOp(dst=tq, op="/", left=a, right=BinOp(dst=Temp("tbneg"), op="-", left=Const(0), right=b)))
    # tr = (-a) % b
    bb.add(BinOp(dst=tr, op="%", left=BinOp(dst=Temp("taneg"), op="-", left=Const(0), right=a), right=b))
    bb.add(Return())

    fn.blocks.append(bb)
    plan = _plan("divmod2", params=[], locals_=["a","b"], need_param_homes=0)
    asm = emit_function(fn, plan=plan)

    # Debe haber algún 'div' y sus mflo/mfhi correspondientes
    assert re.search(r"\bdiv\s+\$t\d,\s*\$t\d", asm)
    assert re.search(r"\bmflo\s+\$t\d\b", asm)
    assert re.search(r"\bmfhi\s+\$t\d\b", asm)
