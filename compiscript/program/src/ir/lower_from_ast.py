# program/src/ir/lower_from_ast.py
from __future__ import annotations
from typing import List, Tuple, Optional, Any

from src.ast import nodes as A

ExprT = Tuple[Any, ...]
StmtT = Tuple[Any, ...]


_gensym_counter = 0
def _gensym(prefix: str) -> str:
    global _gensym_counter
    _gensym_counter += 1
    return f"__fe_{prefix}_{_gensym_counter}"



def lower_expr(e: Optional[A.Expr]) -> Optional[ExprT]:
    if e is None:
        return None

    if isinstance(e, A.IntLiteral):
        return ('const', e.value)
    if isinstance(e, A.FloatLiteral):
        return ('const', e.value)
    if isinstance(e, A.StringLiteral):
        return ('const', e.value)
    if isinstance(e, A.BoolLiteral):
        return ('const', e.value)
    if isinstance(e, A.NullLiteral):
        return ('const', None)

    if isinstance(e, A.ArrayLiteral):
        elems = [lower_expr(x) for x in e.elements]
        return ('call', '__array__', elems)

    if isinstance(e, A.Identifier):
        return ('name', e.name)
    if isinstance(e, A.ThisExpr):
        return ('name', 'this')

    if isinstance(e, A.NewExpr):
        args = [lower_expr(a) for a in e.args]
        return ('new', e.class_name, args)

    if isinstance(e, A.CallExpr):
        if isinstance(e.func, A.Identifier):
            args = [lower_expr(a) for a in e.args]
            return ('call', e.func.name, args)
        if isinstance(e.func, A.PropertyAccessExpr) and isinstance(e.func.prop, str):
            recv = lower_expr(e.func.obj)
            args = [recv] + [lower_expr(a) for a in e.args]
            return ('call', f'__mcall__{e.func.prop}', args)
        raise ValueError("callee no-identificador aún no soportado")

    if isinstance(e, A.IndexExpr):
        return ('index', lower_expr(e.array), lower_expr(e.index))

    if isinstance(e, A.PropertyAccessExpr):
        return ('prop', lower_expr(e.obj), e.prop)

    if isinstance(e, A.UnaryOp):
        return ('un', e.op, lower_expr(e.expr))

    if isinstance(e, A.BinaryOp):
        return ('bin', e.op, lower_expr(e.left), lower_expr(e.right))

    if isinstance(e, A.TernaryOp):
        return ('tern', lower_expr(e.cond), lower_expr(e.then), lower_expr(e.other))

    if isinstance(e, A.Assign):
        tgt = e.target
        rhs = lower_expr(e.value)
        if isinstance(tgt, A.Identifier):
            return ('assign', ('name', tgt.name), rhs)
        if isinstance(tgt, A.PropertyAccessExpr):
            return ('assign', ('prop', lower_expr(tgt.obj), tgt.prop), rhs)
        if isinstance(tgt, A.IndexExpr):
            return ('assign', ('index', lower_expr(tgt.array), lower_expr(tgt.index)), rhs)
        raise ValueError("assign.target no soportado (en expresión)")

    raise ValueError(f"lower_expr no soportada: {type(e).__name__}")

def lower_block(b: A.Block) -> StmtT:
    return ('block', [lower_stmt(s) for s in b.statements])

def _lower_stmt_list(stmts: List[A.Stmt]) -> StmtT:
    return ('block', [lower_stmt(s) for s in stmts])

def lower_stmt(s: A.Stmt) -> StmtT:
    if isinstance(s, A.Block):
        return lower_block(s)

    if isinstance(s, (A.FunctionDecl, A.ClassDecl)):
        return ('block', [])

    if isinstance(s, A.ExprStmt):
        if isinstance(s.expr, A.Assign):
            tgt = s.expr.target
            rhs = lower_expr(s.expr.value)
            if isinstance(tgt, A.Identifier):
                return ('assign', ('name', tgt.name), rhs)
            if isinstance(tgt, A.PropertyAccessExpr):
                return ('assign', ('prop', lower_expr(tgt.obj), tgt.prop), rhs)
            if isinstance(tgt, A.IndexExpr):
                return ('assign', ('index', lower_expr(tgt.array), lower_expr(tgt.index)), rhs)
            raise ValueError("assign.target no soportado (en ExprStmt)")
        return ('expr', lower_expr(s.expr))

    if isinstance(s, A.PrintStmt):
        return ('expr', ('call', 'print', [lower_expr(s.expr)]))

    if isinstance(s, A.VarDecl):
        if s.init is None:
            return ('block', [])
        return ('assign', ('name', s.name), lower_expr(s.init))

    if isinstance(s, A.Assign):
        tgt = s.target
        rhs = lower_expr(s.value)

        if isinstance(tgt, A.Identifier):
            return ('assign', ('name', tgt.name), rhs)
        if isinstance(tgt, A.PropertyAccessExpr):
            return ('assign', ('prop', lower_expr(tgt.obj), tgt.prop), rhs)
        if isinstance(tgt, A.IndexExpr):
            return ('assign', ('index', lower_expr(tgt.array), lower_expr(tgt.index)), rhs)

        raise ValueError("assign.target no soportado")

    if isinstance(s, A.IfStmt):
        cond = lower_expr(s.cond)
        then_b = lower_block(s.then_block)
        else_b = lower_block(s.else_block) if s.else_block is not None else None
        return ('if', cond, then_b, else_b)

    if isinstance(s, A.WhileStmt):
        return ('while', lower_expr(s.cond), lower_block(s.body))

    if isinstance(s, A.DoWhileStmt):
        return ('do_while', lower_block(s.body), lower_expr(s.cond))

    if isinstance(s, A.ForStmt):
        init_stmt: Optional[StmtT] = lower_stmt(s.init) if s.init is not None else None
        cond_expr = lower_expr(s.cond) if s.cond is not None else None

        step_stmt: Optional[StmtT] = None
        if s.update is not None:
            if isinstance(s.update, A.Assign):
                step_stmt = lower_stmt(s.update)
            else:
                step_stmt = ('expr', lower_expr(s.update))

        body_b = lower_block(s.body)
        return ('for', init_stmt, cond_expr, step_stmt, body_b)

    if isinstance(s, A.SwitchStmt):
        cond = lower_expr(s.expr)
        cases: List[Tuple[ExprT, StmtT]] = []
        for c in s.cases:
            cases.append((lower_expr(c.expr), _lower_stmt_list(c.body)))
        default_blk = _lower_stmt_list(s.default_body) if s.default_body is not None else None
        return ('switch', cond, cases, default_blk)

    if isinstance(s, A.BreakStmt):
        return ('break',)
    if isinstance(s, A.ContinueStmt):
        return ('continue',)

    if isinstance(s, A.ReturnStmt):
        if s.value is None:
            return ('return',)
        return ('return', lower_expr(s.value))

    if isinstance(s, A.ForeachStmt):
        arr_tmp = _gensym('arr')
        len_tmp = _gensym('len')
        i_tmp   = _gensym('i')

        lowered_iter = lower_expr(s.iterable)
        body_lowered = lower_block(s.body)

        body_stmts: List[StmtT] = []
        body_stmts.append(('assign', ('name', s.var_name), ('index', ('name', arr_tmp), ('name', i_tmp))))
        if isinstance(body_lowered, tuple) and body_lowered and body_lowered[0] == 'block':
            body_stmts.extend(body_lowered[1])
        else:
            body_stmts.append(body_lowered)
        body_stmts.append(('assign', ('name', i_tmp), ('bin', '+', ('name', i_tmp), ('const', 1))))

        return ('block', [
            ('assign', ('name', arr_tmp), lowered_iter),
            ('assign', ('name', len_tmp), ('call', '__len__', [('name', arr_tmp)])),
            ('assign', ('name', i_tmp), ('const', 0)),
            ('while', ('bin', '<', ('name', i_tmp), ('name', len_tmp)), ('block', body_stmts)),
        ])

    if isinstance(s, A.TryCatchStmt):
        raise NotImplementedError("try/catch aún no implementado")

    raise ValueError(f"lower_stmt no soportada: {type(s).__name__}")


def lower_function_decl(fn: A.FunctionDecl, *, owner_class: Optional[str] = None) -> Tuple[str, List[str], StmtT]:
    name = fn.name
    if owner_class:
        name = f"{owner_class}::{name}"
    params = [p.name for p in fn.params]
    body = lower_block(fn.body)
    return (name, params, body)

def lower_class_decl(cd: A.ClassDecl) -> List[Tuple[str, List[str], StmtT]]:
    out: List[Tuple[str, List[str], StmtT]] = []
    for m in cd.members:
        if isinstance(m.member, A.FunctionDecl):
            out.append(lower_function_decl(m.member, owner_class=cd.name))
    return out

def lower_program(prog: A.Program) -> List[Tuple[str, List[str], StmtT]]:
    functions: List[Tuple[str, List[str], StmtT]] = []

    for st in prog.statements:
        if isinstance(st, A.FunctionDecl):
            functions.append(lower_function_decl(st))
            continue

        if isinstance(st, A.ClassDecl):
            functions.extend(lower_class_decl(st))
            continue

    loose: List[A.Stmt] = [
        st for st in prog.statements
        if not isinstance(st, (A.FunctionDecl, A.ClassDecl))
    ]
    if loose:
        body = ('block', [lower_stmt(s) for s in loose])
        functions.append(("main", [], body))

    return functions
