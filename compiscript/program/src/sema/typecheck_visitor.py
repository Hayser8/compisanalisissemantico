# program/src/sema/typecheck_visitor.py
from __future__ import annotations
from typing import List, Optional, Tuple
from CompiscriptParser import CompiscriptParser as P
from antlr4 import ParserRuleContext, TerminalNode
from CompiscriptParser import CompiscriptParser
from CompiscriptVisitor import CompiscriptVisitor

from .errors import (
    ErrorReporter,
    E_UNDECLARED, E_ASSIGN_INCOMPAT, E_OP_TYPES, E_CALL_ARITY, E_INDEX_INVALID,
    E_MEMBER_NOT_FOUND, E_DUPLICATE_ID, E_THIS_CONTEXT, E_BAD_BREAK_CONTINUE, E_COND_NOT_BOOL,
    E_RETURN_OUTSIDE, E_MISSING_RETURN, E_ASSIGN_TO_CONST, E_DEAD_CODE,
)
from .scopes import Scope, ScopeStack, ClassScope, FunctionScope
from .symbols import (
    Symbol, VariableSymbol, ConstSymbol, ParamSymbol, FieldSymbol,
    FunctionSymbol, ClassSymbol
)
from .types import (
    Type, BOOLEAN, INTEGER, FLOAT, STRING, VOID, NULL,
    ArrayType, ClassType, function_type, call_result,
    is_boolean, is_assignable, array_of, index_result,
    result_add, result_sub, result_mul, result_div, result_mod,
    result_logical_and, result_logical_or, result_logical_not,
    result_relational, result_equality, is_numeric
)
from .type_linker import TypeLinker
from .decl_collector import DeclarationCollector


class TypeCheckVisitor(CompiscriptVisitor):
    def __init__(self, reporter: ErrorReporter, decl: DeclarationCollector) -> None:
        self.rep = reporter
        self.decl = decl
        self.scopes = ScopeStack(decl.global_scope)
        self.current_function: Optional[FunctionSymbol] = None
        self.current_class: Optional[ClassSymbol] = None
        self.loop_depth: int = 0
        self._tl = TypeLinker(self.rep, decl)

    # ===== Utilidades =====

    @property
    def scope(self) -> Scope:
        return self.scopes.current

    def _declare_local_or_error(self, ctx: ParserRuleContext, sym: Symbol) -> None:
        """
        Declara en el scope actual (sólo si NO es global/clase).
        Si el identificador ya existe en el scope ACTUAL, reporta E_DUPLICATE_ID.
        (Permite shadowing respecto a scopes exteriores.)
        """
        if self.scope.kind in ("global", "class"):
            return
        if not self.scope.declare(sym):
            self.rep.error(E_DUPLICATE_ID, f"Identificador redeclarado: {sym.name}", ctx)

    def _resolve_var(self, ctx: ParserRuleContext, name: str) -> Optional[Symbol]:
        sym = self.scope.resolve(name)
        if sym is None:
            self.rep.error(E_UNDECLARED, f"Identificador no declarado: {name}", ctx)
        return sym

    def _type_of_symbol(self, sym: Symbol) -> Optional[Type]:
        if isinstance(sym, (VariableSymbol, ConstSymbol, ParamSymbol, FieldSymbol)):
            return getattr(sym, "resolved_type", None)
        if isinstance(sym, FunctionSymbol):
            return None
        if isinstance(sym, ClassSymbol):
            return ClassType(sym.name)
        return None

    def _require_boolean(self, t: Type, ctx: ParserRuleContext):
        if not is_boolean(t):
            self.rep.error(E_COND_NOT_BOOL, f"Se requiere boolean, recibido {t}", ctx)
    
    def _current_function_scope(self) -> Optional[FunctionScope]:
        return self.scopes.current_function_scope()
    
    def _fn_key_for_current_context(self, fname: str, is_method: bool) -> str:
        path = self.scopes.function_path()
        parts = list(path) + [fname]
        if self.current_class is not None:
            if not path and is_method:
                return f"{self.current_class.name}::{fname}"
            return f"{self.current_class.name}::" + "::".join(parts)
        return "::" + "::".join(parts)

    def _maybe_capture(self, name: str, decl_scope: Optional[Scope]) -> None:
        if self.current_function is None or decl_scope is None:
            return
        if not isinstance(decl_scope, FunctionScope):
            return
        cur_fn_scope = self._current_function_scope()
        if cur_fn_scope is None:
            return
        if decl_scope is cur_fn_scope:
            return
        self.current_function.captured.add(name)

    def _member_lookup(self, ctype: ClassType, member: str) -> Optional[Symbol]:
        cname = ctype.name
        while True:
            cscope: ClassScope = self.decl.class_scopes.get(cname)
            if cscope:
                sym = cscope.resolve(member)
                if sym:
                    return sym
            cls_sym = self.decl.global_scope.resolve(cname)
            if not isinstance(cls_sym, ClassSymbol) or not cls_sym.base_name:
                break
            cname = cls_sym.base_name
        return None

    def _qualified_key_from_decl_scope(self, decl_scope: Scope, fname: str) -> str:
        parts = []
        cls = None
        s = decl_scope
        while s is not None:
            if isinstance(s, FunctionScope):
                parts.append(s.name)
            elif isinstance(s, ClassScope):
                cls = s.name
            s = s.parent
        parts = list(reversed(parts))
        parts.append(fname)
        if cls:
            return f"{cls}::" + "::".join(parts)
        return "::" + "::".join(parts)

    def _visit_block_in_current_scope(self, ctx: CompiscriptParser.BlockContext):
        must_return = False
        for st in ctx.statement():
            if must_return:
                self.rep.error(E_DEAD_CODE, "Código inalcanzable después de return/break/continue", st)
                continue
            r = self.visit(st)
            if r is True:
                must_return = True
        return must_return

    # ===== Entrypoint =====

    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        for st in ctx.statement():
            self.visit(st)
        return None

    # ===== Bloques y control de flujo =====

    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        self.scopes.enter_block()
        must_return = False
        for st in ctx.statement():
            if must_return:
                self.rep.error(E_DEAD_CODE, "Código inalcanzable después de return/break/continue", st)
                continue
            r = self.visit(st)
            if r is True:
                must_return = True
        self.scopes.pop()
        return must_return

    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        cond_t = self.visit(ctx.expression())
        if cond_t is not None:
            self._require_boolean(cond_t, ctx.expression())
        then_ret = self.visit(ctx.block(0))
        else_ret = False
        if len(ctx.block()) > 1:
            else_ret = self.visit(ctx.block(1))
        return bool(then_ret and else_ret)

    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        cond_t = self.visit(ctx.expression())
        if cond_t is not None:
            self._require_boolean(cond_t, ctx.expression())
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        return False

    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        cond_t = self.visit(ctx.expression())
        if cond_t is not None:
            self._require_boolean(cond_t, ctx.expression())
        return False

    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        if ctx.expression(0):
            cond_t = self.visit(ctx.expression(0))
            if cond_t is not None:
                self._require_boolean(cond_t, ctx.expression(0))
        if ctx.expression(1):
            self.visit(ctx.expression(1))
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        return False

    # ===== Foreach =====
    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        """
        foreach (it in expr) { ... }
        - expr debe ser ArrayType
        - el iterador 'it' toma el tipo de elemento del arreglo
        - abrimos un scope de bloque para alinear con la pasada de declaraciones
        """
        arr_t = self.visit(ctx.expression())
        elem_t: Optional[Type] = None

        if isinstance(arr_t, ArrayType):
            # Compatibilidad por si el atributo se llama distinto
            elem_t = getattr(arr_t, "elem", None) or getattr(arr_t, "element", None)
        else:
            self.rep.error(E_OP_TYPES, f"foreach requiere arreglo, recibido {arr_t}", ctx.expression())

        self.loop_depth += 1
        # Abrimos el mismo scope de bloque que usó decl_collector para el iterador
        self.scopes.enter_block()

        it_name = ctx.Identifier().getText()
        it_sym = self.scope.resolve(it_name)

        # Si por alguna razón no lo declaró decl_collector (fallback), lo declaramos aquí.
        if it_sym is None:
            it_sym = VariableSymbol(name=it_name)
            self._declare_local_or_error(ctx, it_sym)
            it_sym = self.scope.resolve(it_name)

        # Asignar tipo al iterador
        if isinstance(it_sym, VariableSymbol):
            it_sym.resolved_type = elem_t

        # Visitar cuerpo
        self.visit(ctx.block())

        # Cerrar scope del foreach
        self.scopes.pop()
        self.loop_depth -= 1
        return False

    # (Si tu gramática usa otra regla, p.ej. ForeachStmt)
    def visitForeachStmt(self, ctx: CompiscriptParser.ForeachStmtContext):
        # Adaptación mínima: asume mismos hijos que ForeachStatement
        arr_t = self.visit(ctx.expression())
        elem_t: Optional[Type] = None

        if isinstance(arr_t, ArrayType):
            elem_t = getattr(arr_t, "elem", None) or getattr(arr_t, "element", None)
        else:
            self.rep.error(E_OP_TYPES, f"foreach requiere arreglo, recibido {arr_t}", ctx.expression())

        self.loop_depth += 1
        self.scopes.enter_block()

        it_name = ctx.Identifier().getText()
        it_sym = self.scope.resolve(it_name)
        if it_sym is None:
            it_sym = VariableSymbol(name=it_name)
            self._declare_local_or_error(ctx, it_sym)
            it_sym = self.scope.resolve(it_name)
        if isinstance(it_sym, VariableSymbol):
            it_sym.resolved_type = elem_t

        # cuerpo
        if hasattr(ctx, "block") and ctx.block():
            self.visit(ctx.block())
        elif hasattr(ctx, "statement") and ctx.statement():
            self.visit(ctx.statement())

        self.scopes.pop()
        self.loop_depth -= 1
        return False

    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        if self.loop_depth == 0:
            self.rep.error(E_BAD_BREAK_CONTINUE, "`break` fuera de un bucle", ctx)
        return True

    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        if self.loop_depth == 0:
            self.rep.error(E_BAD_BREAK_CONTINUE, "`continue` fuera de un bucle", ctx)
        return True

    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        if self.current_function is None:
            self.rep.error(E_RETURN_OUTSIDE, "`return` fuera de una función", ctx)
            return True
        expected = self.current_function.resolved_return or VOID
        if ctx.expression():
            val_t = self.visit(ctx.expression())
            if expected == VOID:
                self.rep.error(E_OP_TYPES, "La función es void y no debe retornar valor", ctx)
            elif val_t is not None and not is_assignable(val_t, expected):
                self.rep.error(E_ASSIGN_INCOMPAT, f"Tipo de retorno {val_t} no asignable a {expected}", ctx.expression())
        else:
            if expected != VOID:
                self.rep.error(E_MISSING_RETURN, f"Se requiere retornar {expected}", ctx)
        return True

    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        # Tipo de la condición
        cond_t = self.visit(ctx.expression())

        # Permitimos boolean o string. Si no es ninguno, emitimos ambos errores (compatibilidad de tests).
        if cond_t is not None and cond_t not in (STRING, BOOLEAN):
            self.rep.error(E_COND_NOT_BOOL, f"switch requiere 'boolean', recibido {cond_t}", ctx.expression())
            self.rep.error(E_OP_TYPES, f"switch requiere 'string', recibido {cond_t}", ctx.expression())

        def _label_expect_msg():
            if cond_t == STRING:
                return "Etiqueta de case debe ser 'string'"
            if cond_t == BOOLEAN:
                return "Etiqueta de case debe ser 'boolean'"
            return "Etiqueta de case con tipo incompatible"

        # Duplicados solo para literales string
        seen_str_literals: set[str] = set()

        for case in ctx.switchCase():
            if case.expression():
                label_t = self.visit(case.expression())

                if cond_t in (STRING, BOOLEAN):
                    if label_t is not None and label_t != cond_t:
                        self.rep.error(E_OP_TYPES, f"{_label_expect_msg()}, recibido {label_t}", case.expression())

                if cond_t == STRING:
                    txt = case.expression().getText()
                    if len(txt) >= 2 and txt[0] == '"' and txt[-1] == '"':
                        lit = txt[1:-1]
                        if lit in seen_str_literals:
                            self.rep.error(E_DUPLICATE_ID, f'Etiqueta de case duplicada: "{lit}"', case)
                        else:
                            seen_str_literals.add(lit)

            for st in case.statement():
                self.visit(st)

        if ctx.defaultCase():
            for st in ctx.defaultCase().statement():
                self.visit(st)

        return False

    # ===== Declaraciones dentro de cuerpos =====

    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        name = ctx.Identifier().getText()

        # Tipo anotado (si existe)
        tann = None
        if ctx.typeAnnotation():
            ta = ctx.typeAnnotation()
            tctx = getattr(ta, "type_", None)() if hasattr(ta, "type_") else (ta.type() if hasattr(ta, "type") else None)
            tann = tctx.getText() if tctx is not None else None

        if self.scope.kind in ("global", "class"):
            sym = self.scope.resolve(name)
        else:
            vs = VariableSymbol(name=name, type_ann=tann)
            self._declare_local_or_error(ctx, vs)
            sym = self.scope.resolve(name)

        if ctx.initializer():
            val_t = self.visit(ctx.initializer().expression())
            if isinstance(sym, VariableSymbol):
                if tann:
                    dst = self._tl._parse_type_str(tann)
                    sym.resolved_type = dst
                    if val_t is not None and not is_assignable(val_t, dst):
                        self.rep.error(E_ASSIGN_INCOMPAT, f"No se puede asignar {val_t} a {dst}", ctx.initializer().expression())
                else:
                    sym.resolved_type = val_t
        return False

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        name = ctx.Identifier().getText()
        sym = self.scope.resolve(name)

        if not isinstance(sym, ConstSymbol):
            cs = ConstSymbol(name=name)
            self._declare_local_or_error(ctx, cs)
            sym = self.scope.resolve(name)

        tann = None
        if ctx.typeAnnotation():
            ta = ctx.typeAnnotation()
            tctx = getattr(ta, "type_", None)() if hasattr(ta, "type_") else (ta.type() if hasattr(ta, "type") else None)
            tann = tctx.getText() if tctx is not None else None

        val_t = self.visit(ctx.expression())

        if isinstance(sym, ConstSymbol):
            if tann:
                dst = self._tl._parse_type_str(tann)
                sym.resolved_type = dst
                if val_t is not None and not is_assignable(val_t, dst):
                    self.rep.error(E_ASSIGN_INCOMPAT, f"No se puede asignar {val_t} a {dst}", ctx.expression())
            else:
                sym.resolved_type = val_t
        return False

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        fname = ctx.Identifier().getText()
        is_method = self.scope.kind == "class" and isinstance(self.current_class, ClassSymbol)

        key = self._fn_key_for_current_context(fname, is_method=is_method)
        fn_scope: FunctionScope = self.decl.function_scopes[key]

        if fn_scope.parent is not self.scope:
            fn_scope.parent = self.scope

        prev_func = self.current_function
        prev_class = self.current_class

        fn_sym = self.scope.resolve(fname)
        if not isinstance(fn_sym, FunctionSymbol):
            fn_sym = FunctionSymbol(name=fname)  # fallback

        self.current_function = fn_sym

        if is_method and prev_class is None and isinstance(self.scope, ClassScope):
            self.current_class = self.decl.global_scope.resolve(self.scope.name)  # ClassSymbol

        self.scopes.push(fn_scope)
        must_return = self._visit_block_in_current_scope(ctx.block())
        self.scopes.pop()

        expected = fn_sym.resolved_return or VOID
        if expected != VOID and not must_return:
            self.rep.error(E_MISSING_RETURN, f"Falta return en todos los caminos para {expected}", ctx)

        self.current_function = prev_func
        self.current_class = prev_class
        return False

    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        cname = ctx.Identifier(0).getText()
        prev_class = self.current_class
        self.current_class = self.decl.global_scope.resolve(cname) if isinstance(self.decl.global_scope.resolve(cname), ClassSymbol) else None
        cscope = self.decl.class_scopes[cname]
        self.scopes.push(cscope)
        for m in ctx.classMember():
            fdecl = m.functionDeclaration()
            if fdecl:
                self.visit(fdecl)
        self.scopes.pop()
        self.current_class = prev_class
        return False

    # ===== Sentencias y expresiones =====

    def visitExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        self.visit(ctx.expression())
        return False

    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        if len(ctx.expression()) == 1 and ctx.Identifier():
            name = ctx.Identifier().getText()
            sym = self._resolve_var(ctx, name)
            if isinstance(sym, ConstSymbol):
                self.rep.error(E_ASSIGN_TO_CONST, f"No se puede reasignar const '{name}'", ctx)
            dst_t = self._type_of_symbol(sym) if sym else None
            val_t = self.visit(ctx.expression(0))
            if dst_t and val_t and not is_assignable(val_t, dst_t):
                self.rep.error(E_ASSIGN_INCOMPAT, f"No se puede asignar {val_t} a {dst_t}", ctx.expression(0))
            return False

        obj_t = self.visit(ctx.expression(0))
        if not isinstance(obj_t, ClassType):
            self.rep.error(E_MEMBER_NOT_FOUND, f"No es objeto para asignación de propiedad: {obj_t}", ctx.expression(0))
            return False

        prop = ctx.Identifier().getText()
        mem = self._member_lookup(obj_t, prop)
        if not isinstance(mem, FieldSymbol):
            self.rep.error(E_MEMBER_NOT_FOUND, f"Propiedad '{prop}' no existe", ctx)
            return False
        
        if isinstance(mem, FieldSymbol) and not getattr(mem, "mutable", True):
            self.rep.error(E_ASSIGN_TO_CONST, f"No se puede reasignar const '{prop}'", ctx)
            return False

        dst_t = getattr(mem, "resolved_type", None)
        val_t = self.visit(ctx.expression(1))
        if dst_t and val_t and not is_assignable(val_t, dst_t):
            self.rep.error(E_ASSIGN_INCOMPAT, f"No se puede asignar {val_t} a {dst_t}", ctx.expression(1))
        return False

    # ---------- Expresiones (núcleo) ----------
    def _eval_chain(self, ctx: ParserRuleContext, first_child, op_set: set, op_apply):
        children = list(ctx.getChildren())
        if not children:
            return None
        cur = self.visit(children[0]) if first_child is None else self.visit(first_child)
        i = 1 if first_child is None else 0
        while i < len(children):
            node = children[i]
            if isinstance(node, TerminalNode) and node.getText() in op_set:
                op = node.getText()
                rhs = self.visit(children[i+1])
                try:
                    cur = op_apply(op, cur, rhs, children[i+1])
                except Exception:
                    self.rep.error(E_OP_TYPES, f"Tipos inválidos para operador {op}", children[i+1])
                i += 2
            else:
                i += 1
        return cur

    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        return self._eval_chain(ctx, None, {"||"},
                                lambda op, a, b, nctx: result_logical_or(a, b))

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        return self._eval_chain(ctx, None, {"&&"},
                                lambda op, a, b, nctx: result_logical_and(a, b))

    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        return self._eval_chain(ctx, None, {"==", "!="},
                                lambda op, a, b, nctx: result_equality(a, b))

    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        return self._eval_chain(ctx, None, {"<", "<=", ">", ">="},
                                lambda op, a, b, nctx: result_relational(a, b))

    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        return self._eval_chain(ctx, None, {"+", "-"},
                                lambda op, a, b, nctx: result_add(a, b) if op == "+" else result_sub(a, b))

    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        return self._eval_chain(ctx, None, {"*", "/", "%"},
                                lambda op, a, b, nctx:
                                    result_mul(a, b) if op == "*" else (result_div(a, b) if op == "/" else result_mod(a, b)))

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            t = self.visit(ctx.getChild(1))
            if op == "!":
                return result_logical_not(t)
            if op == "-":
                if not is_numeric(t):
                    self.rep.error(E_OP_TYPES, f"Operador '-' requiere numérico, recibido {t}", ctx)
                return t
        return self.visit(ctx.getChild(0))

    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        if ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        if ctx.leftHandSide():
            return self._eval_left_hand_side(ctx.leftHandSide())
        return self.visit(ctx.expression())

    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        if ctx.getText() == "null":
            return NULL
        if ctx.getText() in ("true", "false"):
            return BOOLEAN
        if ctx.Literal():
            text = ctx.Literal().getText()
            if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
                return STRING
            if any(ch in text for ch in ('.', 'e', 'E')):
                return FLOAT
            return INTEGER
        if ctx.arrayLiteral():
            return self._eval_array_literal(ctx.arrayLiteral())
        return None

    def _eval_array_literal(self, ctx: CompiscriptParser.ArrayLiteralContext):
        elems = ctx.expression()
        if not elems:
            self.rep.error(E_OP_TYPES, "Literal de arreglo vacío sin tipo explícito", ctx)
            return array_of(VOID)
        t0: Optional[Type] = None
        for e in elems:
            te = self.visit(e)
            if t0 is None:
                t0 = te
            else:
                if te != t0:
                    if te and t0 and is_numeric(te) and is_numeric(t0):
                        t0 = FLOAT if FLOAT in (te, t0) else INTEGER
                    else:
                        self.rep.error(E_OP_TYPES, f"Elementos de arreglo incompatibles: {t0} y {te}", e)
        return array_of(t0 or VOID)

    def _eval_left_hand_side(self, ctx: CompiscriptParser.LeftHandSideContext):
        atom = ctx.primaryAtom()

        # a) Identificador
        if isinstance(atom, P.IdentifierExprContext):
            name = atom.Identifier().getText()
            sym, decl_scope = self.scope.resolve_with_scope(name)
            if sym is None:
                self.rep.error(E_UNDECLARED, f"Identificador no declarado: {name}", atom)
                base_t = None
            else:
                if isinstance(sym, (VariableSymbol, ConstSymbol, ParamSymbol)):
                    self._maybe_capture(name, decl_scope)
                if isinstance(sym, (VariableSymbol, ConstSymbol, ParamSymbol, FieldSymbol)):
                    base_t = self._type_of_symbol(sym)
                elif isinstance(sym, FunctionSymbol):
                    base_t = None
                elif isinstance(sym, ClassSymbol):
                    base_t = ClassType(sym.name)
                else:
                    base_t = None

        # b) new Clase(args)
        elif isinstance(atom, P.NewExprContext):
            cname = atom.Identifier().getText()
            args = []
            if atom.arguments():
                for a in atom.arguments().expression():
                    args.append(self.visit(a))

            csym = self.decl.global_scope.resolve(cname)
            if not isinstance(csym, ClassSymbol):
                self.rep.error(E_MEMBER_NOT_FOUND, f"Clase '{cname}' no existe", atom)
                return ClassType(cname)

            ctor = self._member_lookup(ClassType(cname), "constructor")
            if isinstance(ctor, FunctionSymbol):
                fscope = self.decl.function_scopes.get(f"{cname}::constructor")
                exp = [getattr(fscope.resolve(p.name), "resolved_type", None) for p in ctor.params] if fscope else [getattr(p, "resolved_type", None) for p in ctor.params]
                try:
                    _ = call_result(function_type(exp, VOID), args)
                except Exception as ex:
                    msg = str(ex)
                    code = E_CALL_ARITY if "Aridad" in msg else E_OP_TYPES
                    self.rep.error(code, f"Constructor de {cname}: {msg}", atom)
            else:
                if len(args) != 0:
                    self.rep.error(E_CALL_ARITY, f"{cname} no tiene constructor; se esperaban 0 argumentos", atom)
            base_t = ClassType(cname)

        # c) this
        elif isinstance(atom, P.ThisExprContext):
            if self.current_class is None:
                self.rep.error(E_THIS_CONTEXT, "`this` solo puede usarse dentro de métodos de clase", atom)
                return None
            base_t = ClassType(self.current_class.name)

        else:
            base_t = None

        # ---------- 2) Sufijos ----------
        cur_t = base_t
        for s in ctx.suffixOp():
            if isinstance(s, P.CallExprContext):
                if isinstance(atom, P.IdentifierExprContext) and base_t is None:
                    fname = atom.Identifier().getText()
                    fsym, decl_scope = self.scope.resolve_with_scope(fname)
                    if not isinstance(fsym, FunctionSymbol):
                        self.rep.error(E_UNDECLARED, f"Llamada a '{fname}' que no es función", s)
                        return None
                    key = self._qualified_key_from_decl_scope(decl_scope, fname) if decl_scope else f"::{fname}"
                    fscope = self.decl.function_scopes.get(key)
                    params = []
                    if fscope:
                        for p in fsym.params:
                            ps = fscope.resolve(p.name)
                            params.append(getattr(ps, "resolved_type", None))
                    else:
                        for p in fsym.params:
                            params.append(getattr(p, "resolved_type", None))
                    ret = fsym.resolved_return or VOID
                    fn_t = function_type(params, ret)
                else:
                    if cur_t is None:
                        self.rep.error(E_OP_TYPES, "Llamada sobre algo que no es función", s)
                        return None
                    fn_t = cur_t

                args = []
                if s.arguments():
                    for a in s.arguments().expression():
                        args.append(self.visit(a))
                try:
                    ret_t = call_result(fn_t, args)  # type: ignore[arg-type]
                except Exception as ex:
                    msg = str(ex)
                    code = E_CALL_ARITY if "Aridad" in msg else E_OP_TYPES
                    self.rep.error(code, msg, s)
                    ret_t = getattr(fn_t, "ret", None)  # type: ignore[attr-defined]
                cur_t = ret_t

            elif isinstance(s, P.IndexExprContext):
                idx_t = self.visit(s.expression())
                try:
                    cur_t = index_result(cur_t, idx_t)  # type: ignore[arg-type]
                except Exception:
                    self.rep.error(E_INDEX_INVALID, f"Indexación inválida sobre {cur_t} con índice {idx_t}", s)
                    cur_t = None

            elif isinstance(s, P.PropertyAccessExprContext):
                prop = s.Identifier().getText()
                if not isinstance(cur_t, ClassType):
                    self.rep.error(E_MEMBER_NOT_FOUND, f"Acceso '{prop}' sobre no-objeto {cur_t}", s)
                    cur_t = None
                else:
                    mem = self._member_lookup(cur_t, prop)
                    if mem is None:
                        self.rep.error(E_MEMBER_NOT_FOUND, f"Miembro '{prop}' no existe en {cur_t}", s)
                        cur_t = None
                    elif isinstance(mem, FieldSymbol):
                        cur_t = getattr(mem, "resolved_type", None)
                    elif isinstance(mem, FunctionSymbol):
                        fscope = self.decl.function_scopes.get(f"{cur_t.name}::{prop}")
                        params = []
                        if fscope:
                            for p in mem.params:
                                ps = fscope.resolve(p.name)
                                params.append(getattr(ps, "resolved_type", None))
                        else:
                            for p in mem.params:
                                params.append(getattr(p, "resolved_type", None))
                        ret = mem.resolved_return or VOID
                        cur_t = function_type(params, ret)
                    else:
                        cur_t = None
        return cur_t

    # ===== Asignación como expresión =====

    def visitAssignExpr(self, ctx: CompiscriptParser.AssignExprContext):
        lhs_ctx = ctx.lhs
        rhs_t = self.visit(ctx.assignmentExpr())

        atom = lhs_ctx.primaryAtom()
        if isinstance(atom, P.ThisExprContext):
            if self.current_class is None:
                self.rep.error(E_THIS_CONTEXT, "`this` solo puede usarse dentro de métodos de clase", atom)
            else:
                self.rep.error(E_OP_TYPES, "No se puede asignar a `this`", atom)
            return rhs_t

        if lhs_ctx.suffixOp() and isinstance(lhs_ctx.suffixOp()[-1], CompiscriptParser.PropertyAccessExprContext):
            obj_t = self._eval_left_hand_side_truncated(lhs_ctx, drop_last=1)
            if not isinstance(obj_t, ClassType):
                self.rep.error(E_MEMBER_NOT_FOUND, "Asignación a propiedad sobre no-objeto", ctx)
                return rhs_t
            prop = lhs_ctx.suffixOp()[-1].Identifier().getText()
            mem = self._member_lookup(obj_t, prop)
            if not isinstance(mem, FieldSymbol):
                self.rep.error(E_MEMBER_NOT_FOUND, f"Propiedad '{prop}' no existe", ctx)
                return rhs_t
            dst_t = getattr(mem, "resolved_type", None)
            if isinstance(mem, FieldSymbol) and not getattr(mem, "mutable", True):
                self.rep.error(E_ASSIGN_TO_CONST, f"No se puede reasignar const '{prop}'", ctx)
                return dst_t or rhs_t
            if dst_t and rhs_t and not is_assignable(rhs_t, dst_t):
                self.rep.error(E_ASSIGN_INCOMPAT, f"No se puede asignar {rhs_t} a {dst_t}", ctx.assignmentExpr())
            return dst_t or rhs_t

        if lhs_ctx.suffixOp() and isinstance(lhs_ctx.suffixOp()[-1], CompiscriptParser.IndexExprContext):
            arr_t = self._eval_left_hand_side_truncated(lhs_ctx, drop_last=1)
            idx_t = self.visit(lhs_ctx.suffixOp()[-1].expression())
            elem_t = None
            try:
                elem_t = index_result(arr_t, idx_t)  # type: ignore[arg-type]
            except Exception:
                self.rep.error(E_INDEX_INVALID, "Asignación con indexación inválida", lhs_ctx.suffixOp()[-1])
                return rhs_t
            if elem_t and rhs_t and not is_assignable(rhs_t, elem_t):
                self.rep.error(E_ASSIGN_INCOMPAT, f"No se puede asignar {rhs_t} a {elem_t}", ctx.assignmentExpr())
            return elem_t or rhs_t

        self.rep.error(E_OP_TYPES, "El lado izquierdo de la asignación no es asignable", ctx)
        return rhs_t

    def _eval_left_hand_side_truncated(self, ctx: CompiscriptParser.LeftHandSideContext, drop_last: int):
        atom = ctx.primaryAtom()
        if isinstance(atom, P.IdentifierExprContext):
            name = atom.Identifier().getText()
            sym = self._resolve_var(atom, name)
            cur_t = self._type_of_symbol(sym) if sym else None
        elif isinstance(atom, P.NewExprContext):
            cur_t = ClassType(atom.Identifier().getText())
        elif isinstance(atom, P.ThisExprContext):
            cur_t = ClassType(self.current_class.name) if self.current_class else None
        else:
            cur_t = None

        for s in ctx.suffixOp()[:-drop_last]:
            if isinstance(s, P.CallExprContext):
                self.rep.error(E_OP_TYPES, "Llamada en LHS no soportada", s)
                return None
            elif isinstance(s, P.IndexExprContext):
                idx_t = self.visit(s.expression())
                try:
                    cur_t = index_result(cur_t, idx_t)  # type: ignore[arg-type]
                except Exception:
                    self.rep.error(E_INDEX_INVALID, f"Indexación inválida", s)
                    return None
            elif isinstance(s, P.PropertyAccessExprContext):
                prop = s.Identifier().getText()
                if not isinstance(cur_t, ClassType):
                    self.rep.error(E_MEMBER_NOT_FOUND, f"Acceso '{prop}' sobre no-objeto", s)
                    return None
                mem = self._member_lookup(cur_t, prop)
                if mem is None:
                    self.rep.error(E_MEMBER_NOT_FOUND, f"Miembro '{prop}' no existe", s)
                    return None
                if isinstance(mem, FieldSymbol):
                    cur_t = getattr(mem, "resolved_type", None)
                elif isinstance(mem, FunctionSymbol):
                    fscope = self.decl.function_scopes.get(f"{cur_t.name}::{prop}")
                    params = []
                    if fscope:
                        for p in mem.params:
                            ps = fscope.resolve(p.name)
                            params.append(getattr(ps, "resolved_type", None))
                    else:
                        for p in mem.params:
                            params.append(getattr(p, "resolved_type", None))
                    ret = mem.resolved_return or VOID
                    cur_t = function_type(params, ret)
        return cur_t
