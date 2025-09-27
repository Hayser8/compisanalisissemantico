from __future__ import annotations
from typing import Dict, List, Optional
from antlr4 import ParserRuleContext
from CompiscriptParser import CompiscriptParser
from CompiscriptVisitor import CompiscriptVisitor
from .errors import ErrorReporter, E_DUPLICATE_ID, E_INHERIT_CYCLE, E_DUPLICATE_PARAM
from .scopes import GlobalScope, ClassScope, FunctionScope, Scope
from .symbols import (
    Symbol, VariableSymbol, ConstSymbol, ParamSymbol, FieldSymbol,
    FunctionSymbol, ClassSymbol
)

# ----- helpers de tipos (robustos a type() vs type_()) -----
def _type_to_str(tctx) -> Optional[str]:
    return tctx.getText() if tctx is not None else None

def _get_type_from_typeAnnotation(ta_ctx):
    if ta_ctx is None:
        return None
    if hasattr(ta_ctx, "type_"):
        return ta_ctx.type_()
    if hasattr(ta_ctx, "type"):
        return ta_ctx.type()
    return None

def _get_type_from_fn_decl(fn_ctx):
    if hasattr(fn_ctx, "type_"):
        return fn_ctx.type_()
    if hasattr(fn_ctx, "type"):
        return fn_ctx.type()
    return None

def _get_type_from_param(pctx):
    if hasattr(pctx, "type_"):
        return pctx.type_()
    if hasattr(pctx, "type"):
        return pctx.type()
    return None
# -----------------------------------------------------------

class DeclarationCollector(CompiscriptVisitor):
    """
    Pasada 1: declara identificadores (sin evaluar cuerpos).
    - Top-level: vars/consts/funcs/clases
    - En clases: campos y métodos (marca constructor)
    - Parámetros: detecta duplicados
    - Herencia: detecta ciclos
    """
    def __init__(self, reporter: ErrorReporter) -> None:
        self.reporter = reporter
        self.global_scope = GlobalScope()
        self.scope_stack: List[Scope] = [self.global_scope]
        self.class_scopes: Dict[str, ClassScope] = {}
        self.function_scopes: Dict[str, FunctionScope] = {}
        self.class_nodes: Dict[str, ParserRuleContext] = {}
        self.class_bases: Dict[str, Optional[str]] = {}

    @property
    def current_scope(self) -> Scope:
        return self.scope_stack[-1]

    def push(self, scope: Scope) -> None:
        self.scope_stack.append(scope)

    def pop(self) -> None:
        self.scope_stack.pop()

    def declare_or_error(self, sym: Symbol, ctx: ParserRuleContext) -> None:
        # Prohíbe redeclaración **en el mismo scope** (sí permite shadowing)
        if not self.current_scope.declare(sym):
            self.reporter.error(E_DUPLICATE_ID, f"Identificador redeclarado: {sym.name}", ctx)

    # Entrypoint
    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        for st in ctx.statement():
            self.visit(st)
        self._check_inheritance_cycles()
        return self.global_scope

    # ---- Declaraciones top-level ----
    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        # Solo declaramos en global o clase (NO locales)
        if self.current_scope.kind not in ("global", "class"):
            return None
        name = ctx.Identifier().getText()
        tann = _type_to_str(_get_type_from_typeAnnotation(ctx.typeAnnotation()))
        self.declare_or_error(VariableSymbol(name=name, type_ann=tann), ctx)
        return None

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        # Solo declaramos en global o clase (NO locales)
        if self.current_scope.kind not in ("global", "class"):
            return None
        name = ctx.Identifier().getText()
        tann = _type_to_str(_get_type_from_typeAnnotation(ctx.typeAnnotation()))
        self.declare_or_error(ConstSymbol(name=name, type_ann=tann), ctx)
        return None

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext, *, is_method=False):
        name = ctx.Identifier().getText()
        ret_ann = _type_to_str(_get_type_from_fn_decl(ctx))
        fn_sym = FunctionSymbol(name=name, return_ann=ret_ann, is_method=is_method)
        self.declare_or_error(fn_sym, ctx)

        # Scope de función para parámetros
        fn_scope = FunctionScope(name=name, parent=self.current_scope)

        # KEY única según contexto (global / anidada / en método)
        key = self._qualified_fn_key(name)
        self.function_scopes[key] = fn_scope

        # Parámetros: detectar duplicados **dentro de la misma lista**
        if ctx.parameters():
            seen = set()
            for pctx in ctx.parameters().parameter():
                pname = pctx.Identifier().getText()
                if pname in seen:
                    self.reporter.error(E_DUPLICATE_PARAM, f"Parámetro duplicado: {pname}", pctx)
                    continue
                seen.add(pname)
                ptann = _type_to_str(_get_type_from_param(pctx))
                psym = ParamSymbol(name=pname, type_ann=ptann)
                if not fn_scope.declare(psym):
                    self.reporter.error(E_DUPLICATE_PARAM, f"Parámetro duplicado: {pname}", pctx)
                fn_sym.params.append(psym)

        # Entrar al scope de función para recorrer y encontrar funciones anidadas
        self.push(fn_scope)
        if ctx.block():
            self.visit(ctx.block())
        self.pop()
        return None

    # ---- Clases y miembros ----
    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        name = ctx.Identifier(0).getText()
        base_name = ctx.Identifier(1).getText() if len(ctx.Identifier()) > 1 else None
        csym = ClassSymbol(name=name, base_name=base_name)
        self.declare_or_error(csym, ctx)

        self.class_nodes[name] = ctx
        self.class_bases[name] = base_name

        class_scope = ClassScope(name=name, parent=self.current_scope)
        self.class_scopes[name] = class_scope

        self.push(class_scope)
        for m in ctx.classMember():
            fdecl = m.functionDeclaration()
            vdecl = m.variableDeclaration()
            cdecl = m.constantDeclaration()
            if fdecl:
                mname = fdecl.Identifier().getText()
                is_ctor = (mname == "constructor")
                ret_ann = _type_to_str(_get_type_from_fn_decl(fdecl))
                msym = FunctionSymbol(name=mname, return_ann=ret_ann, is_method=True, is_constructor=is_ctor)
                self.declare_or_error(msym, fdecl)
                # Scope para parámetros del método
                m_scope = FunctionScope(name=mname, parent=class_scope)
                self.function_scopes[self._method_key(name, mname)] = m_scope
                if fdecl.parameters():
                    seen = set()
                    for pctx in fdecl.parameters().parameter():
                        pname = pctx.Identifier().getText()
                        if pname in seen:
                            self.reporter.error(E_DUPLICATE_PARAM, f"Parámetro duplicado: {pname}", pctx)
                            continue
                        seen.add(pname)
                        ptann = _type_to_str(_get_type_from_param(pctx))
                        psym = ParamSymbol(name=pname, type_ann=ptann)
                        if not m_scope.declare(psym):
                            self.reporter.error(E_DUPLICATE_PARAM, f"Parámetro duplicado: {pname}", pctx)
                        msym.params.append(psym)
                # Recorrer cuerpo del método para detectar funciones anidadas
                self.push(m_scope)
                if fdecl.block():
                    self.visit(fdecl.block())
                self.pop()
            elif vdecl:
                vname = vdecl.Identifier().getText()
                tann = _type_to_str(_get_type_from_typeAnnotation(vdecl.typeAnnotation()))
                self.declare_or_error(FieldSymbol(name=vname, type_ann=tann), vdecl)
            elif cdecl:
                cname = cdecl.Identifier().getText()
                tann = _type_to_str(_get_type_from_typeAnnotation(cdecl.typeAnnotation()))
                self.declare_or_error(FieldSymbol(name=cname, type_ann=tann, mutable=False), cdecl)
        self.pop()
        return None

    # ---- Ciclos de herencia ----
    def _check_inheritance_cycles(self):
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {k: WHITE for k in self.class_bases.keys()}

        def dfs(u: str):
            color[u] = GRAY
            v = self.class_bases.get(u)
            if v is not None and v in self.class_bases:
                if color.get(v, WHITE) == GRAY:
                    self.reporter.error(E_INHERIT_CYCLE, f"Ciclo de herencia involucrando '{u}' y '{v}'", self.class_nodes[u])
                elif color.get(v, WHITE) == WHITE:
                    dfs(v)
            color[u] = BLACK

        for cname in list(self.class_bases.keys()):
            if color.get(cname, WHITE) == WHITE:
                dfs(cname)

    # ---- Keys helper ----
    def _fn_key(self, fn: FunctionSymbol) -> str:
        return f"::{fn.name}"

    def _method_key(self, cls: str, m: str) -> str:
        return f"{cls}::{m}"

    def _qualified_fn_key(self, name: str) -> str:
        parts: List[str] = []
        cls = None
        for s in self.scope_stack:
            if isinstance(s, ClassScope):
                cls = s.name
            elif isinstance(s, FunctionScope):
                parts.append(s.name)
        parts.append(name)
        if cls:
            return f"{cls}::" + "::".join(parts)
        return "::" + "::".join(parts)
