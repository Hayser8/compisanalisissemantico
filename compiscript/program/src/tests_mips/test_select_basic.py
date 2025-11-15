# program/src/tests_mips/test_select_basic.py
import re
from src.ir.model import Program, Function, BasicBlock, Label, LabelInstr, Temp, Name, Const, BinOp, Assign, Return, IfGoto, Goto, Call, Load, Store
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.emitter import emit_function

def _mk_bb(name: str) -> BasicBlock:
    return BasicBlock(label=Label(name), instrs=[LabelInstr(Label(name))])

def test_add_and_return():
    fn = Function("sum2", ["a", "b"])
    bb = _mk_bb("L0")
    t0 = Temp("t0")
    a = Name("a"); b = Name("b")
    bb.add(BinOp(dst=t0, op="+", left=a, right=b))
    bb.add(Return(value=t0))
    fn.blocks.append(bb)

    plan = FramePlan(func_name="sum2", param_names=["a","b"], local_names=[], need_param_homes=2).build()
    asm = emit_function(fn, plan=plan)

    # debe aparecer 'addu $t?, $t?, $t?' y salto al epílogo
    assert re.search(r"\baddu\s+\$t\d,\s*\$t\d,\s*\$t\d", asm)
    assert "__epilogue" in asm

def test_ifgoto_and_labels():
    fn = Function("cond", ["x"])
    bb = _mk_bb("L0")
    t0 = Temp("t0")
    x = Name("x")
    # t0 = (x == 0); if t0 goto L1; goto L2;
    bb.add(BinOp(dst=t0, op="==", left=x, right=Const(0)))
    bb.add(IfGoto(cond=t0, target=Label("L1")))
    bb.add(Goto(target=Label("L2")))
    fn.blocks.append(bb)
    # añade labels de destino para que existan
    bb1 = _mk_bb("L1"); fn.blocks.append(bb1)
    bb2 = _mk_bb("L2"); fn.blocks.append(bb2)

    plan = FramePlan(func_name="cond", param_names=["x"], local_names=[], need_param_homes=1).build()
    asm = emit_function(fn, plan=plan)

    assert re.search(r"\bseq\s+\$t\d,\s*\$t\d,\s*\$t\d", asm) or re.search(r"\bseq\b", asm)
    assert re.search(r"\bbne\s+\$t\d,\s*\$zero,\s*L1", asm)
    assert "L2:" in asm

def test_call_and_move_v0():
    fn = Function("caller", ["a"])
    bb = _mk_bb("L0")
    t0 = Temp("t0")
    bb.add(Call(dst=t0, func="foo", args=[Name("a")]))
    bb.add(Return(value=t0))
    fn.blocks.append(bb)

    plan = FramePlan(func_name="caller", param_names=["a"], local_names=[], need_param_homes=1).build()
    asm = emit_function(fn, plan=plan)

    # mueve arg a $a0, jal foo, move t?,$v0
    assert re.search(r"\bmove\s+\$a0,\s*\$t\d", asm)
    assert "jal foo" in asm
    assert re.search(r"\bmove\s+\$t\d,\s*\$v0", asm)

def test_array_index_load_store():
    fn = Function("arr", [])
    bb = _mk_bb("L0")
    t0 = Temp("t0")
    arr = Name("arr")
    idx = Name("i")
    # t0 = load arr[i]; store arr[i], t0
    bb.add(Load(dst=t0, array=arr, index=idx))
    bb.add(Store(array=arr, index=idx, value=t0))
    bb.add(Return())
    fn.blocks.append(bb)

    plan = FramePlan(func_name="arr", param_names=[], local_names=["arr","i"], need_param_homes=0).build()
    asm = emit_function(fn, plan=plan)

    # sll idx, idx, 2 ; addu ... ; lw/sw 0(...)
    assert re.search(r"\bsll\s+\$t\d,\s*\$t\d,\s*2", asm)
    assert re.search(r"\baddu\s+\$t\d,\s*\$t\d,\s*\$t\d", asm)
    assert re.search(r"\blw\s+\$t\d,\s*0\(\$t\d\)", asm)
    assert re.search(r"\bsw\s+\$t\d,\s*0\(\$t\d\)", asm)
