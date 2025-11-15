# program/src/tests_mips/test_templates_basic.py
import re
from typing import List, Dict

from src.backend.mips.templates import emit_for_instr
from src.ir.model import (
    Temp, Name, Const, Label, LabelInstr, Goto, IfGoto,
    Assign, BinOp, Return
)

class FakeRegAlloc:
    """
    Stub minimal requerido por templates.emit_for_instr:
      - reg_for_read(op, out) -> str
      - reg_for_write(dst, out) -> str
      - store_if_name(dst, src_reg, out) -> None
    Reglas:
      - Const -> li en $t0 (o $t1 si ya se usó); aquí usamos $t0 siempre para simplificar.
      - Name con home -> lw en $t0 desde offset fijo (simulamos offset -8 para 'x', -12 para 'y').
      - Temp -> ya vive en $tX; devolvemos $t2 por convención en este stub.
    """
    def __init__(self, homes: Dict[str,int] | None = None):
        self.homes = homes or {}
        self.last_write = "$t2"

    def reg_for_read(self, op, out: List[str]) -> str:
        if isinstance(op, Const):
            v = op.value
            if isinstance(v, bool):
                v = 1 if v else 0
            if v is None:
                v = 0
            out.append(f"  li $t0, {v}")
            return "$t0"
        if isinstance(op, Name):
            off = self.homes.get(op.name, None)
            if off is not None:
                out.append(f"  lw $t0, {off}($fp)")
                return "$t0"
            # si no tiene home, lo tratamos como ya-en-reg para el test
            return "$t3"
        if isinstance(op, Temp):
            return "$t4"
        # fallback
        return "$t5"

    def reg_for_write(self, dst, out: List[str]) -> str:
        # Usamos $t2 como “destino” por convención
        self.last_write = "$t2"
        return "$t2"

    def store_if_name(self, dst, src_reg: str, out: List[str]) -> None:
        if isinstance(dst, Name):
            off = self.homes.get(dst.name, None)
            if off is not None:
                out.append(f"  sw {src_reg}, {off}($fp)")

def _asm_of(ins, homes=None, epilogue="Fn__epilogue"):
    out: List[str] = []
    ra = FakeRegAlloc(homes)
    emit_for_instr(ins, ra, out, epilogue_label=epilogue)
    return "\n".join(out)

def test_label_and_goto_and_ifgoto_const():
    L = Label("L1_then")
    a = [
        LabelInstr(L),
        Goto(L),
        IfGoto(Const(True), L),
        IfGoto(Const(False), L),
    ]
    out: List[str] = []
    ra = FakeRegAlloc()
    for ins in a:
        emit_for_instr(ins, ra, out, epilogue_label="EPI")
    txt = "\n".join(out)
    assert "L1_then:" in txt
    # Goto directo
    assert "  j L1_then" in txt
    # if true -> j L1_then
    assert re.search(r"\n\s*j L1_then", txt)
    # if false -> no emite salto extra (no debe haber dos saltos seguidos)
    assert txt.count("j L1_then") == 2

def test_assign_const_to_name_persists():
    x = Name("x")
    ins = Assign(dst=x, src=Const(7))
    txt = _asm_of(ins, homes={"x": -8})
    # li + move + store
    assert "  li $t0, 7" in txt
    assert "  move $t2, $t0" in txt
    assert "  sw $t2, -8($fp)" in txt

# program/src/tests_mips/test_template_basic.py
def test_binop_add_and_cmp():
    t0 = Temp("t0")
    ins1 = BinOp(dst=t0, op="+", left=Const(1), right=Const(2))
    txt1 = _asm_of(ins1)
    assert "  li $t0, 1" in txt1
    assert "  li $t0, 2" in txt1  # se vuelve a usar $t0 para el segundo const (stub simple)
    assert "  addu $t2, $t0, $t0" in txt1

    ins2 = BinOp(dst=t0, op="==", left=Const(3), right=Const(3))
    txt2 = _asm_of(ins2)
    # Acepta el patrón clásico (xor+sltiu) o la pseudo-instrucción MARS (seq)
    assert (
        "  xor $t2, $t0, $t0" in txt2
        or "  sltiu $t2," in txt2
        or "  seq $t2," in txt2
    )


def test_return_moves_to_v0_and_jumps_epilogue():
    ins = Return(value=Const(42))
    txt = _asm_of(ins, epilogue="Foo__epilogue")
    assert "  li $t0, 42" in txt
    assert "  move $v0, $t0" in txt
    assert "  j Foo__epilogue" in txt
