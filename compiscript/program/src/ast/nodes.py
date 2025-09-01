# src/ast/nodes.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union

Pos = Tuple[int, int]  # (line, column)

# ====== Base ======

@dataclass
class Node:
    pos: Optional[Pos] = None

# ====== Programa y sentencias ======

@dataclass
class Program(Node):
    statements: List["Stmt"] = field(default_factory=list)

class Stmt(Node):
    pass

@dataclass
class Block(Stmt):
    statements: List[Stmt] = field(default_factory=list)

@dataclass
class VarDecl(Stmt):
    name: str = ""
    type_ann: Optional[str] = None
    init: Optional["Expr"] = None
    is_const: bool = False

@dataclass
class Assign(Stmt):
    target: "Expr" = None
    value: "Expr" = None

@dataclass
class ExprStmt(Stmt):
    expr: "Expr" = None

@dataclass
class PrintStmt(Stmt):
    expr: "Expr" = None

@dataclass
class IfStmt(Stmt):
    cond: "Expr" = None
    then_block: Block = None
    else_block: Optional[Block] = None

@dataclass
class WhileStmt(Stmt):
    cond: "Expr" = None
    body: Block = None

@dataclass
class DoWhileStmt(Stmt):
    body: Block = None
    cond: "Expr" = None

@dataclass
class ForStmt(Stmt):
    init: Optional[Stmt] = None          # VarDecl o Assign o None
    cond: Optional["Expr"] = None
    update: Optional["Expr"] = None
    body: Block = None

@dataclass
class ForeachStmt(Stmt):
    var_name: str = ""
    iterable: "Expr" = None
    body: Block = None

@dataclass
class TryCatchStmt(Stmt):
    try_block: Block = None
    err_name: str = ""
    catch_block: Block = None

@dataclass
class SwitchCase(Node):
    expr: "Expr" = None
    body: List[Stmt] = field(default_factory=list)

@dataclass
class SwitchStmt(Stmt):
    expr: "Expr" = None
    cases: List[SwitchCase] = field(default_factory=list)
    default_body: Optional[List[Stmt]] = None

@dataclass
class BreakStmt(Stmt):
    pass

@dataclass
class ContinueStmt(Stmt):
    pass

@dataclass
class ReturnStmt(Stmt):
    value: Optional["Expr"] = None

@dataclass
class Param(Node):
    name: str = ""
    type_ann: Optional[str] = None

@dataclass
class FunctionDecl(Stmt):
    name: str = ""
    params: List[Param] = field(default_factory=list)
    return_type: Optional[str] = None
    body: Block = None
    is_constructor: bool = False

@dataclass
class ClassMember(Node):
    member: Union[FunctionDecl, VarDecl] = None

@dataclass
class ClassDecl(Stmt):
    name: str = ""
    base: Optional[str] = None
    members: List[ClassMember] = field(default_factory=list)

# ====== Expresiones ======

class Expr(Node):
    pass

@dataclass
class Identifier(Expr):
    name: str = ""

@dataclass
class ThisExpr(Expr):
    pass

@dataclass
class NewExpr(Expr):
    class_name: str = ""
    args: List[Expr] = field(default_factory=list)

@dataclass
class CallExpr(Expr):
    func: Expr = None
    args: List[Expr] = field(default_factory=list)

@dataclass
class IndexExpr(Expr):
    array: Expr = None
    index: Expr = None

@dataclass
class PropertyAccessExpr(Expr):
    obj: Expr = None
    prop: str = ""

@dataclass
class IntLiteral(Expr):
    value: int = 0

@dataclass
class FloatLiteral(Expr):   
    value: float = 0.0 
    
@dataclass
class StringLiteral(Expr):
    value: str = ""

@dataclass
class BoolLiteral(Expr):
    value: bool = False

@dataclass
class NullLiteral(Expr):
    pass

@dataclass
class ArrayLiteral(Expr):
    elements: List[Expr] = field(default_factory=list)

@dataclass
class UnaryOp(Expr):
    op: str = ""
    expr: Expr = None

@dataclass
class BinaryOp(Expr):
    op: str = ""
    left: Expr = None
    right: Expr = None

@dataclass
class TernaryOp(Expr):
    cond: Expr = None
    then: Expr = None
    other: Expr = None
