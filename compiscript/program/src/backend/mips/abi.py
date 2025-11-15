# program/src/mips/abi.py
from __future__ import annotations
from typing import List

# Registros por nombre (solo strings canónicos para emitir asm)
V0, V1 = "$v0", "$v1"
A0, A1, A2, A3 = "$a0", "$a1", "$a2", "$a3"
T0, T1, T2, T3, T4, T5, T6, T7, T8, T9 = (
    "$t0", "$t1", "$t2", "$t3", "$t4", "$t5", "$t6", "$t7", "$t8", "$t9"
)
S0, S1, S2, S3, S4, S5, S6, S7 = (
    "$s0", "$s1", "$s2", "$s3", "$s4", "$s5", "$s6", "$s7"
)
SP, FP, RA, ZERO = "$sp", "$fp", "$ra", "$zero"

# Convención
CALLER_SAVED: List[str] = [V0, V1, A0, A1, A2, A3, T0, T1, T2, T3, T4, T5, T6, T7, T8, T9]
CALLEE_SAVED: List[str] = [S0, S1, S2, S3, S4, S5, S6, S7, FP, RA]

ARG_REGS: List[str] = [A0, A1, A2, A3]
RET_REG: str = V0

def mangle_method_label(name: str) -> str:
    """
    Convierte 'Clase::metodo' en 'Clase__metodo'.
    Si no hay '::', retorna name intacto.
    """
    return name.replace("::", "__")
