from __future__ import annotations
from typing import List, Optional, Tuple, Any

from .context import IRGenContext
from .model import (
    Label, LabelInstr, Goto, IfGoto, Return, Assign, BinOp, Const, Name, Temp
)
from .gen_expr import gen_expr, _as_operand


# Mini-IR de sentencias:
# ('block', [stmt, ...])
# ('expr', expr)
# ('return',)                    -> return
# ('return', expr)               -> return expr
# ('if', cond, then_block, else_block_or_None)
# ('while', cond, body_block)
# ('do_while', body_block, cond)
# ('for', init_or_None, cond_or_None, step_or_None, body_block)  # init y step pueden ser ('expr', expr)
# ('break',)
# ('continue',)
# ('switch', cond, [(expr, block), ...], default_block_or_None)  # sin fallthrough: cada case salta a END


Stmt = Tuple[Any, ...]


def gen_block(stmts: List[Stmt], ctx: IRGenContext) -> None:
    for s in stmts:
        gen_stmt(s, ctx)


def gen_stmt(node: Stmt, ctx: IRGenContext) -> None:
    tag = node[0]

    # Bloque
    if tag == 'block':
        _, lst = node
        gen_block(lst, ctx)
        return

    # Expresión como statement
    if tag == 'expr':
        _, expr = node
        _ = gen_expr(expr, ctx)  # el resultado se ignora
        return

    # Return
    if tag == 'return':
        if len(node) == 1:
            ctx.emit(Return())
        else:
            _, expr = node
            val = _as_operand(expr, ctx)
            ctx.emit(Return(val))
        return

    # If / else
    if tag == 'if':
        _, cond, then_blk, else_blk = node
        c = _as_operand(cond, ctx)
        L_then = ctx.label_alloc.new_label("then")
        L_else = ctx.label_alloc.new_label("else") if else_blk is not None else ctx.label_alloc.new_label("end")
        L_end  = L_else if else_blk is None else ctx.label_alloc.new_label("end")

        ctx.emit(IfGoto(cond=c, target=L_then))
        ctx.emit(Goto(L_else))

        # then:
        ctx.emit(LabelInstr(L_then))
        gen_stmt(then_blk, ctx)
        ctx.emit(Goto(L_end))

        # else:
        if else_blk is not None:
            ctx.emit(LabelInstr(L_else))
            gen_stmt(else_blk, ctx)
            ctx.emit(Goto(L_end))

        # end
        ctx.emit(LabelInstr(L_end))
        return

    # While
    if tag == 'while':
        _, cond, body = node
        L_head = ctx.label_alloc.new_label("while_head")
        L_body = ctx.label_alloc.new_label("while_body")
        L_end  = ctx.label_alloc.new_label("while_end")

        ctx.emit(Goto(L_head))             # entrar al head
        ctx.emit(LabelInstr(L_head))       # head:
        c = _as_operand(cond, ctx)
        ctx.emit(IfGoto(c, L_body))        # if cond goto body
        ctx.emit(Goto(L_end))              # else goto end

        # cuerpo (break → end, continue → head)
        ctx.push_loop(label_break=L_end, label_continue=L_head)
        ctx.emit(LabelInstr(L_body))       # body:
        gen_stmt(body, ctx)
        ctx.emit(Goto(L_head))             # fin de iteración → head
        ctx.pop_loop()

        ctx.emit(LabelInstr(L_end))        # end:
        return

    # Do-while
    if tag == 'do_while':
        _, body, cond = node
        L_body = ctx.label_alloc.new_label("do_body")
        L_head = ctx.label_alloc.new_label("do_head")  # punto de reevaluar condición (mismo que body fin)
        L_end  = ctx.label_alloc.new_label("do_end")

        ctx.emit(LabelInstr(L_body))       # first body (al menos una vez)
        ctx.push_loop(label_break=L_end, label_continue=L_head)
        gen_stmt(body, ctx)
        ctx.pop_loop()

        # continue salta a L_head:
        ctx.emit(LabelInstr(L_head))
        c = _as_operand(cond, ctx)
        ctx.emit(IfGoto(c, L_body))        # if cond → repetir
        ctx.emit(Goto(L_end))              # else → salir
        ctx.emit(LabelInstr(L_end))
        return

    # For (clásico)
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
            # sin condición => infinito; salta directo al body
            ctx.emit(Goto(L_body))

        # cuerpo
        ctx.push_loop(label_break=L_end, label_continue=L_step)
        ctx.emit(LabelInstr(L_body))
        gen_stmt(body, ctx)
        ctx.emit(Goto(L_step))
        ctx.pop_loop()

        # step
        ctx.emit(LabelInstr(L_step))
        if step is not None:
            gen_stmt(step, ctx)
        ctx.emit(Goto(L_head))

        # end
        ctx.emit(LabelInstr(L_end))
        return

    # break
    if tag == 'break':
        L = ctx.current_break_label()
        ctx.emit(Goto(L))
        return

    # continue
    if tag == 'continue':
        L = ctx.current_continue_label()
        ctx.emit(Goto(L))
        return

    # switch (sin fallthrough; soporta boolean/string/num comparables con ==)
    if tag == 'switch':
        _, cond, cases, default_blk = node
        c = _as_operand(cond, ctx)

        # 1) Primero crear labels de los CASES en orden (para que queden L1_case, L2_case, ...)
        case_labels: List[Tuple[Label, Any]] = []
        for (case_expr, case_blk) in cases:
            lab = ctx.label_alloc.new_label("case")
            case_labels.append((lab, (case_expr, case_blk)))

        # 2) Luego (si existe) el DEFAULT y por último el END
        has_default = default_blk is not None
        L_default = ctx.label_alloc.new_label("switch_default") if has_default else None
        L_end = ctx.label_alloc.new_label("switch_end")

        # 3) Emisión de comparaciones y saltos a cada CASE
        for lab, (case_expr, _) in case_labels:
            cv = _as_operand(case_expr, ctx)
            t = ctx.temp_alloc.new_temp()
            ctx.emit(BinOp(dst=t, op="==", left=c, right=cv))
            ctx.emit(IfGoto(cond=t, target=lab))

        # 4) Si ninguno matchea → default (si hay) o end
        ctx.emit(Goto(L_default if has_default else L_end))

        # 5) Cuerpos de CASES
        for lab, (_, case_blk) in case_labels:
            ctx.emit(LabelInstr(lab))
            gen_stmt(case_blk, ctx)
            ctx.emit(Goto(L_end))

        # 6) DEFAULT
        if has_default:
            ctx.emit(LabelInstr(L_default))  # type: ignore[arg-type]
            gen_stmt(default_blk, ctx)       # type: ignore[arg-type]
            ctx.emit(Goto(L_end))

        # 7) END
        ctx.emit(LabelInstr(L_end))
        return

    raise ValueError(f"Sentencia no soportada: {node!r}")
