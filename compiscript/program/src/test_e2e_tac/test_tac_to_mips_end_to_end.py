import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # -> /program
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ir.model import (
    Program,
    Function,
    BasicBlock,
    Label,
    LabelInstr,
    Assign,
    BinOp,
    Return,
    Call,
    Load,
    Store,
    Name,
    Const,
)
from src.backend.mips.frame_plan import FramePlan
from src.backend.mips.objects import LayoutRegistry
from src.backend.mips.validate import validate_program
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.runner import run_asm, have_any_sim



# ---------- Helpers para inferir locals y armar FramePlan ----------

def _collect_names_from_obj(obj, acc: set):
    """Busca src.ir.model.Name recursivamente y mete sus .name en acc."""
    from src.ir.model import Name

    if isinstance(obj, Name):
        acc.add(obj.name)
        return
    if isinstance(obj, (list, tuple)):
        for x in obj:
            _collect_names_from_obj(x, acc)
        return
    # Para instrucciones, miramos sus atributos
    if hasattr(obj, "__dict__"):
        for v in obj.__dict__.values():
            _collect_names_from_obj(v, acc)


def infer_locals(fn: Function) -> list[str]:
    """Inferir nombres locales de la función (Names que no son parámetros)."""
    from src.ir.model import Name

    param_names = [getattr(p, "name", "") for p in fn.params]
    used: set[str] = set()

    for bb in fn.blocks:
        for ins in bb.instrs:
            _collect_names_from_obj(ins, used)

    return sorted(n for n in used if n and n not in param_names)


def plan_for_fn(fn: Function) -> FramePlan:
    """
    FramePlan genérico:
      - param_names: nombres de parámetros (por si algún día tienes params)
      - local_names: todos los Name usados en la función menos los params
      - need_param_homes: todos los params reciben home en el frame
    """
    param_names = [getattr(p, "name", "") for p in fn.params]
    local_names = infer_locals(fn)

    plan = FramePlan(
        func_name=fn.name,
        param_names=param_names,
        local_names=local_names,
        need_param_homes=len(param_names),
    )
    plan.build()
    return plan


# ---------- Dummies para pool y globales (no usamos strings/globales aquí) ----------

class DummyPool:
    """Objeto vacío: emit_full_program lo acepta sin problemas mientras no haya strings."""
    pass


class DummyGlobals:
    """Sin globales por ahora."""
    pass


# ---------- Test principal ----------

def test_tac_to_mips_end_to_end_simple_program():
    """
    Programa en IR que hace:

        x = 10
        y = 32
        sum = x + y       # 42
        __print_int(sum)

        arr = __new_array(2)
        arr[0] = sum      # 42
        arr[1] = 5
        t0 = arr[0]
        t1 = arr[1]
        res2 = t0 + t1    # 47
        __print_int(res2)

    Esperamos que el MIPS imprima algo que contenga "42" y "47".
    """

    if not have_any_sim():
        pytest.skip("Se necesita MARS_JAR o spim/qtspim instalado para este test")

    # ----- Construir IR de main -----
    l0 = Label("L0")

    instrs = [
        LabelInstr(label=l0),

        # x = 10
        Assign(dst=Name("x"), src=Const(10)),

        # y = 32
        Assign(dst=Name("y"), src=Const(32)),

        # sum = x + y
        BinOp(dst=Name("sum"), op="+", left=Name("x"), right=Name("y")),

        # __print_int(sum)
        Call(dst=None, func="__print_int", args=[Name("sum")]),

        # arr = __new_array(2)
        Call(dst=Name("arr"), func="__new_array", args=[Const(2)]),

        # arr[0] = sum
        Store(array=Name("arr"), index=Const(0), value=Name("sum")),

        # arr[1] = 5
        Store(array=Name("arr"), index=Const(1), value=Const(5)),

        # t0 = arr[0]
        Load(dst=Name("t0"), array=Name("arr"), index=Const(0)),

        # t1 = arr[1]
        Load(dst=Name("t1"), array=Name("arr"), index=Const(1)),

        # res2 = t0 + t1
        BinOp(dst=Name("res2"), op="+", left=Name("t0"), right=Name("t1")),

        # __print_int(res2)
        Call(dst=None, func="__print_int", args=[Name("res2")]),

        # return;
        Return(value=None),
    ]

    main_block = BasicBlock(label=l0, instrs=instrs)

    main_fn = Function(
        name="main",
        params=[],
        blocks=[main_block],
    )

    prog = Program(functions=[main_fn])

    # ----- Validar TAC -----
    validate_program(prog)

    # ----- Emitir ASM completo -----
    pool = DummyPool()
    gtab = DummyGlobals()
    layouts = LayoutRegistry()

    asm = emit_full_program(
        prog,
        pool=pool,
        gtab=gtab,
        plan_for_fn=plan_for_fn,
        layouts=layouts,
    )

    # ----- Ejecutar en MARS / SPIM -----
    rc, out, err = run_asm(asm)

    # Queremos que el programa termine bien
    assert rc == 0, f"Simulador devolvió código {rc}. stderr:\n{err}"

    # Y que en stdout se vean 42 y 47 en algún lado
    assert "42" in out, f"No se encontró '42' en la salida:\n{out}"
    assert "47" in out, f"No se encontró '47' en la salida:\n{out}"
