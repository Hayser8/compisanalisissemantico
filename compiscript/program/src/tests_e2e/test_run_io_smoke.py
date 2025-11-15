# src/tests_e2e/test_run_io_smoke.py
from __future__ import annotations
import os, glob, subprocess, tempfile, pytest

from src.ir.model import Program, Function, BasicBlock, Temp, Assign, Call, Return, Const
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.string_pool import StringPool
from src.backend.mips.globals_table import GlobalsTable
from src.backend.mips.objects import LayoutRegistry
from src.backend.mips.frame_plan import FramePlan


def _plan(fn_name: str = "main"):
    return FramePlan(func_name=fn_name, param_names=[], local_names=[], need_param_homes=0).build()


def _find_mars_jar() -> str | None:
    # 1) variable de entorno
    env = os.getenv("MARS_JAR")
    if env and os.path.exists(env):
        return env

    # 2) buscar en src/tools relativo a este archivo
    here = os.path.dirname(__file__)                  # .../program/src/tests_e2e
    src_root = os.path.abspath(os.path.join(here, ".."))  # .../program/src
    tools = os.path.join(src_root, "tools")

    candidates = [
        os.path.join(tools, "MARS.jar"),
        os.path.join(tools, "Mars.jar"),
        os.path.join(tools, "Mars4_5.jar"),
    ]
    candidates.extend(sorted(glob.glob(os.path.join(tools, "Mars*.jar"))))

    for c in candidates:
        if os.path.exists(c):
            return c
    return None


MARS_JAR = _find_mars_jar()
SIM_AVAILABLE = bool(MARS_JAR)


@pytest.mark.skipif(not SIM_AVAILABLE, reason="Requiere MARS_JAR o un Mars*.jar en src/tools/")
def test_io_smoke_print_and_exit():
    # Programa: t0 = 42; print_int(t0); exit()
    prog = Program()
    fn = Function("main", [])
    bb = BasicBlock("L0")
    t0 = Temp("t0")
    bb.add(Assign(dst=t0, src=Const(42)))
    bb.add(Call(dst=None, func="__print_int", args=[t0]))
    bb.add(Call(dst=None, func="__exit", args=[]))
    fn.blocks.append(bb)
    prog.functions.append(fn)

    asm = emit_full_program(
        prog,
        pool=StringPool(),
        gtab=GlobalsTable(),
        plan_for_fn=lambda f: _plan(f.name),
        layouts=LayoutRegistry(),
    )

    with tempfile.NamedTemporaryFile("w", suffix=".asm", delete=False) as f:
        f.write(asm)
        asm_path = f.name

    # Ejecutar MARS en modo headless: nc (no gui) + sm (run main)
    cmd = ["java", "-jar", MARS_JAR, "nc", "sm", asm_path]
    p = subprocess.run(cmd, capture_output=True, text=True)

    # Debe imprimir 42 (sin necesidad de newline)
    assert "42" in p.stdout
