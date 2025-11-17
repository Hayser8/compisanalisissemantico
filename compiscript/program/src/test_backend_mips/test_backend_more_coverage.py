# program/src/test_backend_mips/test_backend_more_coverage.py

import re
import pytest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # -> /program
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.emitter import emit_function
from src.backend.mips.objects import LayoutRegistry
from src.backend.mips.regalloc import RegAlloc
from src.ir.model import Program, Function, BasicBlock, LabelInstr, Return, Name, Const

def _simple_block(ret_name: str) -> BasicBlock:
    # Bloque: L0: return <ret_name>;
    lab = LabelInstr(label=Name("L0"))  # ajusta si tu Label es otra clase
    ret = Return(value=Name(ret_name))
    return BasicBlock(label=lab.label, instrs=[lab, ret])

def test_method_this_param_has_home_for_methods():
    """
    Verifica que para un método tipo Class::meth(this),
    el emitter genere un 'sw $a0, off($fp)' en el prólogo.
    """
    fn = Function(
        name="Animal::speak",
        params=[Name("this")],
        blocks=[_simple_block("this")],
    )

    # FramePlan que dice: un param con home y un slot -4
    plan = FramePlan(
        func_name=fn.name,
        param_names=["this"],
        local_names=[],
        need_param_homes=1,
    ).build()

    asm = emit_function(fn, plan=plan, layouts=LayoutRegistry())

    # Tiene que haber un store desde a0 a algún offset negativo
    assert re.search(r"sw \$a0,\s*-\d+\(\$fp\)", asm), asm


def test_two_params_are_copied_to_homes():
    """
    Para una función sum2(x,y), el prólogo debe copiar a0→slot,
    a1→slot, sin dejar parámetros “fantasma”.
    """
    fn = Function(
        name="sum2",
        params=[Name("x"), Name("y")],
        blocks=[_simple_block("x")],
    )
    plan = FramePlan(
        func_name=fn.name,
        param_names=["x", "y"],
        local_names=[],
        need_param_homes=2,
    ).build()

    asm = emit_function(fn, plan=plan, layouts=LayoutRegistry())

    # Debe haber un sw $a0,... y un sw $a1,...
    assert "sw $a0," in asm, asm
    assert "sw $a1," in asm, asm

from src.backend.mips.emitter import emit_epilogue

def test_all_non_main_epilogues_guard_ra_zero():
    ep = "\n".join(emit_epilogue(256, exit_main=False))
    # Debe contener el patrón de guardia
    assert "beq $ra, $zero, __cps_halt" in ep
    assert "jr $ra" in ep

from src.backend.mips.runner import run_asm, have_any_sim

@pytest.mark.skipif(not have_any_sim(), reason="No MIPS simulator available")
def test_new_array_runtime_works_in_mars():
    """
    Prueba el runtime __new_array: crea array[3], escribe 1,2,3 usando $t0
    como base y verifica que la suma da 6.
    """
    asm = r"""
    .text
    .globl main
    main:
      li $t4, 3
      move $a0, $t4
      jal __new_array        # v0 = base, t0 = base (contrato runtime)
      # llenamos arr[0]..arr[2] usando t0
      li $t1, 0
      li $t4, 1
      sll $t3, $t1, 2
      addu $t3, $t0, $t3
      sw $t4, 0($t3)

      li $t1, 1
      li $t4, 2
      sll $t3, $t1, 2
      addu $t3, $t0, $t3
      sw $t4, 0($t3)

      li $t1, 2
      li $t4, 3
      sll $t3, $t1, 2
      addu $t3, $t0, $t3
      sw $t4, 0($t3)

      # sumamos arr[0] + arr[1] + arr[2] en t2
      li $t2, 0
      li $t1, 0
    sum_loop:
      slti $t5, $t1, 3
      beq $t5, $zero, end
      sll $t3, $t1, 2
      addu $t3, $t0, $t3
      lw   $t6, 0($t3)
      addu $t2, $t2, $t6
      addi $t1, $t1, 1
      j sum_loop
    end:
      move $a0, $t2        # imprimir resultado
      li $v0, 1
      syscall
      li $v0, 10
      syscall

    __new_array:
      sll  $a0, $a0, 2
      li   $v0, 9
      syscall
      move $t0, $v0
      jr   $ra
    """

    code, out, err = run_asm(asm)
    assert code == 0
    assert "6" in out  # arr[0]+arr[1]+arr[2] = 1+2+3

@pytest.mark.skipif(not have_any_sim(), reason="No MIPS simulator available")
def test_recursive_factorial_runs_in_mars():
    asm = r"""
    .text
    .globl main

    main:
      li $a0, 5
      jal factorial
      move $a0, $v0   # imprimir factorial(5) = 120
      li $v0, 1
      syscall
      li $v0, 10
      syscall

    factorial:
      addiu $sp, $sp, -256
      sw $fp, 0($sp)
      sw $ra, 4($sp)
      addiu $fp, $sp, 256
      sw $a0, -4($fp)
    fac_L0:
      lw $t0, -4($fp)
      li $t1, 1
      slt $t2, $t0, $t1   # t2 = (n < 1)
      bne $t2, $zero, fac_base
      # recursivo
      lw $t0, -4($fp)
      addiu $t0, $t0, -1
      move $a0, $t0
      jal factorial
      lw $t0, -4($fp)
      mul $v0, $v0, $t0
      j fac_epilogue
    fac_base:
      li $v0, 1
    fac_epilogue:
      lw $fp, 0($sp)
      lw $ra, 4($sp)
      addiu $sp, $sp, 256
      beq $ra, $zero, __cps_halt
      nop
      jr $ra

    __cps_halt:
      li $v0, 10
      syscall
    """
    code, out, err = run_asm(asm)
    assert code == 0
    assert "120" in out
