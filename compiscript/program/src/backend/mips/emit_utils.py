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
    Prólogo estándar.

    Convención coherente con FramePlan:

      - FramePlan.frame_size = 8 (old $fp/$ra) + zona negativa (params, locals, spills).
      - Aquí se puede pasar una lista de $s* a guardar (save_s).
      - Este helper RESERVA espacio extra para los $s* sin tocar los offsets
        negativos de homes/locals/spills.

    Layout final en memoria (tras el prólogo):

        # frame_size proviene de FramePlan (8 + negativos)
        extra_s = 4 * len(save_s)
        full_frame = frame_size + extra_s

        SP_new = SP_old - full_frame
        FP     = SP_old

        En offsets relativos a $fp:

        -full_frame($fp)      : old $fp
        -full_frame+4($fp)    : old $ra
        -full_frame+8($fp)... : $s0, $s1, ...
        ...
        -8($fp)               : último home/local/spill
        -4($fp)               : primer home/local/spill

    Es decir:
      - Los homes/locals/spills siguen en offsets NEGATIVOS cerca de 0.
      - Los registros salvados viven MÁS ABAJO, en offsets más negativos.
    """
    if frame_size <= 0 or frame_size % WORD != 0:
        raise ValueError("frame_size debe ser múltiplo de 4 y > 0")

    save_s = save_s or []
    extra_s = WORD * len(save_s)
    full_frame = frame_size + extra_s

    lines: List[str] = []

    # Reservar todo el frame (negativos + old fp/ra + s-regs)
    lines.append(f"  addiu $sp, $sp, -{full_frame}")

    # Guardar old $fp y old $ra en la base del frame (relativo a $sp)
    lines.append("  sw $fp, 0($sp)")
    lines.append("  sw $ra, 4($sp)")

    # Guardar $s* inmediatamente después
    for i, reg in enumerate(save_s):
        off = 8 + WORD * i
        lines.append(f"  sw {reg}, {off}($sp)")

    # Colocar $fp al tope del frame (SP_old)
    lines.append(f"  addiu $fp, $sp, {full_frame}")
    return lines


def emit_epilogue(
    frame_size: int,
    restore_s: List[str] | None = None,
    *,
    exit_main: bool = False,
) -> List[str]:
    """
    Epílogo simétrico a emit_prologue:

      - Restaura $s* (si los hubiera).
      - Restaura $fp y $ra.
      - Libera todo el frame (incluyendo espacio extra de $s*).
      - Si exit_main=True → termina el programa.
      - Si exit_main=False → vuelve por $ra; si $ra==0 → salta a __cps_halt.
    """
    if frame_size <= 0 or frame_size % WORD != 0:
        raise ValueError("frame_size debe ser múltiplo de 4 y > 0")

    restore_s = restore_s or []
    extra_s = WORD * len(restore_s)
    full_frame = frame_size + extra_s

    lines: List[str] = []

    # Restaurar $s* (en el mismo orden y offsets que en el prólogo)
    for i, reg in enumerate(restore_s):
        off = 8 + WORD * i
        lines.append(f"  lw {reg}, {off}($sp)")

    # Restaurar $fp y $ra
    lines.append("  lw $fp, 0($sp)")
    lines.append("  lw $ra, 4($sp)")

    # Liberar TODO el frame
    lines.append(f"  addiu $sp, $sp, {full_frame}")

    if exit_main:
        # Solo main hace exit del programa
        lines.append("  li $v0, 10")
        lines.append("  syscall")
    else:
        # Cualquier otra función: si $ra==0, no saltar a 0x0
        lines.append("  beq $ra, $zero, __cps_halt")
        lines.append("  jr $ra")

    return lines


# =========================
#  PARAM COPY (homes)
# =========================
def emit_copy_params_to_homes(homes: list[int], frame_size: int) -> List[str]:
    """
    Copia parámetros desde $a0..$a3 a sus 'homes' en el frame.

    homes[i] es offset (NEGATIVO) relativo a $fp donde va el parámetro i.

    Se usa después del prólogo, cuando $fp ya apunta al tope del frame y
    la zona negativa está completamente reservada.
    """
    lines: List[str] = []

    upto = min(len(homes), 4)
    for i in range(upto):
        off = _assert_neg(homes[i])
        lines.append(f"  sw $a{i}, {off}($fp)")

    # Parámetros extra (i>=4) irían en stack del caller, no se copian aquí.
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
