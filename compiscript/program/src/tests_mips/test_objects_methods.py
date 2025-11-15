import re
from src.ir.model import Function, BasicBlock, Label, LabelInstr, Return, Temp, Name, Const, GetProp, SetProp, NewObject, Call
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.emitter import emit_function
from src.backend.mips.objects import LayoutRegistry

def _mk_bb(name):
    bb = BasicBlock(Label(name))
    bb.add(LabelInstr(Label(name)))
    return bb

def test_newobject_allocates_with_sbrk_and_get_set_prop_use_offsets():
    # Layout: class A { x, y }
    layouts = LayoutRegistry()
    layouts.register_class("A", ["x", "y"])  # x=0, y=4

    fn = Function("demo", [])
    bb = _mk_bb("L0")
    t0 = Temp("t0")  # obj
    t1 = Temp("t1")  # readback
    # t0 = new A()
    bb.add(NewObject(dst=t0, class_name="A", args=[]))
    # set t0.x = 42
    bb.add(SetProp(obj=t0, prop="x", value=Const(42)))
    # t1 = get t0.x
    bb.add(GetProp(dst=t1, obj=t0, prop="x"))
    bb.add(Return(value=t1))
    fn.blocks.append(bb)

    plan = FramePlan(func_name="demo", param_names=[], local_names=[], need_param_homes=0).build()
    asm = emit_function(fn, plan=plan, layouts=layouts)

    # Syscall sbrk sequence
    assert "li $v0, 9" in asm
    assert "li $a0, 8" in asm   # tamaño de A: 2 campos * 4
    assert "syscall" in asm
    # set/get usan offset 0
    assert re.search(r"\bsw\s+\$t\d,\s*0\(\$t\d\)", asm)
    assert re.search(r"\blw\s+\$t\d,\s*0\(\$t\d\)", asm)

def test_method_call_convention_this_in_a0():
    # Llamada a A::m(obj, n)
    layouts = LayoutRegistry()
    layouts.register_class("A", ["x"])

    fn = Function("caller", [])
    bb = _mk_bb("L0")
    t0 = Temp("t0")
    t1 = Temp("t1")
    # obj = new A(); r = call A__m(obj, 7)
    bb.add(NewObject(dst=t0, class_name="A", args=[]))
    bb.add(Call(dst=t1, func="A__m", args=[t0, Const(7)]))
    bb.add(Return(value=t1))
    fn.blocks.append(bb)

    plan = FramePlan(func_name="caller", param_names=[], local_names=[], need_param_homes=0).build()
    asm = emit_function(fn, plan=plan, layouts=layouts)

    # Debe mover primer arg a $a0 (this) y segundo a $a1, luego jal A__m
    assert re.search(r"\bmove\s+\$a0,\s*\$t\d", asm)
    assert re.search(r"\bmove\s+\$a1,\s*\$t\d", asm)
    assert "jal A__m" in asm
