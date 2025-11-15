import re
from src.ir.model import Program, Function, BasicBlock, Label, Temp, Name, Const, Assign, Call, Return, MakeClosure, CallClosure
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.data import StringPool, GlobalsTable

def _mk_fn(name="main"):
    fn = Function(name, [])
    bb = BasicBlock(Label("L0")); fn.blocks.append(bb)
    return fn

def _plan(locals=None, homes=0):
    return FramePlan(func_name="main", param_names=[], local_names=locals or [], need_param_homes=homes).build()

def test_call_more_than_4_args_spills_and_aligns():
    prog = Program()
    main = _mk_fn()
    bb = main.blocks[0]
    # prepara 6 args en temps/names para forzar registros + stack
    for i in range(6):
        bb.add(Assign(dst=Name(f"x{i}"), src=Const(i+1)))
    # t0 = call foo(x0,x1,x2,x3,x4,x5)
    bb.add(Call(dst=Temp("t0"), func="foo", args=[Name(f"x{i}") for i in range(6)]))
    bb.add(Return(Const(0)))
    prog.functions.append(main)

    asm = emit_full_program(
        prog, pool=StringPool(), gtab=GlobalsTable(),
        plan_for_fn=lambda fn: _plan(locals=[f"x{i}" for i in range(6)]), layouts=None
    )

    # Debe haber reserva de stack múltiplo de 8 para 2 extras -> 2*4=8 -> exacto
    assert re.search(r"addiu \$sp, \$sp, -8", asm)
    # sw de los extras en 0($sp) y 4($sp)
    assert re.search(r"\nsw \$s?\w+, 0\(\$sp\)", asm)  # puede ser $t* o $s* según RA
    assert re.search(r"\nsw \$s?\w+, 4\(\$sp\)", asm)
    # mueve 4 primeros a $a0..$a3
    assert re.search(r"move \$a0, ", asm)
    assert re.search(r"move \$a3, ", asm)
    # jal foo y cleanup
    assert "jal foo" in asm
    assert re.search(r"addiu \$sp, \$sp, 8", asm)

def test_nested_calls_caller_save_spills_temps():
    prog = Program()
    main = _mk_fn()
    bb = main.blocks[0]
    # tA = call f(1,2,3,4)    (usa $a0..$a3)
    bb.add(Call(dst=Temp("tA"), func="f", args=[Const(1),Const(2),Const(3),Const(4)]))
    # usa tA para computar arg de otra call -> requiere spill caller-save antes del siguiente jal
    bb.add(Call(dst=Temp("tB"), func="g", args=[Temp("tA")]))
    bb.add(Return(Temp("tB")))
    prog.functions.append(main)

    asm = emit_full_program(
        prog, pool=StringPool(), gtab=GlobalsTable(),
        plan_for_fn=lambda fn: _plan(), layouts=None
    )

    # Debe existir comentario de spill (lo insertamos explícitamente)
    assert "caller-save spill tA" in asm
    # Y el patrón de sw t* , off($fp)
    assert re.search(r"sw \$t\d, -\d+\(\$fp\)", asm)

def test_prologue_saves_sregs_when_names_used():
    prog = Program()
    main = _mk_fn()
    bb = main.blocks[0]
    # fuerza uso de Name persistente: leer y escribir varias veces
    bb.add(Assign(dst=Name("x"), src=Const(7)))
    bb.add(Assign(dst=Name("y"), src=Const(9)))
    bb.add(Call(dst=Temp("t0"), func="h", args=[Name("x"), Name("y")]))  # RA tenderá a dar $s* a Names
    bb.add(Return(Const(0)))
    prog.functions.append(main)

    asm = emit_full_program(
        prog, pool=StringPool(), gtab=GlobalsTable(),
        plan_for_fn=lambda fn: _plan(locals=["x","y"]), layouts=None
    )

    # En el prólogo deben guardarse algunos $s* si fueron usados
    # sw $sX, NN($sp)
    assert re.search(r"\nsw \$s[0-7], \d+\(\$sp\)", asm)
    # Y restaurarse en epílogo
    assert re.search(r"\nlw \$s[0-7], \d+\(\$sp\)", asm)
