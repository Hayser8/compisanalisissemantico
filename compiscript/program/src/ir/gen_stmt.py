# program/src/ir/gen_stmt.py
from __future__ import annotations
from typing import List, Optional, Tuple, Any

from .context import IRGenContext
from .model import (
    Label, LabelInstr, Goto, IfGoto, Return, Assign, BinOp, Const, Name, Temp,
    Store, SetProp
)
from .gen_expr import gen_expr, _as_operand

# formas aceptadas:
# block, expr, assign (name|index|prop), vardecl, constdecl,
# return, if, while, do_while, for, break, continue, switch
Stmt = Tuple[Any, ...]


def gen_block(stmts: List[Stmt], ctx: IRGenContext) -> None:
    for s in stmts:
        gen_stmt(s, ctx)


def gen_stmt(node: Stmt, ctx: IRGenContext) -> None:
    tag = node[0]

    if tag == 'block':
        _, lst = node
        gen_block(lst, ctx)
        return

    if tag == 'expr':
        _, expr = node
        _ = gen_expr(expr, ctx)
        return

    if tag == 'assign':
        _, target, expr = node
        val = _as_operand(expr, ctx)

        if target[0] == 'name':
            ctx.emit(Assign(dst=Name(target[1]), src=val))
            return

        if target[0] == 'index':
            _, arr, idx = target
            arr_o = _as_operand(arr, ctx)
            idx_o = _as_operand(idx, ctx)
            ctx.emit(Store(array=arr_o, index=idx_o, value=val))
            return

        if target[0] == 'prop':
            _, obj, prop = target
            obj_o = _as_operand(obj, ctx)
            ctx.emit(SetProp(obj=obj_o, prop=prop, value=val))
            return

        raise ValueError(f"assign target no soportado: {target!r}")

    if tag in ('vardecl', 'constdecl'):
        _, name, init = node
        if init is not None:
            gen_stmt(('assign', ('name', name), init), ctx)
        return

    if tag == 'return':
        if len(node) == 1:
            ctx.emit(Return())
        else:
            _, expr = node
            val = _as_operand(expr, ctx)
            ctx.emit(Return(val))
        return

    if tag == 'if':
        _, cond, then_blk, else_blk = node
        c = _as_operand(cond, ctx)
        L_then = ctx.label_alloc.new_label("then")
        L_else = ctx.label_alloc.new_label("else") if else_blk is not None else ctx.label_alloc.new_label("end")
        L_end  = L_else if else_blk is None else ctx.label_alloc.new_label("end")

        ctx.emit(IfGoto(cond=c, target=L_then))
        ctx.emit(Goto(L_else))

        ctx.emit(LabelInstr(L_then))
        gen_stmt(then_blk, ctx)
        ctx.emit(Goto(L_end))

        if else_blk is not None:
            ctx.emit(LabelInstr(L_else))
            gen_stmt(else_blk, ctx)
            ctx.emit(Goto(L_end))

        ctx.emit(LabelInstr(L_end))
        return

    if tag == 'while':
        _, cond, body = node
        L_head = ctx.label_alloc.new_label("while_head")
        L_body = ctx.label_alloc.new_label("while_body")
        L_end  = ctx.label_alloc.new_label("while_end")

        ctx.emit(Goto(L_head))
        ctx.emit(LabelInstr(L_head))
        c = _as_operand(cond, ctx)
        ctx.emit(IfGoto(c, L_body))
        ctx.emit(Goto(L_end))

        ctx.push_loop(label_break=L_end, label_continue=L_head)
        ctx.emit(LabelInstr(L_body))
        gen_stmt(body, ctx)
        ctx.emit(Goto(L_head))
        ctx.pop_loop()

        ctx.emit(LabelInstr(L_end))
        return

    if tag == 'do_while':
        _, body, cond = node
        L_body = ctx.label_alloc.new_label("do_body")
        L_head = ctx.label_alloc.new_label("do_head")
        L_end  = ctx.label_alloc.new_label("do_end")

        ctx.emit(LabelInstr(L_body))
        ctx.push_loop(label_break=L_end, label_continue=L_head)
        gen_stmt(body, ctx)
        ctx.pop_loop()

        ctx.emit(LabelInstr(L_head))
        c = _as_operand(cond, ctx)
        ctx.emit(IfGoto(c, L_body))
        ctx.emit(Goto(L_end))
        ctx.emit(LabelInstr(L_end))
        return

    if tag == 'for':
        _, init, cond, step, body = node
        if init is not None:
            gen_stmt(init, ctx)

        L_head = ctx.label_alloc.new_label("for_head")
        L_body = ctx.label_alloc.new_label("for_body")
        L_step = ctx.label_alloc.new_label("for_step")
        L_end  = ctx.label_alloc.new_label("for_end")

        ctx.emit(Goto(L_head))
        ctx.emit(LabelInstr(L_head))
        if cond is not None:
            c = _as_operand(cond, ctx)
            ctx.emit(IfGoto(c, L_body))
            ctx.emit(Goto(L_end))
        else:
            ctx.emit(Goto(L_body))

        ctx.push_loop(label_break=L_end, label_continue=L_step)
        ctx.emit(LabelInstr(L_body))
        gen_stmt(body, ctx)
        ctx.emit(Goto(L_step))
        ctx.pop_loop()

        ctx.emit(LabelInstr(L_step))
        if step is not None:
            gen_stmt(step, ctx)
        ctx.emit(Goto(L_head))

        ctx.emit(LabelInstr(L_end))
        return

    if tag == 'break':
        L = ctx.current_break_label()
        ctx.emit(Goto(L))
        return

    if tag == 'continue':
        L = ctx.current_continue_label()
        ctx.emit(Goto(L))
        return

    if tag == 'switch':
        _, cond, cases, default_blk = node
        c = _as_operand(cond, ctx)

        case_labels: List[Tuple[Label, Any]] = []
        for (case_expr, case_blk) in cases:
            lab = ctx.label_alloc.new_label("case")
            case_labels.append((lab, (case_expr, case_blk)))

        has_default = default_blk is not None
        L_default = ctx.label_alloc.new_label("switch_default") if has_default else None
        L_end = ctx.label_alloc.new_label("switch_end")

        for lab, (case_expr, _) in case_labels:
            cv = _as_operand(case_expr, ctx)
            t = ctx.temp_alloc.new_temp()
            ctx.emit(BinOp(dst=t, op="==", left=c, right=cv))
            ctx.emit(IfGoto(cond=t, target=lab))

        ctx.emit(Goto(L_default if has_default else L_end))

        for lab, (_, case_blk) in case_labels:
            ctx.emit(LabelInstr(lab))
            gen_stmt(case_blk, ctx)
            ctx.emit(Goto(L_end))

        if has_default:
            ctx.emit(LabelInstr(L_default))
            gen_stmt(default_blk, ctx)
            ctx.emit(Goto(L_end))

        ctx.emit(LabelInstr(L_end))
        return

    raise ValueError(f"Sentencia no soportada: {node!r}")
