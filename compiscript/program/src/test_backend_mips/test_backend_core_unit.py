# program/src/test_backend_mips/test_backend_core_unit.py

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # -> /program
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ir.model import (
    Program,
    Function,
    BasicBlock,
    Label,
    LabelInstr,
    Assign,
    BinOp,
    Return,
    Load,
    Store,
    Name,
    Const,
    Temp,
    MakeClosure,
    CallClosure,
)

from src.backend.mips.frame_plan import FramePlan, WORD
from src.backend.mips.emit_utils import (
    emit_prologue,
    emit_epilogue,
    asm_lw_fp,
    asm_sw_fp,
)
from src.backend.mips.regalloc import RegAlloc
from src.backend.mips.templates import emit_for_instr
from src.backend.mips.objects import LayoutRegistry
from src.backend.mips.emitter import emit_function, emit_full_program
from src.backend.mips.data import StringPool, GlobalsTable


# --------------------------------------------------------------------
# Helpers compartidos
# --------------------------------------------------------------------

def _collect_names_from_obj(obj, acc: set):
    """Busca src.ir.model.Name recursivamente y mete sus .name en acc."""
    from src.ir.model import Name

    if isinstance(obj, Name):
        acc.add(obj.name)
        return
    if isinstance(obj, (list, tuple)):
        for x in obj:
            _collect_names_from_obj(x, acc)
        return
    if hasattr(obj, "__dict__"):
        for v in obj.__dict__.values():
            _collect_names_from_obj(v, acc)


def infer_locals(fn: Function) -> list[str]:
    """Inferir nombres locales de la función (Names que no son parámetros)."""
    from src.ir.model import Name

    param_names = [getattr(p, "name", "") for p in fn.params]
    used: set[str] = set()

    for bb in fn.blocks:
        for ins in bb.instrs:
            _collect_names_from_obj(ins, used)

    return sorted(n for n in used if n and n not in param_names)


def plan_for_fn(fn: Function) -> FramePlan:
    param_names = [getattr(p, "name", "") for p in fn.params]
    local_names = infer_locals(fn)
    plan = FramePlan(
        func_name=fn.name,
        param_names=param_names,
        local_names=local_names,
        need_param_homes=len(param_names),
    )
    plan.build()
    return plan


# --------------------------------------------------------------------
# 1) FramePlan + prólogo / epílogo
# --------------------------------------------------------------------

def test_frame_plan_offsets_and_prologue_epilogue_symmetry():
    plan = FramePlan(
        func_name="f",
        param_names=["a", "b"],
        local_names=["x", "y"],
        need_param_homes=2,
        spill_bytes=16,
    ).build()

    # Offsets de params: -4, -8
    assert plan.param_home_off[0] == -4
    assert plan.param_home_off[1] == -8

    # Locals continúan: -12, -16
    assert plan.local_off["x"] == -12
    assert plan.local_off["y"] == -16

    # negative_size = params(8) + locals(8) + spills(16) = 32
    assert plan.negative_size == 32

    # frame_size = negative_size + 8, alineado a 8
    assert plan.frame_size == 40

    # Todos los offsets deben ser negativos
    all_offs = list(plan.param_home_off.values()) + list(plan.local_off.values())
    assert all(o < 0 for o in all_offs)

    # No debe haber problema al usarlos con asm_lw_fp / asm_sw_fp
    lines = []
    for off in all_offs:
        asm_lw_fp(lines, "$t0", off)
        asm_sw_fp(lines, "$t0", off)

    # Prólogo / epílogo simétricos y con beq+nop en epílogo normal
    pro = emit_prologue(plan.frame_size)
    epi = emit_epilogue(plan.frame_size, exit_main=False)

    assert pro[0] == "  addiu $sp, $sp, -40"
    assert epi[2] == "  addiu $sp, $sp, 40"
    assert "beq $ra, $zero, __cps_halt" in epi[3]
    assert epi[4] == "  nop"
    assert epi[-1] == "  jr $ra"


# --------------------------------------------------------------------
# 2) RegAlloc: spills siempre negativos y alejados
# --------------------------------------------------------------------

def test_regalloc_spill_offsets_are_negative_and_monotonic():
    # Frame simple: 1 param + 1 local
    plan = FramePlan(
        func_name="g",
        param_names=["p"],
        local_names=["x"],
        need_param_homes=1,
    ).build()

    ra = RegAlloc(plan)

    o1 = ra._alloc_spill_slot()
    o2 = ra._alloc_spill_slot()

    assert o1 < 0
    assert o2 < 0
    # El segundo spill debe estar "más abajo" (más negativo)
    assert o2 < o1

    # El tamaño de spills en el plan debe reflejar 2 palabras
    assert plan.spill_bytes >= 2 * WORD

    # Los offsets deben ser válidos para asm_sw_fp
    out: list[str] = []
    asm_sw_fp(out, "$t0", o1)
    asm_sw_fp(out, "$t1", o2)
    # Si hubiera offset >= 0, asm_sw_fp lanzaría ValueError


# --------------------------------------------------------------------
# 3) BinOp con shift inmediato (regresión de bug en >>)
# --------------------------------------------------------------------

def test_binop_shift_right_immediate_generates_sra_with_source():
    l0 = Label("L0")
    bb = BasicBlock(
        label=l0,
        instrs=[
            LabelInstr(label=l0),
            Assign(dst=Name("x"), src=Const(8)),
            BinOp(dst=Name("y"), op=">>", left=Name("x"), right=Const(1)),
            Return(value=None),
        ],
    )
    fn = Function(name="shift_fn", params=[], blocks=[bb])
    plan = plan_for_fn(fn)
    asm = emit_function(fn, plan=plan, layouts=LayoutRegistry())

    # Debe haber una instrucción de la forma: sra $t0, $tx, 1
    assert "sra " in asm
    # Más fuerte: alguna línea tiene 'sra $t0' y una coma luego (registro fuente)
    assert any("sra $t0" in ln and "," in ln for ln in asm.splitlines())


# --------------------------------------------------------------------
# 4) Arrays: Load / Store calculan base + idx*4
# --------------------------------------------------------------------

def test_array_load_and_store_use_index_times_4():
    l0 = Label("L0")
    bb = BasicBlock(
        label=l0,
        instrs=[
            LabelInstr(label=l0),
            Assign(dst=Name("arr"), src=Const(0)),   # valor irrelevante
            Store(array=Name("arr"), index=Const(3), value=Const(42)),
            Load(dst=Name("tmp"), array=Name("arr"), index=Const(3)),
            Return(value=Name("tmp")),
        ],
    )
    fn = Function(name="arr_fn", params=[], blocks=[bb])
    plan = plan_for_fn(fn)
    asm = emit_function(fn, plan=plan, layouts=LayoutRegistry())

    lines = asm.splitlines()
    # Debe aparecer sll $t3, <idx_reg>, 2
    assert any("sll $t3" in ln and ", 2" in ln for ln in lines)
    # Luego un 'addu $t3, base, $t3'
    assert any("addu $t3" in ln for ln in lines)
    # Y un 'sw' y 'lw' a 0($t3)
    assert any("sw" in ln and "0($t3)" in ln for ln in lines)
    assert any("lw" in ln and "0($t3)" in ln for ln in lines)


# --------------------------------------------------------------------
# 5) Closures: MakeClosure + CallClosure generan secuencias correctas
# --------------------------------------------------------------------

def test_make_and_call_closure_sequences():
    l0 = Label("L0")
    l_body = Label("L_clo")

    bb = BasicBlock(
        label=l0,
        instrs=[
            LabelInstr(label=l0),
            # Crear closure con 1 capture
            MakeClosure(dst=Name("clo"), code=l_body, captures=[Const(1)]),
            # Llamarla con 2 argumentos lógicos
            CallClosure(dst=None, closure=Name("clo"), args=[Const(10), Const(20)]),
            Return(value=None),
            # Label del cuerpo del closure (no interesa su cuerpo en este test)
            LabelInstr(label=l_body),
            Return(value=None),
        ],
    )
    fn = Function(name="closure_fn", params=[], blocks=[bb])
    plan = plan_for_fn(fn)
    asm = emit_function(fn, plan=plan, layouts=LayoutRegistry())

    lines = asm.splitlines()

    # MakeClosure debe:
    #  - llamar a syscall 9 para el env
    #  - usar 'la $a0, L_clo'
    #  - llamar a __make_closure
    assert any("li $v0, 9" in ln for ln in lines)
    assert any("la $a0, L_clo" in ln for ln in lines)
    assert any("jal __make_closure" in ln for ln in lines)

    # CallClosure debe llamar a __closure_apply
    assert any("jal __closure_apply" in ln for ln in lines)


from src.backend.mips.closures import emit_runtime_closures


def test_runtime_closures_labels_and_exit():
    asm = emit_runtime_closures()
    lines = asm.splitlines()

    # Labels globales
    assert any(".globl __make_closure" in ln for ln in lines)
    assert any(".globl __closure_apply" in ln for ln in lines)
    assert any(".globl __cps_halt" in ln for ln in lines)

    # __cps_halt debe terminar con syscall 10
    idx = lines.index("__cps_halt:")
    tail = lines[idx : idx + 4]
    assert any("li   $v0, 10" in ln or "li $v0, 10" in ln for ln in tail)
    assert any("syscall" in ln for ln in tail)


# --------------------------------------------------------------------
# 6) .data: strings y globales en emit_full_program
# --------------------------------------------------------------------

def test_emit_full_program_data_strings_and_globals():
    # --- Program mínimo: main que retorna ---
    l0 = Label("L0")
    main_fn = Function(
        name="main",
        params=[],
        blocks=[BasicBlock(label=l0, instrs=[LabelInstr(label=l0), Return(value=None)])],
    )
    prog = Program(functions=[main_fn])

    # --- Pool de strings / globales ---
    pool = StringPool()
    pool.ensure_label("hola")
    pool.ensure_label("adios")

    gtab = GlobalsTable()
    gtab.define_word("G0", 123)

    asm = emit_full_program(
        prog,
        pool=pool,
        gtab=gtab,
        plan_for_fn=plan_for_fn,
        layouts=LayoutRegistry(),
    )

    # Debe existir sección .data y .text
    assert ".data" in asm
    assert ".text" in asm

    # Global definido
    assert "G0: .word 123" in asm

    # Alguna string __str_0 / __str_1 con .asciiz
    assert "__str_0" in asm
    assert ".asciiz" in asm


# --------------------------------------------------------------------
# 7) Stubs de métodos __mcall__X
# --------------------------------------------------------------------

def test_method_stub_emission_for_mcall():
    # Un método de clase simulado
    l0 = Label("L0")
    meth_fn = Function(
        name="Point::move",
        params=[Name("this")],
        blocks=[BasicBlock(label=l0, instrs=[LabelInstr(label=l0), Return(value=None)])],
    )

    # main vacío para que haya entrypoint
    l1 = Label("L1")
    main_fn = Function(
        name="main",
        params=[],
        blocks=[BasicBlock(label=l1, instrs=[LabelInstr(label=l1), Return(value=None)])],
    )

    prog = Program(functions=[main_fn, meth_fn])

    pool = StringPool()
    gtab = GlobalsTable()

    asm = emit_full_program(
        prog,
        pool=pool,
        gtab=gtab,
        plan_for_fn=plan_for_fn,
        layouts=LayoutRegistry(),
    )

    lines = asm.splitlines()

    # Debe aparecer el stub __mcall__move que hace jal Point__move
    assert any(ln.strip() == "__mcall__move:" for ln in lines)
    assert any("jal Point__move" in ln for ln in lines)
