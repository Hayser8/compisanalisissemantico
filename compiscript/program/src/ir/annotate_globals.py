# program/src/ir/annotate_globals.py
from __future__ import annotations
from typing import Dict, Set

from .model import (
    Program, Function, BasicBlock, Instr,
    Name, Temp, Const, Label,
    Assign, UnaryOp, BinOp, IfGoto, Goto, Return,
    Load, Store, GetProp, SetProp, NewObject, Call,
    MakeClosure, CallClosure,
)


def _iter_name_operands(instr: Instr):
    """
    Itera sobre TODOS los Operand que son Name dentro de una instrucción.
    Se usa para recolectar USOS (no distingue def vs use).
    """
    # LabelInstr no tiene operandos tipo Name

    if isinstance(instr, Assign):
        for op in (instr.dst, instr.src):
            if isinstance(op, Name):
                yield op

    elif isinstance(instr, UnaryOp):
        if isinstance(instr.dst, Name):
            yield instr.dst
        if isinstance(instr.value, Name):
            yield instr.value

    elif isinstance(instr, BinOp):
        for op in (instr.dst, instr.left, instr.right):
            if isinstance(op, Name):
                yield op

    elif isinstance(instr, IfGoto):
        if isinstance(instr.cond, Name):
            yield instr.cond

    elif isinstance(instr, Goto):
        # no operands
        pass

    elif isinstance(instr, Return):
        if instr.value is not None and isinstance(instr.value, Name):
            yield instr.value

    elif isinstance(instr, Load):
        if isinstance(instr.dst, Name):
            yield instr.dst
        if isinstance(instr.array, Name):
            yield instr.array
        if isinstance(instr.index, Name):
            yield instr.index

    elif isinstance(instr, Store):
        if isinstance(instr.array, Name):
            yield instr.array
        if isinstance(instr.index, Name):
            yield instr.index
        if isinstance(instr.value, Name):
            yield instr.value

    elif isinstance(instr, GetProp):
        if isinstance(instr.dst, Name):
            yield instr.dst
        if isinstance(instr.obj, Name):
            yield instr.obj

    elif isinstance(instr, SetProp):
        if isinstance(instr.obj, Name):
            yield instr.obj
        if isinstance(instr.value, Name):
            yield instr.value

    elif isinstance(instr, NewObject):
        if isinstance(instr.dst, Name):
            yield instr.dst
        for a in instr.args:
            if isinstance(a, Name):
                yield a

    elif isinstance(instr, Call):
        if instr.dst is not None and isinstance(instr.dst, Name):
            yield instr.dst
        for a in instr.args:
            if isinstance(a, Name):
                yield a

    elif isinstance(instr, MakeClosure):
        if isinstance(instr.dst, Name):
            yield instr.dst
        for c in instr.captures:
            if isinstance(c, Name):
                yield c

    elif isinstance(instr, CallClosure):
        if instr.dst is not None and isinstance(instr.dst, Name):
            yield instr.dst
        if isinstance(instr.closure, Name):
            yield instr.closure
        for a in instr.args:
            if isinstance(a, Name):
                yield a

    # Si más adelante agregas nuevas Instr, aquí se amplía.


def _collect_name_uses(prog: Program) -> Dict[str, Set[str]]:
    """
    Devuelve un dict: nombre -> {nombres_de_funciones_donde_aparece}
    (Solo consideramos Name, no Temps ni Consts).
    """
    uses: Dict[str, Set[str]] = {}
    for fn in prog.functions:
        for bb in fn.blocks:
            for instr in bb.instrs:
                for op in _iter_name_operands(instr):
                    uses.setdefault(op.name, set()).add(fn.name)
    return uses


def _iter_name_defs(instr: Instr):
    """
    Itera sobre los NOMBRES que aparecen en posición de "definición",
    es decir, donde la instrucción escribe en un Name (dst).
    Se usa para distinguir globales verdaderos de locales repetidos.
    """
    # Asumimos que solo ciertas instrucciones definen un Name (dst).
    if isinstance(instr, Assign):
        if isinstance(instr.dst, Name):
            yield instr.dst.name

    elif isinstance(instr, UnaryOp):
        if isinstance(instr.dst, Name):
            yield instr.dst.name

    elif isinstance(instr, BinOp):
        if isinstance(instr.dst, Name):
            yield instr.dst.name

    elif isinstance(instr, Load):
        if isinstance(instr.dst, Name):
            yield instr.dst.name

    elif isinstance(instr, GetProp):
        if isinstance(instr.dst, Name):
            yield instr.dst.name

    elif isinstance(instr, NewObject):
        if isinstance(instr.dst, Name):
            yield instr.dst.name

    elif isinstance(instr, Call):
        if instr.dst is not None and isinstance(instr.dst, Name):
            yield instr.dst.name

    elif isinstance(instr, MakeClosure):
        if isinstance(instr.dst, Name):
            yield instr.dst.name

    # Return, Store, SetProp, IfGoto, Goto, CallClosure, etc.
    # no definen directamente un Name nuevo.


def _collect_name_defs(prog: Program) -> Dict[str, Set[str]]:
    """
    Devuelve un dict: nombre -> {funciones_donde_se_define_como_dst}
    """
    defs: Dict[str, Set[str]] = {}
    for fn in prog.functions:
        for bb in fn.blocks:
            for instr in bb.instrs:
                for name in _iter_name_defs(instr):
                    defs.setdefault(name, set()).add(fn.name)
    return defs


def _rewrite_names_as_global(prog: Program, global_names: Set[str]) -> None:
    """
    Recorre todo el IR y reemplaza Name(...) por Name(..., is_global=True)
    cuando el nombre está en global_names.
    Como Name es frozen, creamos nuevos objetos Name y reescribimos las fields.
    """
    def maybe_global(op):
        if isinstance(op, Name) and op.name in global_names:
            return Name(name=op.name, type_hint=op.type_hint, is_global=True)
        return op

    for fn in prog.functions:
        for bb in fn.blocks:
            new_instrs = []
            for instr in bb.instrs:
                i = instr

                if isinstance(i, Assign):
                    i.dst = maybe_global(i.dst)
                    i.src = maybe_global(i.src)

                elif isinstance(i, UnaryOp):
                    i.dst = maybe_global(i.dst)
                    i.value = maybe_global(i.value)

                elif isinstance(i, BinOp):
                    i.dst = maybe_global(i.dst)
                    i.left = maybe_global(i.left)
                    i.right = maybe_global(i.right)

                elif isinstance(i, IfGoto):
                    i.cond = maybe_global(i.cond)

                elif isinstance(i, Return) and i.value is not None:
                    i.value = maybe_global(i.value)

                elif isinstance(i, Load):
                    i.dst = maybe_global(i.dst)
                    i.array = maybe_global(i.array)
                    i.index = maybe_global(i.index)

                elif isinstance(i, Store):
                    i.array = maybe_global(i.array)
                    i.index = maybe_global(i.index)
                    i.value = maybe_global(i.value)

                elif isinstance(i, GetProp):
                    i.dst = maybe_global(i.dst)
                    i.obj = maybe_global(i.obj)

                elif isinstance(i, SetProp):
                    i.obj = maybe_global(i.obj)
                    i.value = maybe_global(i.value)

                elif isinstance(i, NewObject):
                    i.dst = maybe_global(i.dst)
                    i.args = [maybe_global(a) for a in i.args]

                elif isinstance(i, Call):
                    if i.dst is not None:
                        i.dst = maybe_global(i.dst)
                    i.args = [maybe_global(a) for a in i.args]

                elif isinstance(i, MakeClosure):
                    i.dst = maybe_global(i.dst)
                    i.captures = [maybe_global(c) for c in i.captures]

                elif isinstance(i, CallClosure):
                    if i.dst is not None:
                        i.dst = maybe_global(i.dst)
                    i.closure = maybe_global(i.closure)
                    i.args = [maybe_global(a) for a in i.args]

                # LabelInstr y Goto no necesitan cambios

                new_instrs.append(i)
            bb.instrs = new_instrs


def annotate_globals(prog: Program) -> None:
    """
    Paso de post-proceso sobre el IR:

      1) Recolecta usos de Name en cada función.
      2) Recolecta "defs" (dónde se les asigna por primera vez).
      3) Decide qué nombres son globales.

    Heurística actual:
      - Nunca marcamos parámetros como globales.
      - Nunca marcamos "this" como global.
      - Un nombre es global si:
          * Se DEFINE (dst) solo en 'main'  (def_fns == {'main'})
          * Y se USA en más de una función. (len(uses[name]) > 1)

      Eso captura globals como 'a', 'xs', 'ys', 'd1', etc.:
        - Se asignan en main.
        - Se usan en otras funciones (runAll, pokeArray, sumWithLoops, ...).
      Y evita falsos positivos como 'i', 's', 'this', etc.
    """
    uses = _collect_name_uses(prog)
    defs = _collect_name_defs(prog)

    # Conjunto de todos los parámetros (para NO marcarlos como globales)
    param_names: Set[str] = set()
    for fn in prog.functions:
        param_names.update(fn.params)

    global_names: Set[str] = set()

    for name, fnset in uses.items():
        # 1) Nunca global si es parámetro
        if name in param_names:
            continue

        # 2) Nunca global para "this" (es implícito de métodos)
        if name == "this":
            continue

        def_fns = defs.get(name, set())

        # 3) Global si:
        #    - Solo se define en 'main'
        #    - Y aparece en MÁS de una función
        if def_fns == {"main"} and len(fnset) > 1:
            global_names.add(name)

    # Guardar en el Program (útil si lo quieres inspeccionar después)
    prog.global_vars = global_names

    # Reescribir Name(...) como global donde aplique
    _rewrite_names_as_global(prog, global_names)
