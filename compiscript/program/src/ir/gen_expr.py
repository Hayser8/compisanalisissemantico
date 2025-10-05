# program/src/ir/gen_expr.py
from __future__ import annotations
from typing import Tuple, Any

from .context import IRGenContext
from .model import (
    Operand, Temp, Name, Const, Label, LabelInstr,
    Assign, UnaryOp, BinOp, IfGoto, Goto, Return,
    Load, GetProp, NewObject, Call, Store  # <-- Store para inicializar arrays
)

# Mini-IR de expresiones (tuplas) aceptada por gen_expr:
# ('const', value)
# ('name', 'a')
# ('un', op, expr)                        # op in {'-', '!'}
# ('bin', op, left, right)                # op in {'+','-','*','/','%','==','!=','<','<=','>','>=','&&','||'}
# ('tern', cond, then_expr, else_expr)
# ('index', arr, idx)                     # lectura a[i] -> Load
# ('prop', obj, 'p')                      # lectura obj.p -> GetProp
# ('new', 'Clase', [args])                # construcción -> NewObject
# ('call', 'fn', [args])                  # llamada     -> Call
# ('array', [e1, e2, ...])                # literal de arreglo -> __new_array + Store

Expr = Tuple[Any, ...]


def _as_operand(node: Expr, ctx: IRGenContext) -> Operand:
    """Convierte directos a Operand sin emitir TAC: const y name."""
    tag = node[0]
    if tag == 'const':
        return Const(node[1])
    if tag == 'name':
        return Name(node[1])
    # Para otros, se delega a gen_expr (que emitirá TAC)
    return gen_expr(node, ctx)


def gen_expr(node: Expr, ctx: IRGenContext) -> Operand:
    """
    Genera TAC para 'node' y devuelve un Operand (Temp/Name/Const).
    Para const/names puede devolverlos directo; para operaciones,
    devuelve un Temp con el resultado.
    """
    tag = node[0]

    # Literales y nombres
    if tag == 'const':
        return Const(node[1])
    if tag == 'name':
        return Name(node[1])

    # Unarios: ('un', op, expr)
    if tag == 'un':
        _, op, sub = node
        v = _as_operand(sub, ctx)
        dst = ctx.temp_alloc.new_temp()
        ctx.emit(UnaryOp(dst=dst, op=op, value=v))
        return dst

    # Binarios: ('bin', op, l, r)
    if tag == 'bin':
        _, op, l, r = node
        lo = _as_operand(l, ctx)
        ro = _as_operand(r, ctx)
        dst = ctx.temp_alloc.new_temp()
        ctx.emit(BinOp(dst=dst, op=op, left=lo, right=ro))
        return dst

    # Ternario: ('tern', cond, t1, t2)
    if tag == 'tern':
        _, c, t1, t2 = node
        c_op = _as_operand(c, ctx)
        L_then = ctx.label_alloc.new_label("then")
        L_else = ctx.label_alloc.new_label("else")
        L_end  = ctx.label_alloc.new_label("end")
        dst = ctx.temp_alloc.new_temp()

        ctx.emit(IfGoto(cond=c_op, target=L_then))
        ctx.emit(Goto(target=L_else))

        ctx.emit(LabelInstr(L_then))
        v_then = _as_operand(t1, ctx)
        ctx.emit(Assign(dst=dst, src=v_then))
        ctx.emit(Goto(target=L_end))

        ctx.emit(LabelInstr(L_else))
        v_else = _as_operand(t2, ctx)
        ctx.emit(Assign(dst=dst, src=v_else))
        ctx.emit(Goto(target=L_end))

        ctx.emit(LabelInstr(L_end))
        return dst

    # Indexación de lectura: ('index', arr, idx) -> t = load arr[idx]
    if tag == 'index':
        _, arr, idx = node
        arr_o = _as_operand(arr, ctx)
        idx_o = _as_operand(idx, ctx)
        dst = ctx.temp_alloc.new_temp()
        ctx.emit(Load(dst=dst, array=arr_o, index=idx_o))
        return dst

    # Acceso a propiedad: ('prop', obj, 'p') -> t = get obj.p
    if tag == 'prop':
        _, obj, prop = node
        obj_o = _as_operand(obj, ctx)
        dst = ctx.temp_alloc.new_temp()
        ctx.emit(GetProp(dst=dst, obj=obj_o, prop=prop))
        return dst

    # new Clase(args): ('new', 'Clase', [args]) -> t = new Clase(args)
    if tag == 'new':
        _, cname, args = node
        args_o = [_as_operand(a, ctx) for a in args]
        dst = ctx.temp_alloc.new_temp()
        ctx.emit(NewObject(dst=dst, class_name=cname, args=args_o))
        return dst

    # Llamada: ('call', 'fn', [args]) -> t = call fn, args
    if tag == 'call':
        _, callee, args = node
        if not isinstance(callee, str):
            # De momento, sólo calls por nombre.
            raise ValueError("call con callee no-string aún no soportado")
        args_o = [_as_operand(a, ctx) for a in args]
        dst = ctx.temp_alloc.new_temp()
        ctx.emit(Call(dst=dst, func=callee, args=args_o))
        return dst

    # Literal de arreglo: ('array', [e1, e2, ...])
    if tag == 'array':
        _, elems = node
        n = len(elems)
        dst = ctx.temp_alloc.new_temp()
        # Crear arreglo de tamaño n
        ctx.emit(Call(dst=dst, func="__new_array", args=[Const(n)]))
        # Inicializar elementos
        for i, e in enumerate(elems):
            val = _as_operand(e, ctx)
            ctx.emit(Store(array=dst, index=Const(i), value=val))
        return dst

    raise ValueError(f"Expresión no soportada: {node!r}")
