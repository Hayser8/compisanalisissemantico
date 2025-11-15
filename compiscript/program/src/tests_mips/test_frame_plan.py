# program/src/tests_mips/test_frame_plan.py
from src.backend.mips.frame_plan import FramePlan, WORD
from src.backend.mips.emitter import emit_function_skeleton

def _has(lines, frag: str) -> bool:
    return any(frag in ln for ln in lines)

def test_frame_plan_offsets_and_frame_size_basic():
    plan = FramePlan(
        func_name="f",
        param_names=["a", "b", "c"],
        local_names=["x", "y"],
        need_param_homes=3,   # $a0..$a2
        spill_bytes=0,
    ).build()

    # Param homes: -4, -8, -12
    assert plan.home_offset_for_param_index(0) == -4
    assert plan.home_offset_for_param_index(1) == -8
    assert plan.home_offset_for_param_index(2) == -12

    # Locals siguen: -16, -20
    assert plan.offset_of_local("x") == -16
    assert plan.offset_of_local("y") == -20

    # frame_size = negative_area(20) + 8(fp/ra) = 28 -> alineado a 32
    assert plan.frame_size == 32

def test_emitter_uses_plan_and_emits_prologue_epilogue_and_param_homes():
    plan = FramePlan(
        func_name="A::m",
        param_names=["this", "n"],
        local_names=["tmp"],
        need_param_homes=2,  # $a0(this), $a1(n)
    ).build()

    asm = emit_function_skeleton("A::m", plan)

    # Label mangled
    assert asm[0] == "A__m:"

    # Prologue con frame_size alineado
    assert _has(asm, "addiu $sp, $sp, -")
    assert _has(asm, "sw $ra, ")
    assert _has(asm, "sw $fp, ")
    assert _has(asm, "move $fp, $sp")

    # Copia de params a homes
    assert _has(asm, "sw $a0, -4($fp)")
    assert _has(asm, "sw $a1, -8($fp)")

    # Epilogue correcto
    assert _has(asm, "move $sp, $fp")
    assert asm[-1] == "jr $ra"
