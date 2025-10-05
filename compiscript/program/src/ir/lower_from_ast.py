# program/src/ir/lower_from_ast.py
from __future__ import annotations
from typing import List, Tuple, Optional, Any

from src.ast import nodes as A

# Tipos de salida que consumen gen_expr / gen_stmt
ExprT = Tuple[Any, ...]
StmtT = Tuple[Any, ...]


# ---------- util: nombres únicos para temporales sintéticos ----------
_gensym_counter = 0
def _gensym(prefix: str) -> str:
    global _gensym_counter
    _gensym_counter += 1
    return f"__fe_{prefix}_{_gensym_counter}"


# =============== Expresiones ===============

def lower_expr(e: Optional[A.Expr]) -> Optional[ExprT]:
    if e is None:
        return None

    # Literales
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

    # Array literal -> helper de runtime
    # [1,2,3] => ('call','__array__',[('const',1),('const',2),('const',3)])
    if isinstance(e, A.ArrayLiteral):
        elems = [lower_expr(x) for x in e.elements]
        return ('call', '__array__', elems)

    # Identificador / this
    if isinstance(e, A.Identifier):
        return ('name', e.name)
    if isinstance(e, A.ThisExpr):
        return ('name', 'this')

    # new Clase(args)
    if isinstance(e, A.NewExpr):
        args = [lower_expr(a) for a in e.args]
        return ('new', e.class_name, args)

    # Llamada
    if isinstance(e, A.CallExpr):
        # Callee: identificador simple
        if isinstance(e.func, A.Identifier):
            args = [lower_expr(a) for a in e.args]
            return ('call', e.func.name, args)
        # Callee: acceso a propiedad => método: obj.m(a,b) -> __mcall__m(obj, a, b)
        if isinstance(e.func, A.PropertyAccessExpr) and isinstance(e.func.prop, str):
            recv = lower_expr(e.func.obj)
            args = [recv] + [lower_expr(a) for a in e.args]
            return ('call', f'__mcall__{e.func.prop}', args)
        raise ValueError("Lowering de llamada con callee no-identificador aún no soportado")

    # Indexación: arr[idx]
    if isinstance(e, A.IndexExpr):
        return ('index', lower_expr(e.array), lower_expr(e.index))

    # Acceso a propiedad: obj.p
    if isinstance(e, A.PropertyAccessExpr):
        return ('prop', lower_expr(e.obj), e.prop)

    # Unario
    if isinstance(e, A.UnaryOp):
        return ('un', e.op, lower_expr(e.expr))

    # Binario
    if isinstance(e, A.BinaryOp):
        return ('bin', e.op, lower_expr(e.left), lower_expr(e.right))

    # Ternario
    if isinstance(e, A.TernaryOp):
        return ('tern', lower_expr(e.cond), lower_expr(e.then), lower_expr(e.other))

    # Asignación usada como EXPRESIÓN (p.ej. en el update de un for)
    if isinstance(e, A.Assign):
        tgt = e.target
        rhs = lower_expr(e.value)
        if isinstance(tgt, A.Identifier):
            return ('assign', ('name', tgt.name), rhs)
        if isinstance(tgt, A.PropertyAccessExpr):
            return ('assign', ('prop', lower_expr(tgt.obj), tgt.prop), rhs)
        if isinstance(tgt, A.IndexExpr):
            return ('assign', ('index', lower_expr(tgt.array), lower_expr(tgt.index)), rhs)
        raise ValueError("Assign.target no soportado (en expresión)")

    raise ValueError(f"lower_expr: expresión no soportada: {type(e).__name__}")


# =============== Sentencias ===============

def lower_block(b: A.Block) -> StmtT:
    return ('block', [lower_stmt(s) for s in b.statements])

def _lower_stmt_list(stmts: List[A.Stmt]) -> StmtT:
    return ('block', [lower_stmt(s) for s in stmts])

def lower_stmt(s: A.Stmt) -> StmtT:
    # Bloque
    if isinstance(s, A.Block):
        return lower_block(s)

    # --- NUEVO: ignorar decls de función/clase dentro de bloques ---
    if isinstance(s, (A.FunctionDecl, A.ClassDecl)):
        # Se emiten (o resuelven) en otra fase; aquí no generan IR in-situ.
        return ('block', [])

    # Expresión como sentencia
    if isinstance(s, A.ExprStmt):
        # Parche: si la "expresión" es Assign, bajamos a stmt 'assign'
        if isinstance(s.expr, A.Assign):
            tgt = s.expr.target
            rhs = lower_expr(s.expr.value)
            if isinstance(tgt, A.Identifier):
                return ('assign', ('name', tgt.name), rhs)
            if isinstance(tgt, A.PropertyAccessExpr):
                return ('assign', ('prop', lower_expr(tgt.obj), tgt.prop), rhs)
            if isinstance(tgt, A.IndexExpr):
                return ('assign', ('index', lower_expr(tgt.array), lower_expr(tgt.index)), rhs)
            raise ValueError("Assign.target no soportado (en ExprStmt)")
        # Si no es Assign, es una expresión normal
        return ('expr', lower_expr(s.expr))

    # print expr -> call print(expr)
    if isinstance(s, A.PrintStmt):
        return ('expr', ('call', 'print', [lower_expr(s.expr)]))

    # Declaraciones (var/const) -> si hay init, simplemente asignamos name = init
    if isinstance(s, A.VarDecl):
        if s.init is None:
            return ('block', [])
        return ('assign', ('name', s.name), lower_expr(s.init))

    # Asignación: target puede ser id, prop o index
    if isinstance(s, A.Assign):
        tgt = s.target
        rhs = lower_expr(s.value)

        if isinstance(tgt, A.Identifier):
            return ('assign', ('name', tgt.name), rhs)
        if isinstance(tgt, A.PropertyAccessExpr):
            return ('assign', ('prop', lower_expr(tgt.obj), tgt.prop), rhs)
        if isinstance(tgt, A.IndexExpr):
            return ('assign', ('index', lower_expr(tgt.array), lower_expr(tgt.index)), rhs)

        raise ValueError("Assign.target no soportado")

    # if / else
    if isinstance(s, A.IfStmt):
        cond = lower_expr(s.cond)
        then_b = lower_block(s.then_block)
        else_b = lower_block(s.else_block) if s.else_block is not None else None
        return ('if', cond, then_b, else_b)

    # while
    if isinstance(s, A.WhileStmt):
        return ('while', lower_expr(s.cond), lower_block(s.body))

    # do-while
    if isinstance(s, A.DoWhileStmt):
        return ('do_while', lower_block(s.body), lower_expr(s.cond))

    # for (init puede ser VarDecl o Assign o None; update puede ser Assign o Expr)
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

    # switch
    if isinstance(s, A.SwitchStmt):
        cond = lower_expr(s.expr)
        cases: List[Tuple[ExprT, StmtT]] = []
        for c in s.cases:
            cases.append((lower_expr(c.expr), _lower_stmt_list(c.body)))
        default_blk = _lower_stmt_list(s.default_body) if s.default_body is not None else None
        return ('switch', cond, cases, default_blk)

    # break / continue
    if isinstance(s, A.BreakStmt):
        return ('break',)
    if isinstance(s, A.ContinueStmt):
        return ('continue',)

    # return
    if isinstance(s, A.ReturnStmt):
        if s.value is None:
            return ('return',)
        return ('return', lower_expr(s.value))

    # -------- FOREACH (nuevo) --------
    if isinstance(s, A.ForeachStmt):
        # foreach (v in iterable) body
        # Desazucarado:
        #   __arr = iterable
        #   __len = __len__(__arr)
        #   __i = 0
        #   while (__i < __len) {
        #       v = __arr[__i]
        #       body...
        #       __i = __i + 1
        #   }
        arr_tmp = _gensym('arr')
        len_tmp = _gensym('len')
        i_tmp   = _gensym('i')

        lowered_iter = lower_expr(s.iterable)
        body_lowered = lower_block(s.body)  # ('block', [...])

        # cuerpo del while: [ v = arr[i], (stmts...), i = i + 1 ]
        body_stmts: List[StmtT] = []
        body_stmts.append(('assign', ('name', s.var_name), ('index', ('name', arr_tmp), ('name', i_tmp))))
        if isinstance(body_lowered, tuple) and body_lowered and body_lowered[0] == 'block':
            body_stmts.extend(body_lowered[1])  # inyectar sentencias reales
        else:
            body_stmts.append(body_lowered)
        body_stmts.append(('assign', ('name', i_tmp), ('bin', '+', ('name', i_tmp), ('const', 1))))

        # bloque completo
        return ('block', [
            ('assign', ('name', arr_tmp), lowered_iter),
            ('assign', ('name', len_tmp), ('call', '__len__', [('name', arr_tmp)])),
            ('assign', ('name', i_tmp), ('const', 0)),
            ('while', ('bin', '<', ('name', i_tmp), ('name', len_tmp)), ('block', body_stmts)),
        ])

    # try/catch: pendiente
    if isinstance(s, A.TryCatchStmt):
        raise NotImplementedError("lowering de 'try/catch' aún no implementado")

    # class/func: no aparecen dentro de blocks una vez que filtramos en el toplevel
    raise ValueError(f"lower_stmt: sentencia no soportada: {type(s).__name__}")


# =============== Top-level: funciones / programa ===============

def lower_function_decl(fn: A.FunctionDecl, *, owner_class: Optional[str] = None) -> Tuple[str, List[str], StmtT]:
    """
    Devuelve una tupla (name, params, body_stmt) lista para IRAdapter.emit_function.
    - owner_class: si no es None, nombra la función como 'Clase::metodo'.
    """
    name = fn.name
    if owner_class:
        name = f"{owner_class}::{name}"
    params = [p.name for p in fn.params]
    body = lower_block(fn.body)
    return (name, params, body)

def lower_class_decl(cd: A.ClassDecl) -> List[Tuple[str, List[str], StmtT]]:
    """
    Convierte los métodos de clase en funciones 'Clase::metodo'.
    Campos (VarDecl/Const) no se emiten como TAC aquí; se manejan en runtime/objeto.
    """
    out: List[Tuple[str, List[str], StmtT]] = []
    for m in cd.members:
        if isinstance(m.member, A.FunctionDecl):
            out.append(lower_function_decl(m.member, owner_class=cd.name))
    return out

def lower_program(prog: A.Program) -> List[Tuple[str, List[str], StmtT]]:
    """
    Toma el AST Program y devuelve [(fn_name, params, body_stmt), ...]
    con funciones top-level y métodos de clase.
    """
    functions: List[Tuple[str, List[str], StmtT]] = []

    for st in prog.statements:
        # Funciones top-level
        if isinstance(st, A.FunctionDecl):
            functions.append(lower_function_decl(st))
            continue

        # Clases (métodos)
        if isinstance(st, A.ClassDecl):
            functions.extend(lower_class_decl(st))
            continue

    # Detectar statements "sueltos" y crear 'main' si aplica
    loose: List[A.Stmt] = [
        st for st in prog.statements
        if not isinstance(st, (A.FunctionDecl, A.ClassDecl))
    ]
    if loose:
        body = ('block', [lower_stmt(s) for s in loose])
        functions.append(("main", [], body))

    return functions
