import re
from src.ir.model import Program, Function, BasicBlock, Label, LabelInstr, Return, Const, Assign, Name
from src.backend.mips.data import StringPool, GlobalsTable
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.frame_plan import FramePlan

def _mk_fn(name="main"):
    fn = Function(name, [])
    bb = BasicBlock(Label("L0"))
    bb.add(LabelInstr(Label("L0")))
    bb.add(Return())
    fn.blocks.append(bb)
    return fn

def _simple_plan(fn: Function):
    # Necesita homes para params (0..4) y locals según nombres en el IR si quisieras.
    # Aquí: sin params/locals -> frame mínimo 16 (slots $ra/$fp y alineo).
    return FramePlan(func_name=fn.name, param_names=fn.params, local_names=[], need_param_homes=min(len(fn.params), 4)).build()

def test_string_pool_emits_asciiz_and_dedup():
    pool = StringPool()
    gtab = GlobalsTable()
    prog = Program()

    # Deduplicación
    l1 = pool.ensure_label("hola")
    l2 = pool.ensure_label("hola")
    l3 = pool.ensure_label("adiós\n\"c\"\t\\")
    assert l1 == l2
    assert l1 != l3

    # Programa con main vacío (para tener .text)
    prog.functions.append(_mk_fn("main"))
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_simple_plan)

    # .data contiene las dos entradas (hola, adiós...)
    assert '.data' in asm
    # etiqueta y contenido escapado
    assert re.search(rf'^{l1}:\s+\.asciiz\s+"hola"$', asm, flags=re.M)
    assert re.search(rf'^{l3}:\s+\.asciiz\s+"adiós\\n\\\"c\\\"\\t\\\\"$', asm, flags=re.M)

def test_globals_emitted_before_strings():
    pool = StringPool()
    gtab = GlobalsTable()
    gtab.define_word("FINAL", 0)
    gtab.define_word("counter", 42)

    prog = Program(); prog.functions.append(_mk_fn("main"))
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_simple_plan)

    # Globales aparecen en .data
    assert re.search(r"^FINAL:\s+\.word\s+0$", asm, flags=re.M)
    assert re.search(r"^counter:\s+\.word\s+42$", asm, flags=re.M)
    # Y .text después
    assert ".text" in asm and ".globl main" in asm

def test_function_and_text_are_emitted():
    pool = StringPool()
    gtab = GlobalsTable()
    prog = Program(); prog.functions.append(_mk_fn("main"))
    asm = emit_full_program(prog, pool=pool, gtab=gtab, plan_for_fn=_simple_plan)

    # Hay label main y epílogo estándar
    assert re.search(r"^main:", asm, flags=re.M)
    assert "main__epilogue:" in asm
