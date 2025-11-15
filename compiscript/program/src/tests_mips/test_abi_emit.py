# program/src/tests_mips/test_abi_emit.py
import re

from src.backend.mips.abi import mangle_method_label, ARG_REGS, RET_REG
from src.backend.mips.emit_utils import (
    emit_prologue, emit_epilogue,
    emit_copy_params_to_homes, emit_move_args_to_a,
    emit_jal, emit_move_v0_to
)

def _join(lines):  # para asserts legibles
    return "\n".join(lines)

def test_mangle_method_label():
    assert mangle_method_label("A::m") == "A__m"
    assert mangle_method_label("main") == "main"

def test_prologue_epilogue_shape():
    pro = emit_prologue(32)    # frame_size 32
    epi = emit_epilogue(32)

    txt_pro = _join(pro)
    txt_epi = _join(epi)

    assert "addiu $sp, $sp, -32" in txt_pro
    assert "sw $ra, 28($sp)" in txt_pro
    assert "sw $fp, 24($sp)" in txt_pro
    assert "move $fp, $sp" in txt_pro

    assert txt_epi.endswith("jr $ra")
    assert "move $sp, $fp" in txt_epi
    assert "lw $fp, 24($sp)" in txt_epi
    assert "lw $ra, 28($sp)" in txt_epi

def test_copy_params_to_homes_ok():
    # 2 params con home slots -8 y -16
    lines = emit_copy_params_to_homes([-8, -16])
    txt = _join(lines)
    assert "sw $a0, -8($fp)" in txt
    assert "sw $a1, -16($fp)" in txt

def test_copy_params_to_homes_reject_non_negative():
    try:
        emit_copy_params_to_homes([0])
        assert False, "Debe rechazar offsets no-negativos para homes"
    except ValueError:
        pass

def test_move_args_to_a_ok():
    # mover tres argumentos desde t0,t1,t2 a $a0..$a2
    lines = emit_move_args_to_a(["$t0", "$t1", "$t2"])
    txt = _join(lines)
    assert "move $a0, $t0" in txt
    assert "move $a1, $t1" in txt
    assert "move $a2, $t2" in txt
    assert len(lines) == 3

def test_move_args_to_a_reject_gt4():
    try:
        emit_move_args_to_a(["$t0", "$t1", "$t2", "$t3", "$t4"])
        assert False, "Debe rechazar >4 args en este MVP"
    except ValueError:
        pass

def test_jal_and_move_v0_to_reg_or_mem():
    call_lines = emit_jal("foo")
    assert call_lines == ["jal foo"]

    to_reg = emit_move_v0_to("$t7")
    assert to_reg == ["move $t7, $v0"]

    to_mem = emit_move_v0_to(("mem", -20))
    assert to_mem == ["sw $v0, -20($fp)"]
