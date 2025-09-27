from __future__ import annotations
from typing import Tuple, Union, Any

from .context import IRGenContext
from .model import (
    Operand, Temp, Name, Const, Label, LabelInstr,
    Assign, UnaryOp, BinOp, IfGoto, Goto, Return  # Return no se usa aquí, pero útil
)

# Mini-IR de expresiones (tuplas) aceptada por gen_expr:
# ('const', value)
# ('name', 'a')
# ('un', op, expr)                        # op in {'-', '!'}
# ('bin', op, left, right)                # op in {'+','-','*','/','%','==','!=','<','<=','>','>=','&&','||'}
# ('tern', cond, then_expr, else_expr)


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
        # Evaluar condición
        c_op = _as_operand(c, ctx)
        # Labels
        L_then = ctx.label_alloc.new_label("then")
        L_else = ctx.label_alloc.new_label("else")
        L_end  = ctx.label_alloc.new_label("end")
        # Resultado en un temp
        dst = ctx.temp_alloc.new_temp()

        # if cond goto then; else → goto L_else
        ctx.emit(IfGoto(cond=c_op, target=L_then))
        ctx.emit(Goto(target=L_else))

        # THEN
        ctx.emit(LabelInstr(L_then))
        v_then = _as_operand(t1, ctx)
        ctx.emit(Assign(dst=dst, src=v_then))
        ctx.emit(Goto(target=L_end))

        # ELSE
        ctx.emit(LabelInstr(L_else))
        v_else = _as_operand(t2, ctx)
        ctx.emit(Assign(dst=dst, src=v_else))
        ctx.emit(Goto(target=L_end))

        # END
        ctx.emit(LabelInstr(L_end))
        return dst

    raise ValueError(f"Expresión no soportada: {node!r}")
