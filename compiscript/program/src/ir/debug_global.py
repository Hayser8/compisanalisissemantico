# program/src/ir/debug_globals.py
from __future__ import annotations
from typing import Iterable, Any

from .model import Program, Name, Operand


def _iter_names(obj: Any) -> Iterable[Name]:
    """
    Recorre recursivamente un objeto y produce todos los Name que encuentre.
    Soporta:
      - Name directamente
      - listas/tuplas de cosas
    """
    if isinstance(obj, Name):
        yield obj
    elif isinstance(obj, (list, tuple)):
        for x in obj:
            yield from _iter_names(x)
    # Para otros tipos no hacemos nada


def debug_dump_globals(program: Program) -> None:
    """
    Imprime, por función, todos los Name que aparecen en las instrucciones
    y muestra su flag is_global (si existe).
    """
    print("\n===== DEBUG: Name.is_global por función =====")
    for fn in program.functions:
        print(f"\nFunction {fn.name}:")
        seen = set()
        for bb in fn.blocks:
            for instr in bb.instrs:
                for field_name, field_value in vars(instr).items():
                    for name_op in _iter_names(field_value):
                        key = (name_op.name, field_name)
                        if key in seen:
                            continue
                        seen.add(key)
                        is_glob = getattr(name_op, "is_global", False)
                        print(f"  {name_op.name:10s} (campo {field_name:8s})  is_global={is_glob}")
    print("===== FIN DEBUG GLOBALS =====\n")
