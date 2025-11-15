# program/src/tests_mips/test_regalloc.py
import re
from typing import List
import pytest

from src.backend.mips.regalloc import RegAlloc
from src.backend.mips.frame_plan import FramePlan
from src.ir.model import Temp, Name, Const

def make_plan(*, params=None, locals_=None, need_param_homes=0, spill_bytes=0) -> FramePlan:
    params = params or []
    locals_ = locals_ or []
    fp = FramePlan(
        func_name="f",
        param_names=list(params),
        local_names=list(locals_),
        need_param_homes=need_param_homes,
        spill_bytes=spill_bytes,
    ).build()
    return fp

def test_round_robin_and_spill_slot_allocation():
    plan = make_plan(params=[], locals_=[], need_param_homes=0)
    ra = RegAlloc(plan)

    out: List[str] = []

    regs = []
    for i in range(12):
        t = Temp(f"t{i}")
        r, _ = ra.ensure_in_reg(t, out)
        regs.append((t, r))

    # primeros 10 deben usar 10 registros distintos $t*
    t_regs = [r for (_, r) in regs[:10]]
    assert len(set(t_regs)) == 10 and all(r.startswith("$t") for r in t_regs)

    # fuerza al menos un spill explícito
    ra.spill_if_needed(regs[10][0], out)
    assert any(re.search(r"^\s*sw\s+\$t\d,\s*-\d+\(\$fp\)", line) for line in out), \
        "Se esperaba al menos un store por spill"

def test_name_loads_from_home_slot():
    # 1 parámetro con home (-4), y 1 local 'x' debajo del home param -> offset de x es negativo menor (p.ej. -8)
    plan = make_plan(params=["p0"], locals_=["x"], need_param_homes=1)
    ra = RegAlloc(plan)
    out: List[str] = []

    expected_off = plan.offset_of_local("x")
    reg, _ = ra.ensure_in_reg(Name("x"), out)
    assert reg.startswith("$t")
    assert any("lw" in ln and f" {expected_off}($fp)" in ln for ln in out), \
        f"Debe cargar x desde su home {expected_off}($fp)"

def test_const_uses_li():
    plan = make_plan()
    ra = RegAlloc(plan)
    out: List[str] = []

    reg, _ = ra.ensure_in_reg(Const(42), out)
    assert any(re.match(r"\s*li\s+\$t\d,\s*42", ln) for ln in out), "Const debe cargar con li"

def test_store_to_home_for_assign_name():
    plan = make_plan(params=["a","b"], locals_=["y"], need_param_homes=2)
    ra = RegAlloc(plan)
    out: List[str] = []

    off = plan.offset_of_local("y")
    ra.store_to_home_if_name(Name("y"), "$t3", out)
    assert any(re.match(rf"\s*sw\s+\$t3,\s*{off}\(\$fp\)", ln) for ln in out), \
        f"Assign a Name debe hacer sw al home slot {off}($fp)"
