from __future__ import annotations
from typing import List, Sequence, Tuple, Union
import sys

Asm = List[str]

from .abi import SP, FP, RA, ARG_REGS, RET_REG
WORD = 4


def _dbg(msg: str) -> None:
    print(f"[EMIT_UTILS] {msg}", file=sys.stdout)


def _assert_neg(off: int) -> int:
    """
    Todos los homes (params, locals, spills) se direccionan con offsets NEGATIVOS
    respecto a $fp. Si algo quiere usar asm_lw_fp / asm_sw_fp con offset >= 0,
    es un bug de planificación del frame.
    """
    if off >= 0:
        raise ValueError(f"Home offset debe ser NEGATIVO, recibido {off}")
    return off


# =========================
#  PROLOGUE / EPILOGUE
# =========================
def emit_prologue(frame_size: int, save_s: List[str] | None = None) -> List[str]:
    """
    Genera el prólogo estándar de función.

    Convención de layout en memoria (relativa a $sp NUEVO):

        0($sp)   : old $fp
        4($sp)   : old $ra
        8($sp)   : $s0 (si se guarda)
        12($sp)  : $s1
        ...
        8+4k($sp): $s(k)  (en el orden de save_s)

    Y $fp se coloca al FINAL del frame:

        addiu $sp, $sp, -frame_size
        sw   $fp, 0($sp)
        sw   $ra, 4($sp)
        [sw $s*, 8+4*i($sp)]
        addiu $fp, $sp, frame_size

    IMPORTANTE:
      - frame_size DEBE ser al menos negative_size + 8 + 4*len(save_s),
        donde negative_size es la zona de params/locals/spills descrita por FramePlan.
      - Esa ampliación se hace en emitter.emit_function calculando frame_bytes.
    """
    if save_s is None:
        save_s = []

    lines: List[str] = []

    # Reserva frame completo
    lines.append(f"  addiu $sp, $sp, -{frame_size}")

    # Guarda old $fp y $ra
    lines.append("  sw $fp, 0($sp)")
    lines.append("  sw $ra, 4($sp)")

    # Guarda $s* (callee-saved) si corresponde
    if save_s:
        off = 8
        for reg in save_s:
            lines.append(f"  sw {reg}, {off}($sp)")
            off += 4

    # $fp apunta al tope lógico del frame
    lines.append(f"  addiu $fp, $sp, {frame_size}")
    return lines


def emit_epilogue(
    frame_size: int,
    *,
    restore_s: List[str] | None = None,
    exit_main: bool = False,
) -> List[str]:
    """
    Genera el epílogo estándar de función.

    Layout asumido (igual que en emit_prologue), relativo al $sp actual:

        0($sp)   : old $fp
        4($sp)   : old $ra
        8($sp)   : $s0 (si se guardó)
        12($sp)  : $s1
        ...

    Secuencia general:

        [lw $s*, 8+4*i($sp)]
        lw $fp, 0($sp)
        lw $ra, 4($sp)
        addiu $sp, $sp, frame_size

        (si exit_main) -> syscall exit
        (si no)        -> beq $ra, $zero, __cps_halt
                          nop
                          jr  $ra
    """
    if restore_s is None:
        restore_s = []

    lines: List[str] = []

    # Restaurar $s* primero, mientras $sp todavía apunta al inicio del frame
    if restore_s:
        off = 8
        for reg in restore_s:
            lines.append(f"  lw {reg}, {off}($sp)")
            off += 4

    # Restaurar old $fp y old $ra
    lines.append("  lw $fp, 0($sp)")
    lines.append("  lw $ra, 4($sp)")

    # Liberar frame
    lines.append(f"  addiu $sp, $sp, {frame_size}")

    if exit_main:
        # main: terminar el programa
        lines.append("  li $v0, 10")
        lines.append("  syscall")
    else:
        # IMPORTANTE: evitar saltar con jr $ra cuando $ra = 0
        # por el branch delay slot de MIPS/MARS.
        lines.append("  beq $ra, $zero, __cps_halt")
        lines.append("  nop")
        lines.append("  jr $ra")

    return lines


# =========================
#  PARAM COPY (homes)
# =========================
def emit_copy_params_to_homes(homes: List[int], frame_size: int) -> List[str]:
    """
    Copia parámetros desde $a0..$a3 a sus "homes" en el frame.

    `homes[i]` es el offset (relativo a $fp) donde debe quedar el parámetro i.
    Sólo se usan hasta 4 parámetros ($a0..$a3).

    Nota: frame_size se pasa solo por simetría, pero aquí no se usa.
    """
    lines: List[str] = []
    a_regs = ["$a0", "$a1", "$a2", "$a3"]

    for i, off in enumerate(homes):
        if i >= len(a_regs):
            break
        lines.append(f"  sw {a_regs[i]}, {off}($fp)")

    return lines


# =========================
#  Helpers varios
# =========================
def emit_move_args_to_a(arg_sources: Sequence[str]) -> Asm:
    if len(arg_sources) > len(ARG_REGS):
        raise ValueError("Este helper MVP solo soporta hasta 4 argumentos en registros")
    out: Asm = []
    for i, src in enumerate(arg_sources):
        out.append(f"  move {ARG_REGS[i]}, {src}")
    return out


def emit_jal(label: str) -> Asm:
    return [f"  jal {label}"]


Dest = Union[str, Tuple[str, int]]


def emit_move_v0_to(dest: Dest) -> Asm:
    if isinstance(dest, str):
        return [f"  move {dest}, {RET_REG}"]
    kind, off = dest
    if kind != "mem":
        raise ValueError("dest debe ser un registro (str) o ('mem', offset)")
    # offset aquí se asume NEGATIVO relativo a $fp si se usa como home
    return [f"  sw {RET_REG}, {off}({FP})"]


def asm_comment(out: Asm, text: str) -> None:
    out.append(f"  # {text}")


def asm_li(out: Asm, reg: str, imm) -> None:
    if isinstance(imm, bool):
        imm = 1 if imm else 0
    if imm is None:
        imm = 0
    out.append(f"  li {reg}, {imm}")


def asm_lw_fp(out: Asm, reg: str, offset: int) -> None:
    out.append(f"  lw {reg}, {_assert_neg(offset)}($fp)")


def asm_sw_fp(out: Asm, reg: str, offset: int) -> None:
    out.append(f"  sw {reg}, {_assert_neg(offset)}($fp)")
