import re
from src.ir.model import Program, Function, BasicBlock, Label, Call, Return, Temp, Name, Const
from src.backend.mips.emitter import emit_full_program, emit_function
from src.backend.mips.frame_plan import FramePlan

def _mk_bb(lbl="L0"):
    return BasicBlock(label=Label(lbl))

def _plan(func_name="main"):
    return FramePlan(func_name=func_name, param_names=[], local_names=[], need_param_homes=0).build()


def test_print_int_and_exit_syscalls():
    prog = Program()
    main = Function("main", [])
    bb = _mk_bb()
    # __print_int(42); __exit()
    bb.add(Call(dst=None, func="__print_int", args=[Const(42)]))
    bb.add(Call(dst=None, func="__exit", args=[]))
    # (return opcional no requerido; el syscall 10 termina el programa)
    main.blocks.append(bb)
    prog.functions.append(main)

    asm = emit_full_program(
        prog, pool=type("P", (), {})(), gtab=type("G", (), {})(),
        plan_for_fn=lambda fn: _plan("main"), layouts=None
    )

    # Debe mover el arg a $a0, setear v0=1 y syscall
    assert re.search(r"\bmove\s+\$a0,\s*\$t\d", asm)
    assert re.search(r"\bli\s+\$v0,\s*1\b", asm)
    assert "syscall" in asm

    # Y debe existir el exit: v0=10; syscall
    assert re.search(r"\bli\s+\$v0,\s*10\b", asm)
    assert asm.count("syscall") >= 2


def test_read_int_returns_value():
    fn = Function("readint", [])
    bb = _mk_bb()
    t = Temp("t")
    bb.add(Call(dst=t, func="__read_int", args=[]))
    bb.add(Return(t))
    fn.blocks.append(bb)

    asm = emit_function(fn, plan=_plan("readint"))

    # v0=5; syscall; move t?, v0
    assert re.search(r"\bli\s+\$v0,\s*5\b", asm)
    assert "syscall" in asm
    assert re.search(r"\bmove\s+\$t\d,\s*\$v0\b", asm)
