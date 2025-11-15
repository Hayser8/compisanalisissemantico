# -*- coding: utf-8 -*-
from __future__ import annotations
import os, re, tempfile, subprocess
from typing import Optional, Set, Iterable
import pytest

# Reusar el buscador del jar que ya tienes
try:
    from src.tools.mars_run import find_mars_jar  # ya validado en tu smoke
except Exception:
    find_mars_jar = None

def _find_mars_or_skip() -> str:
    jar = None
    if find_mars_jar is not None:
        jar = find_mars_jar()
    if not jar:
        env = os.environ.get("MARS_JAR")
        if env and os.path.exists(env):
            jar = env
    if not jar:
        pytest.skip("MARS jar not found; set $MARS_JAR or place Mars*.jar in src/tools")
    return jar

def run_in_mars(asm_text: str, stdin: Optional[str] = None) -> str:
    """Ensambla y ejecuta en MARS sin GUI, devolviendo stdout+stderr."""
    mars_jar = _find_mars_or_skip()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
        f.write(asm_text)
        asm_path = f.name
    proc = subprocess.run(
        ["java", "-jar", mars_jar, "nc", "sm", asm_path],
        input=stdin, text=True, capture_output=True
    )
    return (proc.stdout or "") + "\n" + (proc.stderr or "")

def last_int(stdout: str) -> int:
    m = list(re.finditer(r"(-?\d+)", stdout))
    if not m:
        raise AssertionError(f"No integer found in MARS output.\n---\n{stdout}\n---")
    return int(m[-1].group(1))

def pools_and_gtab():
    """Devuelve (pool, gtab) apuntando a tus módulos reales; si no hay gtab, usa stub."""
    from src.backend.mips.string_pool import StringPool
    try:
        from src.backend.mips.globals_table import GlobalsTable  # ruta real en tu árbol
        gtab = GlobalsTable()
    except Exception:
        class _GlobalsTable(dict):
            pass
        gtab = _GlobalsTable()
    return StringPool(), gtab

# =========================
#  Planner mínimo para tests
# =========================
# Requisitos que espera el emitter:
#   - plan.frame_size               (int > 0, múltiplo de 4)
#   - plan.local_off: dict[str,int] (offsets NEGATIVOS)
#   - plan.param_home_off: dict[int,int]  (offsets NEGATIVOS indexados 0..n-1)
#   - plan.need_param_homes: int
#   - plan.param_names: list[str]

def _collect_local_names(fn) -> Set[str]:
    """Escanea la IR para encontrar Names distintos a los parámetros (locals)."""
    from src.ir.model import Name
    params = set(fn.params)
    locals_: Set[str] = set()
    for bb in getattr(fn, "blocks", []):
        for ins in getattr(bb, "instrs", []):
            for attr in ("dst", "src", "left", "right", "cond"):
                val = getattr(ins, attr, None)
                if isinstance(val, Name) and val.name not in params:
                    locals_.add(val.name)
            # campos tipo lista (args de Call, etc.)
            args = getattr(ins, "args", None)
            if isinstance(args, Iterable):
                for a in args:
                    if isinstance(a, Name) and a.name not in params:
                        locals_.add(a.name)
    # No incluimos parámetros
    locals_ -= params
    return locals_

class _MiniPlan:
    def __init__(self, fn):
        # nombres de parámetros
        self.param_names = list(fn.params)
        self.need_param_homes = len(self.param_names)

        # homes de parámetros: -4, -8, ..., -4*n
        self.param_home_off = {i: -4 * (i + 1) for i in range(self.need_param_homes)}

        # locales (Names que no son params)
        self.local_off = {}
        locs = sorted(_collect_local_names(fn))
        # ubica locales a continuación de los homes de params
        for j, nm in enumerate(locs):
            self.local_off[nm] = -4 * (self.need_param_homes + j + 1)

        # cálculo de frame:
        #   payload = 4 * (#params + #locals)
        #   frame   = 8 (fp, ra) + payload redondeado a múltiplo de 8
        payload_slots = self.need_param_homes + len(self.local_off)
        payload_bytes = 4 * payload_slots
        # redondeo a 8 para evitar caer justo en 0($sp) o 4($sp) con s-regs
        rounded_payload = ((payload_bytes + 7) // 8) * 8
        self.frame_size = 8 + rounded_payload
        if self.frame_size <= 0 or self.frame_size % 4 != 0:
            # fallback ultra conservador
            self.frame_size = 8

def _plan_for(fn):
    """Plan sencillo pero suficiente para las pruebas de integración."""
    try:
        # Si tu implementación real existe, úsala
        from src.backend.mips.frame_plan import plan_for_function as _real
        return _real(fn)
    except Exception:
        return _MiniPlan(fn)
