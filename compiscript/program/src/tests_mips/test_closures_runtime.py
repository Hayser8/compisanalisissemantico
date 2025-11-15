import re
from src.ir.model import Program, Function, BasicBlock, Label
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.data import StringPool, GlobalsTable

def _mk_fn(name: str) -> Function:
    fn = Function(name, [])
    bb = BasicBlock(Label("L0")); fn.blocks.append(bb)
    return fn

def _plan(fn: Function) -> FramePlan:
    return FramePlan(func_name=fn.name, param_names=[], local_names=[], need_param_homes=0).build()

def test_runtime_closure_helpers_present_and_use_jalr():
    prog = Program()
    prog.functions.append(_mk_fn("main"))

    asm = emit_full_program(
        prog,
        pool=StringPool(),
        gtab=GlobalsTable(),
        plan_for_fn=_plan,
        layouts=None,
    )

    # Están las etiquetas
    assert "__make_closure:" in asm
    assert "__closure_apply:" in asm

    # __closure_apply debe cargar codeptr en $t9 y hacer jalr $t9
    assert re.search(r"__closure_apply:.*\blw\s+\$t9,\s*0\(\$a0\)", asm, flags=re.S)
    assert re.search(r"__closure_apply:.*\bjalr\s+\$t9\b", asm, flags=re.S)

