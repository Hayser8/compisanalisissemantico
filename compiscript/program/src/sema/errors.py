# program/src/sema/errors.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any

# Códigos sugeridos (irá creciendo con tu proyecto)
E_DUPLICATE_ID   = "E101"
E_DUPLICATE_PARAM= "E102"
E_INHERIT_CYCLE  = "E140"
E_UNKNOWN_TYPE  = "E120"
E_UNDECLARED        = "E100"
E_ASSIGN_INCOMPAT   = "E200"
E_OP_TYPES          = "E201"
E_CALL_ARITY        = "E202"
E_INDEX_INVALID     = "E203"
E_MEMBER_NOT_FOUND  = "E204"
E_THIS_CONTEXT      = "E205"
E_BAD_BREAK_CONTINUE= "E300"
E_COND_NOT_BOOL     = "E301"
E_RETURN_OUTSIDE    = "E302"
E_MISSING_RETURN    = "E303"
E_ASSIGN_TO_CONST   = "E401"
E_DEAD_CODE         = "E500"

@dataclass
class SemanticError:
    code: str
    message: str
    line: int
    column: int

class ErrorReporter:
    """Acumula errores sin abortar la compilación."""
    def __init__(self) -> None:
        self.errors: List[SemanticError] = []

    def _pos_from_ctx(self, ctx: Any) -> Tuple[int, int]:
        try:
            tok = ctx.start  # ctx de ANTLR
            return tok.line, tok.column
        except Exception:
            return (-1, -1)

    def error(
        self,
        code: str,
        message: str,
        ctx: Optional[Any] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
    ) -> None:
        if line is not None and column is not None:
            ln, col = line, column
        elif ctx is not None:
            ln, col = self._pos_from_ctx(ctx)
        else:
            ln, col = -1, -1
        self.errors.append(SemanticError(code, message, ln, col))

    def has_errors(self) -> bool:
        return bool(self.errors)

    def __len__(self) -> int:
        return len(self.errors)

    def clear(self) -> None:
        self.errors.clear()

    def summary(self) -> str:
        return "\n".join(f"{e.code} @ {e.line}:{e.column} - {e.message}" for e in self.errors)
