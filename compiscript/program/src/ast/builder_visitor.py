# src/ast/builder_visitor.py
from __future__ import annotations
from typing import List, Optional
from antlr4 import TerminalNode
from CompiscriptParser import CompiscriptParser as P
from CompiscriptParser import CompiscriptParser
from CompiscriptVisitor import CompiscriptVisitor

from . import nodes as A

def _pos(ctx) -> A.Pos:
    if ctx is None or ctx.start is None:
        return None
    t = ctx.start
    # ANTLR usa 1-based line, 0-based column; homogenizamos a 1-based ambos
    return (t.line, t.column + 1)

class ASTBuilder(CompiscriptVisitor):
    """Convierte el parse tree de ANTLR a un AST propio (src/ast/nodes.py)."""

    # ===== Programa y sentencias =====

    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        out = A.Program(pos=_pos(ctx))
        for st in ctx.statement():
            out.statements.append(self.visit(st))
        return out

    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        blk = A.Block(pos=_pos(ctx))
        for st in ctx.statement():
            blk.statements.append(self.visit(st))
        return blk

    def visitStatement(self, ctx: CompiscriptParser.StatementContext):
        # Delega en la alternativa concreta
        return self.visitChildren(ctx)

    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        name = ctx.Identifier().getText()
        type_ann = None
        if ctx.typeAnnotation():
            ta = ctx.typeAnnotation()
            tctx = getattr(ta, "type_", None)() if hasattr(ta, "type_") else (ta.type() if hasattr(ta, "type") else None)
            type_ann = tctx.getText() if tctx else None
        init = self.visit(ctx.initializer().expression()) if ctx.initializer() else None
        return A.VarDecl(name=name, type_ann=type_ann, init=init, is_const=False, pos=_pos(ctx))

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        name = ctx.Identifier().getText()
        type_ann = None
        if ctx.typeAnnotation():
            ta = ctx.typeAnnotation()
            tctx = getattr(ta, "type_", None)() if hasattr(ta, "type_") else (ta.type() if hasattr(ta, "type") else None)
            type_ann = tctx.getText() if tctx else None
        init = self.visit(ctx.expression())
        return A.VarDecl(name=name, type_ann=type_ann, init=init, is_const=True, pos=_pos(ctx))

    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        # 'Identifier' '=' expr | expr '.' Identifier '=' expr
        if ctx.Identifier() and len(ctx.expression()) == 1:
            target = A.Identifier(name=ctx.Identifier().getText(), pos=_pos(ctx))
            value = self.visit(ctx.expression(0))
            return A.Assign(target=target, value=value, pos=_pos(ctx))
        # obj.prop = value
        obj = self.visit(ctx.expression(0))
        prop = A.PropertyAccessExpr(obj=obj, prop=ctx.Identifier(0).getText(), pos=_pos(ctx))
        value = self.visit(ctx.expression(1))
        return A.Assign(target=prop, value=value, pos=_pos(ctx))

    def visitExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        return A.ExprStmt(expr=self.visit(ctx.expression()), pos=_pos(ctx))

    def visitPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        return A.PrintStmt(expr=self.visit(ctx.expression()), pos=_pos(ctx))

    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        cond = self.visit(ctx.expression())
        then_b = self.visit(ctx.block(0))
        else_b = self.visit(ctx.block(1)) if len(ctx.block()) > 1 else None
        return A.IfStmt(cond=cond, then_block=then_b, else_block=else_b, pos=_pos(ctx))

    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        return A.WhileStmt(cond=self.visit(ctx.expression()), body=self.visit(ctx.block()), pos=_pos(ctx))

    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        return A.DoWhileStmt(body=self.visit(ctx.block()), cond=self.visit(ctx.expression()), pos=_pos(ctx))

    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        init_stmt = None
        if ctx.variableDeclaration():
            init_stmt = self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            init_stmt = self.visit(ctx.assignment())
        cond = self.visit(ctx.expression(0)) if ctx.expression(0) else None
        update = self.visit(ctx.expression(1)) if ctx.expression(1) else None
        body = self.visit(ctx.block())
        return A.ForStmt(init=init_stmt, cond=cond, update=update, body=body, pos=_pos(ctx))

    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        name = ctx.Identifier().getText()
        iterable = self.visit(ctx.expression())
        body = self.visit(ctx.block())
        return A.ForeachStmt(var_name=name, iterable=iterable, body=body, pos=_pos(ctx))

    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        return A.BreakStmt(pos=_pos(ctx))

    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        return A.ContinueStmt(pos=_pos(ctx))

    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        val = self.visit(ctx.expression()) if ctx.expression() else None
        return A.ReturnStmt(value=val, pos=_pos(ctx))

    def visitTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        return A.TryCatchStmt(
            try_block=self.visit(ctx.block(0)),
            err_name=ctx.Identifier().getText(),
            catch_block=self.visit(ctx.block(1)),
            pos=_pos(ctx)
        )

    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        expr = self.visit(ctx.expression())
        cases: List[A.SwitchCase] = []
        for c in ctx.switchCase():
            ce = self.visit(c.expression())
            body = [self.visit(s) for s in c.statement()]
            cases.append(A.SwitchCase(expr=ce, body=body, pos=_pos(c)))
        default_body = None
        if ctx.defaultCase():
            default_body = [self.visit(s) for s in ctx.defaultCase().statement()]
        return A.SwitchStmt(expr=expr, cases=cases, default_body=default_body, pos=_pos(ctx))

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        name = ctx.Identifier().getText()
        is_ctor = (name == "constructor")
        params: List[A.Param] = []
        if ctx.parameters():
            for p in ctx.parameters().parameter():
                pann = None
                if p.type():
                    pann = p.type().getText()
                params.append(A.Param(name=p.Identifier().getText(), type_ann=pann, pos=_pos(p)))
        ret_ann = ctx.type().getText() if ctx.type() else None
        body = self.visit(ctx.block())
        return A.FunctionDecl(name=name, params=params, return_type=ret_ann, body=body, is_constructor=is_ctor, pos=_pos(ctx))

    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        name = ctx.Identifier(0).getText()
        base = ctx.Identifier(1).getText() if len(ctx.Identifier()) > 1 else None
        members: List[A.ClassMember] = []
        for m in ctx.classMember():
            if m.functionDeclaration():
                members.append(A.ClassMember(member=self.visit(m.functionDeclaration()), pos=_pos(m)))
            elif m.variableDeclaration():
                members.append(A.ClassMember(member=self.visit(m.variableDeclaration()), pos=_pos(m)))
            elif m.constantDeclaration():
                members.append(A.ClassMember(member=self.visit(m.constantDeclaration()), pos=_pos(m)))
        return A.ClassDecl(name=name, base=base, members=members, pos=_pos(ctx))

    # ===== Expresiones =====

    def visitExpression(self, ctx: CompiscriptParser.ExpressionContext):
        return self.visit(ctx.assignmentExpr())

    # assignmentExpr con etiquetas: AssignExpr | PropertyAssignExpr | ExprNoAssign
    def visitAssignExpr(self, ctx: CompiscriptParser.AssignExprContext):
        # lhs '=' assignmentExpr
        lhs = self.visit(ctx.lhs)
        rhs = self.visit(ctx.assignmentExpr())
        return A.Assign(target=lhs, value=rhs, pos=_pos(ctx))

    def visitPropertyAssignExpr(self, ctx: CompiscriptParser.PropertyAssignExprContext):
        base = self.visit(ctx.lhs)
        target = A.PropertyAccessExpr(obj=base, prop=ctx.Identifier().getText(), pos=_pos(ctx))
        rhs = self.visit(ctx.assignmentExpr())
        return A.Assign(target=target, value=rhs, pos=_pos(ctx))

    def visitExprNoAssign(self, ctx: CompiscriptParser.ExprNoAssignContext):
        return self.visit(ctx.conditionalExpr())

    def visitTernaryExpr(self, ctx: CompiscriptParser.ConditionalExprContext):
        # logicalOr ('?' e1 ':' e2)?
        if ctx.getChildCount() == 1:
            return self.visit(ctx.logicalOrExpr())
        cond = self.visit(ctx.logicalOrExpr())
        then = self.visit(ctx.expression(0))
        other = self.visit(ctx.expression(1))
        return A.TernaryOp(cond=cond, then=then, other=other, pos=_pos(ctx))

    # Cadenas binarias
    def _fold_binary(self, ctx, op_set: set, child_rule_name: str):
        # Lee children alternando subexpresiones y operadores
        children = list(ctx.getChildren())
        cur = self.visit(getattr(ctx, child_rule_name)(0))
        i = 1
        # Estructura: [lhs, op, rhs, op, rhs, ...]
        while i < len(children):
            node = children[i]
            if isinstance(node, TerminalNode) and node.getText() in op_set:
                op = node.getText()
                rhs = self.visit(getattr(ctx, child_rule_name)( (i+1)//2 ))
                cur = A.BinaryOp(op=op, left=cur, right=rhs, pos=_pos(ctx))
                i += 2
            else:
                i += 1
        return cur

    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        return self._fold_binary(ctx, {"||"}, "logicalAndExpr")

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        return self._fold_binary(ctx, {"&&"}, "equalityExpr")

    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        return self._fold_binary(ctx, {"==", "!="}, "relationalExpr")

    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        return self._fold_binary(ctx, {"<", "<=", ">", ">="}, "additiveExpr")

    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        return self._fold_binary(ctx, {"+", "-"}, "multiplicativeExpr")

    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        return self._fold_binary(ctx, {"*", "/", "%"}, "unaryExpr")

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            e = self.visit(ctx.getChild(1))
            return A.UnaryOp(op=op, expr=e, pos=_pos(ctx))
        return self.visit(ctx.getChild(0))

    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        if ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        if ctx.leftHandSide():
            return self.visit(ctx.leftHandSide())
        return self.visit(ctx.expression())

    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        text = ctx.getText()
        if text == "null":
            return A.NullLiteral(pos=_pos(ctx))
        if text == "true":
            return A.BoolLiteral(value=True, pos=_pos(ctx))
        if text == "false":
            return A.BoolLiteral(value=False, pos=_pos(ctx))
        if ctx.Literal():
            tok = ctx.Literal()
            # Distinguir entero vs string por comillas
            s = tok.getText()
            if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
                return A.StringLiteral(value=s[1:-1], pos=_pos(ctx))
            return A.IntLiteral(value=int(s), pos=_pos(ctx))
        if ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        return None

    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext):
        elems = []
        if ctx.expression():
            for e in ctx.expression():
                elems.append(self.visit(e))
        return A.ArrayLiteral(elements=elems, pos=_pos(ctx))

    # leftHandSide: primaryAtom (suffixOp)*
    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext):
        atom = self.visit(ctx.primaryAtom())
        cur = atom
        for s in ctx.suffixOp():
            if isinstance(s, P.CallExprContext):
                args = []
                if s.arguments():
                    for a in s.arguments().expression():
                        args.append(self.visit(a))
                cur = A.CallExpr(func=cur, args=args, pos=_pos(s))
            elif isinstance(s, P.IndexExprContext):
                cur = A.IndexExpr(array=cur, index=self.visit(s.expression()), pos=_pos(s))
            elif isinstance(s, P.PropertyAccessExprContext):
                cur = A.PropertyAccessExpr(obj=cur, prop=s.Identifier().getText(), pos=_pos(s))
        return cur

    # primaryAtom alts
    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        return A.Identifier(name=ctx.Identifier().getText(), pos=_pos(ctx))

    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        args = []
        if ctx.arguments():
            for a in ctx.arguments().expression():
                args.append(self.visit(a))
        return A.NewExpr(class_name=ctx.Identifier().getText(), args=args, pos=_pos(ctx))

    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        return A.ThisExpr(pos=_pos(ctx))
