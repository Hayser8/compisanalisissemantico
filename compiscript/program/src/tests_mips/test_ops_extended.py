import re
from src.ir.model import Function, BasicBlock, Label, Temp, Const, UnaryOp, BinOp, Return
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.emitter import emit_function

def _mk_bb(name="L0"):
    return BasicBlock(Label(name))

def _plan(fn_name="t", params=None, locals_=None, need_param_homes=0):
    params = params or []
    locals_ = locals_ or []
    return FramePlan(func_name=fn_name, param_names=params, local_names=locals_, need_param_homes=need_param_homes).build()

def test_unary_ops_emit_correct_mips():
    fn = Function("uops", [])
    bb = _mk_bb("L0")
    # t1 = -5 ; t2 = ~1 ; t3 = !0
    t1, t2, t3 = Temp("t1"), Temp("t2"), Temp("t3")
    bb.add(UnaryOp(dst=t1, op="-", value=Const(5)))
    bb.add(UnaryOp(dst=t2, op="~", value=Const(1)))
    bb.add(UnaryOp(dst=t3, op="!", value=Const(0)))
    bb.add(Return())
    fn.blocks.append(bb)

    asm = emit_function(fn, plan=_plan("uops"))

    # -x => subu rd, $zero, rs
    assert re.search(r"\bsubu\s+\$t\d,\s*\$zero,\s*\$t\d", asm)
    # ~x => nor rd, rs, $zero
    assert re.search(r"\bnor\s+\$t\d,\s*\$t\d,\s*\$zero", asm)
    # !x => sltiu rd, rs, 1
    assert re.search(r"\bsltiu\s+\$t\d,\s*\$t\d,\s*1", asm)

def test_div_and_mod_emit_div_mflo_mfhi():
    fn = Function("idiv", [])
    bb = _mk_bb("L0")
    tq, tr = Temp("tq"), Temp("tr")
    bb.add(BinOp(dst=tq, op="/", left=Const(10), right=Const(3)))
    bb.add(BinOp(dst=tr, op="%", left=Const(10), right=Const(3)))
    bb.add(Return())
    fn.blocks.append(bb)

    asm = emit_function(fn, plan=_plan("idiv"))

    # div rs, rt ; mflo rd  (cociente)
    assert re.search(r"\bdiv\s+\$t\d,\s*\$t\d", asm)
    assert re.search(r"\bmflo\s+\$t\d", asm)
    # div rs, rt ; mfhi rd  (resto)
    assert re.search(r"\bmfhi\s+\$t\d", asm)

def test_shifts_immediate_and_variable():
    fn = Function("shifts", [])
    bb = _mk_bb("L0")
    ti1, tv1, kv = Temp("ti1"), Temp("tv1"), Temp("kv")
    # inmed.:  (1 << 3), (1 >> 2), (1 >>> 1)
    bb.add(BinOp(dst=ti1, op="<<", left=Const(1), right=Const(3)))
    bb.add(BinOp(dst=Temp("ti2"), op=">>", left=Const(1), right=Const(2)))
    bb.add(BinOp(dst=Temp("ti3"), op=">>>", left=Const(1), right=Const(1)))
    # variable: kv = 2; (1 << kv), (1 >> kv), (1 >>> kv)
    bb.add(UnaryOp(dst=kv, op="+", value=Const(2)))  # truco simple para materializar 2 en un $t*
    # Nota: si tu IR no usa UnaryOp("+",...), reemplaza por Assign(dst=kv, src=Const(2))
    # (deja cualquiera de las dos formas; los tests buscan los shifts, no la carga).
    bb.add(BinOp(dst=tv1, op="<<", left=Const(1), right=kv))
    bb.add(BinOp(dst=Temp("tv2"), op=">>", left=Const(1), right=kv))
    bb.add(BinOp(dst=Temp("tv3"), op=">>>", left=Const(1), right=kv))
    bb.add(Return())
    fn.blocks.append(bb)

    asm = emit_function(fn, plan=_plan("shifts"))

    # inmed
    assert re.search(r"\bsll\s+\$t\d,\s*\$t\d,\s*3", asm)
    assert re.search(r"\bsra\s+\$t\d,\s*\$t\d,\s*2", asm)
    assert re.search(r"\bsrl\s+\$t\d,\s*\$t\d,\s*1", asm)
    # variables
    assert re.search(r"\bsllv\s+\$t\d,\s*\$t\d,\s*\$t\d", asm)
    assert re.search(r"\bsrav\s+\$t\d,\s*\$t\d,\s*\$t\d", asm)
    assert re.search(r"\bsrlv\s+\$t\d,\s*\$t\d,\s*\$t\d", asm)

def test_bitwise_and_or_xor():
    fn = Function("bitops", [])
    bb = _mk_bb("L0")
    bb.add(BinOp(dst=Temp("ta"), op="&", left=Const(6), right=Const(3)))
    bb.add(BinOp(dst=Temp("to"), op="|", left=Const(5), right=Const(2)))
    bb.add(BinOp(dst=Temp("tx"), op="^", left=Const(7), right=Const(1)))
    bb.add(Return())
    fn.blocks.append(bb)

    asm = emit_function(fn, plan=_plan("bitops"))

    assert re.search(r"\band\s+\$t\d,\s*\$t\d,\s*\$t\d", asm)
    assert re.search(r"\bor\s+\$t\d,\s*\$t\d,\s*\$t\d", asm)
    assert re.search(r"\bxor\s+\$t\d,\s*\$t\d,\s*\$t\d", asm)
