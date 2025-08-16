# program/tests/test_errors.py
from src.sema.errors import ErrorReporter, SemanticError, E_DUPLICATE_ID, E_INHERIT_CYCLE

class _DummyTok:
    def __init__(self, line, column):
        self.line = line
        self.column = column

class _DummyCtx:
    def __init__(self, line, column):
        self.start = _DummyTok(line, column)

def test_error_with_explicit_position():
    rep = ErrorReporter()
    rep.error(E_DUPLICATE_ID, "Identificador redeclarado: x", line=10, column=3)
    assert rep.has_errors()
    assert len(rep) == 1
    e = rep.errors[0]
    assert e.code == E_DUPLICATE_ID
    assert (e.line, e.column) == (10, 3)
    assert "x" in e.message

def test_error_with_ctx_position():
    rep = ErrorReporter()
    ctx = _DummyCtx(5, 7)
    rep.error(E_INHERIT_CYCLE, "Ciclo de herencia A↔B", ctx=ctx)
    e = rep.errors[0]
    assert (e.line, e.column) == (5, 7)
    assert "Ciclo" in e.message

def test_summary_and_clear():
    rep = ErrorReporter()
    rep.error(E_DUPLICATE_ID, "dup a", line=1, column=1)
    rep.error(E_INHERIT_CYCLE, "ciclo", line=2, column=2)
    s = rep.summary()
    assert "E101" in s and "E140" in s
    rep.clear()
    assert not rep.has_errors()
    assert len(rep) == 0
