import re

from src.ir.model import Program, Function, BasicBlock, Label, LabelInstr
from src.ir.model import Temp, Name, Const, Assign, Return
from src.ir.model import MakeClosure, CallClosure
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.data import StringPool, GlobalsTable


def _mk_fn(name: str) -> Function:
    fn = Function(name, [])
    bb = BasicBlock(Label("L0"))
    bb.add(LabelInstr(bb.label))
    fn.blocks.append(bb)
    return fn


def _plan_with_locals(locals_list):
    def _plan(fn: Function) -> FramePlan:
        # homes de params = 0; declara locals para que Name(...) tenga slot
        return FramePlan(func_name=fn.name,
                         param_names=[],
                         local_names=list(locals_list),
                         need_param_homes=0).build()
    return _plan


def test_make_closure_alloc_env_copy_and_jal():
    """
    Verifica que MakeClosure:
      - reserva env con sbrk (li $v0,9 / li $a0, K*4 / syscall),
      - copia capturas con 'sw ... 0(..)' y 'sw ... 4(..)',
      - hace 'la $a0, f' y 'jal __make_closure',
      - mueve $v0 al destino.
    """
    prog = Program()
    main = _mk_fn("main")
    bb = main.blocks[0]

    # x = 42  (para tener una captura Name('x'))
    bb.add(Assign(dst=Name("x"), src=Const(42)))
    # t1 = make_closure(f, [x, 7])
    bb.add(MakeClosure(dst=Temp("t1"), code="f", captures=[Name("x"), Const(7)]))
    # return 0 (no interesa el valor real aquí)
    bb.add(Return(Const(0)))
    prog.functions.append(main)

    asm = emit_full_program(
        prog,
        pool=StringPool(),
        gtab=GlobalsTable(),
        plan_for_fn=_plan_with_locals(["x"]),
        layouts=None,
    )

    # sbrk de 8 bytes
    assert re.search(r"\bli\s+\$v0,\s*9\b", asm)
    assert re.search(r"\bli\s+\$a0,\s*8\b", asm)
    assert "syscall" in asm

    # sw de dos capturas en offsets 0 y 4 (no nos importa el registro base exacto)
    assert re.search(r"\bsw\s+\$\w+,\s*0\(\$\w+\)", asm)
    assert re.search(r"\bsw\s+\$\w+,\s*4\(\$\w+\)", asm)

    # la $a0, f  y jal __make_closure
    assert re.search(r"\bla\s+\$a0,\s*f\b", asm)
    assert "jal __make_closure" in asm

    # el closure resultante en $v0 se mueve a algún destino
    assert re.search(r"\bmove\s+\$\w+,\s*\$v0\b", asm)


def test_call_closure_moves_a0_and_args_and_jal_apply():
    """
    Verifica que CallClosure:
      - mueve el closure a $a0,
      - mueve hasta 3 args a $a1..$a3,
      - llama a __closure_apply,
      - mueve $v0 al destino.
    """
    prog = Program()
    main = _mk_fn("main")
    bb = main.blocks[0]

    # tC = make_closure(f, [])      ; sin capturas
    bb.add(MakeClosure(dst=Temp("tC"), code="f", captures=[]))
    # tR = call_closure(tC, 1, 2)   ; 2 args -> $a1 y $a2
    bb.add(CallClosure(dst=Temp("tR"), closure=Temp("tC"), args=[Const(1), Const(2)]))
    bb.add(Return(Temp("tR")))
    prog.functions.append(main)

    asm = emit_full_program(
        prog,
        pool=StringPool(),
        gtab=GlobalsTable(),
        plan_for_fn=_plan_with_locals([]),
        layouts=None,
    )

    # $a0 <- closure, $a1/$a2 <- args
    # No verificamos el registro origen exacto, sólo el patrón move a $a*
    assert re.search(r"\bmove\s+\$a0,\s*\$\w+\b", asm)
    assert re.search(r"\bmove\s+\$a1,\s*\$\w+\b", asm)
    assert re.search(r"\bmove\s+\$a2,\s*\$\w+\b", asm)

    # llamada al helper y movimiento del retorno
    assert "jal __closure_apply" in asm
    assert re.search(r"\bmove\s+\$\w+,\s*\$v0\b", asm)
