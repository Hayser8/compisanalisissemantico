# program/src/tests_mips/test_cfg_emit.py
import re
from src.ir.model import Function, BasicBlock, Label, LabelInstr, Name, Temp, Const, BinOp, IfGoto, Goto, Return
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.emitter import emit_function

def _bb(name):
    bb = BasicBlock(label=Label(name))
    bb.add(LabelInstr(Label(name)))
    return bb

def test_if_else_emission_no_fallthrough():
    fn = Function("iff", ["c"])
    t0 = Temp("t0")
    c  = Name("c")

    b0 = _bb("L0")
    # t0 = c == 0
    b0.add(BinOp(dst=t0, op="==", left=c, right=Const(0)))
    # if t0 goto L1_then else L2_else
    b0.add(IfGoto(cond=t0, target=Label("L1_then")))
    b0.add(Goto(target=Label("L2_else")))
    fn.blocks.append(b0)

    b1 = _bb("L1_then"); b1.add(Return(Const(1))); fn.blocks.append(b1)
    b2 = _bb("L2_else"); b2.add(Return(Const(2))); fn.blocks.append(b2)
    b3 = _bb("L3_end");  fn.blocks.append(b3)  # será el epílogo físico

    plan = FramePlan(func_name="iff", param_names=["c"], local_names=[], need_param_homes=1).build()
    asm = emit_function(fn, plan=plan)

    # Deben existir las etiquetas
    assert "L0:" in asm
    assert "L1_then:" in asm
    assert "L2_else:" in asm
    # El return salta al epílogo (no hay fallthrough implícito)
    assert re.search(r"\n\s*j\s+iff__epilogue", asm)

def test_while_emission_shape():
    fn = Function("loop", ["x"])
    x = Name("x")
    t0 = Temp("t0")

    b0 = _bb("L0")
    b0.add(Goto(Label("L1_head")))
    fn.blocks.append(b0)

    b1 = _bb("L1_head")
    b1.add(BinOp(dst=t0, op="!=", left=x, right=Const(0)))
    b1.add(IfGoto(cond=t0, target=Label("L2_body")))
    b1.add(Goto(target=Label("L3_end")))
    fn.blocks.append(b1)

    b2 = _bb("L2_body")
    b2.add(Goto(Label("L1_head")))
    fn.blocks.append(b2)

    b3 = _bb("L3_end")
    b3.add(Return())
    fn.blocks.append(b3)

    plan = FramePlan(func_name="loop", param_names=["x"], local_names=[], need_param_homes=1).build()
    asm = emit_function(fn, plan=plan)

    # Orden y presencia de etiquetas clave
    assert "L1_head:" in asm and "L2_body:" in asm and "L3_end:" in asm
    # Debe existir el salto de cabeza a fin cuando la condición es falsa
    assert re.search(r"\n\s*j\s+L3_end", asm)
    # Return → epílogo
    assert re.search(r"\n\s*j\s+loop__epilogue", asm)

def test_all_targets_have_labels():
    fn = Function("flow", [])
    t0 = Temp("t0")

    b0 = _bb("L0")
    b0.add(BinOp(dst=t0, op="==", left=Const(1), right=Const(1)))
    b0.add(IfGoto(cond=t0, target=Label("L1")))
    b0.add(Goto(Label("L2")))
    fn.blocks.append(b0)
    fn.blocks.append(_bb("L1"))
    fn.blocks.append(_bb("L2"))
    fn.blocks[-1].add(Return())

    plan = FramePlan(func_name="flow", param_names=[], local_names=[], need_param_homes=0).build()
    asm = emit_function(fn, plan=plan)

    labels = set(re.findall(r"^([A-Za-z0-9_]+):", asm, flags=re.M))
    targets = set(re.findall(r"\b(?:j|bne|beq)\s+[^\s,]+,\s*([A-Za-z0-9_]+)|\b(?:j)\s+([A-Za-z0-9_]+)", asm))
    # 'targets' viene como tuplas por el OR del regex, aplanamos:
    flat_targets = {t for pair in targets for t in pair if t}
    # Todos los targets deben existir como etiqueta
    assert flat_targets.issubset(labels | {f"flow__epilogue"})

