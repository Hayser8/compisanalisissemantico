# program/src/ast/dot_export.py
from __future__ import annotations
from typing import List, Tuple
from . import nodes as A

class ASTDotExporter:
    def __init__(self):
        self.lines: List[str] = []
        self._id = 0
        self._map = {}

    def _nid(self, n):
        key = id(n)
        if key in self._map:
            return self._map[key]
        nid = f"n{len(self._map)}"
        self._map[key] = nid
        return nid


    def _label(self, n: A.Node) -> str:
        # Etiquetas compactas por tipo
        t = type(n).__name__
        if isinstance(n, A.VarDecl):
            return f"{t}\\n{name_or(n.name)} : {n.type_ann or ''}{' (const)' if n.is_const else ''}"
        if isinstance(n, A.FunctionDecl):
            ps = ", ".join([p.name + (':' + p.type_ann if p.type_ann else '') for p in n.params])
            rt = n.return_type or 'void'
            flag = ' (ctor)' if n.is_constructor else ''
            return f"{t}{flag}\\n{n.name}({ps}) : {rt}"
        if isinstance(n, A.ClassDecl):
            base = f" : {n.base}" if n.base else ""
            return f"{t}\\n{n.name}{base}"
        if isinstance(n, A.Identifier):
            return f"Id\\n{n.name}"
        if isinstance(n, A.PropertyAccessExpr):
            return f".{n.prop}"
        if isinstance(n, A.IntLiteral):
            return f"Int\\n{n.value}"
        if isinstance(n, A.StringLiteral):
            return f"Str\\n{n.value}"
        if isinstance(n, A.BoolLiteral):
            return f"Bool\\n{n.value}"
        if isinstance(n, A.NullLiteral):
            return "null"
        if isinstance(n, A.UnaryOp):
            return f"UnOp\\n{n.op}"
        if isinstance(n, A.BinaryOp):
            return f"BinOp\\n{n.op}"
        if isinstance(n, A.TernaryOp):
            return "Ternary ? :"
        if isinstance(n, A.NewExpr):
            return f"new {n.class_name}"
        if isinstance(n, A.CallExpr):
            return "call"
        if isinstance(n, A.IndexExpr):
            return "index"
        if isinstance(n, A.ArrayLiteral):
            return "array"
        if isinstance(n, A.ReturnStmt):
            return "return"
        if isinstance(n, A.IfStmt):
            return "if"
        if isinstance(n, A.WhileStmt):
            return "while"
        if isinstance(n, A.DoWhileStmt):
            return "do-while"
        if isinstance(n, A.ForStmt):
            return "for"
        if isinstance(n, A.ForeachStmt):
            return "foreach"
        if isinstance(n, A.TryCatchStmt):
            return "try-catch"
        if isinstance(n, A.SwitchStmt):
            return "switch"
        if isinstance(n, A.SwitchCase):
            return "case"
        if isinstance(n, A.BreakStmt):
            return "break"
        if isinstance(n, A.ContinueStmt):
            return "continue"
        if isinstance(n, A.ExprStmt):
            return "expr;"
        if isinstance(n, A.PrintStmt):
            return "print"
        if isinstance(n, A.Assign):
            return "="
        if isinstance(n, A.Block):
            return "block"
        if isinstance(n, A.Program):
            return "program"
        if isinstance(n, A.ThisExpr):
            return "this"
        return t

    def _emit(self, s: str):
        self.lines.append(s)

    def _edge(self, a: A.Node, b: A.Node, label: str = ""):
        aid = self._nid(a); bid = self._nid(b)
        if label:
            self._emit(f'{aid} -> {bid} [label="{label}"];')
        else:
            self._emit(f"{aid} -> {bid};")

    def _node(self, n: A.Node):
        nid = self._nid(n)
        label = self._label(n).replace('"', '\\"')
        self._emit(f'{nid} [label="{label}"];')

    # Recorrido simple con casos relevantes
    def _walk(self, n: A.Node):
        self._node(n)

        # Programa y sentencias
        if isinstance(n, A.Program):
            for s in n.statements:
                self._node(s); self._edge(n, s); self._walk(s)
        elif isinstance(n, A.Block):
            for s in n.statements:
                self._node(s); self._edge(n, s); self._walk(s)
        elif isinstance(n, A.VarDecl):
            if n.init:
                self._node(n.init); self._edge(n, n.init, "init"); self._walk(n.init)
        elif isinstance(n, A.Assign):
            self._node(n.target); self._edge(n, n.target, "lhs"); self._walk(n.target)
            self._node(n.value); self._edge(n, n.value, "rhs"); self._walk(n.value)
        elif isinstance(n, A.ExprStmt):
            self._node(n.expr); self._edge(n, n.expr); self._walk(n.expr)
        elif isinstance(n, A.PrintStmt):
            self._node(n.expr); self._edge(n, n.expr); self._walk(n.expr)
        elif isinstance(n, A.IfStmt):
            self._node(n.cond); self._edge(n, n.cond, "cond"); self._walk(n.cond)
            self._node(n.then_block); self._edge(n, n.then_block, "then"); self._walk(n.then_block)
            if n.else_block:
                self._node(n.else_block); self._edge(n, n.else_block, "else"); self._walk(n.else_block)
        elif isinstance(n, A.WhileStmt):
            self._node(n.cond); self._edge(n, n.cond, "cond"); self._walk(n.cond)
            self._node(n.body); self._edge(n, n.body, "body"); self._walk(n.body)
        elif isinstance(n, A.DoWhileStmt):
            self._node(n.body); self._edge(n, n.body, "body"); self._walk(n.body)
            self._node(n.cond); self._edge(n, n.cond, "cond"); self._walk(n.cond)
        elif isinstance(n, A.ForStmt):
            if n.init:
                self._node(n.init); self._edge(n, n.init, "init"); self._walk(n.init)
            if n.cond:
                self._node(n.cond); self._edge(n, n.cond, "cond"); self._walk(n.cond)
            if n.update:
                self._node(n.update); self._edge(n, n.update, "update"); self._walk(n.update)
            self._node(n.body); self._edge(n, n.body, "body"); self._walk(n.body)
        elif isinstance(n, A.ForeachStmt):
            self._node(n.iterable); self._edge(n, n.iterable, "in"); self._walk(n.iterable)
            self._node(n.body); self._edge(n, n.body, "body"); self._walk(n.body)
        elif isinstance(n, A.TryCatchStmt):
            self._node(n.try_block); self._edge(n, n.try_block, "try"); self._walk(n.try_block)
            self._node(n.catch_block); self._edge(n, n.catch_block, f"catch {n.err_name}"); self._walk(n.catch_block)
        elif isinstance(n, A.SwitchStmt):
            self._node(n.expr); self._edge(n, n.expr, "switch"); self._walk(n.expr)
            for c in n.cases:
                self._node(c); self._edge(n, c); self._node(c.expr); self._edge(c, c.expr, "case"); self._walk(c.expr)
                for s in c.body:
                    self._node(s); self._edge(c, s); self._walk(s)
            if n.default_body:
                # nodo sintético para default
                dummy = A.Node()
                self._node(dummy); self._edge(n, dummy, "default")
                for s in n.default_body:
                    self._node(s); self._edge(dummy, s); self._walk(s)
        elif isinstance(n, A.ReturnStmt):
            if n.value:
                self._node(n.value); self._edge(n, n.value); self._walk(n.value)
        elif isinstance(n, A.FunctionDecl):
            for p in n.params:
                self._node(p); self._edge(n, p, "param")
            self._node(n.body); self._edge(n, n.body, "body"); self._walk(n.body)
        elif isinstance(n, A.ClassDecl):
            for m in n.members:
                self._node(m); self._edge(n, m)
                self._node(m.member); self._edge(m, m.member); self._walk(m.member)

        # Expresiones
        elif isinstance(n, A.CallExpr):
            self._node(n.func); self._edge(n, n.func, "fn"); self._walk(n.func)
            for a in n.args:
                self._node(a); self._edge(n, a, "arg"); self._walk(a)
        elif isinstance(n, A.PropertyAccessExpr):
            self._node(n.obj); self._edge(n, n.obj, "obj"); self._walk(n.obj)
        elif isinstance(n, A.IndexExpr):
            self._node(n.array); self._edge(n, n.array, "arr"); self._walk(n.array)
            self._node(n.index); self._edge(n, n.index, "idx"); self._walk(n.index)
        elif isinstance(n, A.ArrayLiteral):
            for e in n.elements:
                self._node(e); self._edge(n, e); self._walk(e)
        elif isinstance(n, A.UnaryOp):
            self._node(n.expr); self._edge(n, n.expr); self._walk(n.expr)
        elif isinstance(n, A.BinaryOp):
            self._node(n.left); self._edge(n, n.left, "L"); self._walk(n.left)
            self._node(n.right); self._edge(n, n.right, "R"); self._walk(n.right)
        elif isinstance(n, A.TernaryOp):
            self._node(n.cond); self._edge(n, n.cond, "cond"); self._walk(n.cond)
            self._node(n.then); self._edge(n, n.then, "then"); self._walk(n.then)
            self._node(n.other); self._edge(n, n.other, "else"); self._walk(n.other)
        else:
            # Hojas: Identifier, literals, ThisExpr, NewExpr ...
            if isinstance(n, (A.NewExpr,)):
                for a in n.args:
                    self._node(a); self._edge(n, a, "arg"); self._walk(a)

    def to_dot(self, root: A.Node) -> str:
        self.lines = ["digraph AST {", '  node [shape=box, fontsize=10, fontname="Courier"];']
        self._walk(root)
        self.lines.append("}")
        return "\n".join(self.lines)

def name_or(x): return x or ""
