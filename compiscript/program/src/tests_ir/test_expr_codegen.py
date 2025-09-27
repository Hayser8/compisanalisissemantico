from src.ir.model import Program, Return
from src.ir.pretty import program_to_str
from src.ir.context import IRGenContext
from src.ir.temps import TempAllocator, LabelAllocator
from src.ir.gen_expr import gen_expr

# Helpers para armar rápidamente el contexto de una función
def make_ctx(fn_name="test", params=None):
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function(fn_name, params or [])
    return ctx, prog


def test_addition_of_names():
    # expr: a + b
    ctx, prog = make_ctx("sum", params=["a", "b"])
    t = gen_expr(('bin', '+', ('name', 'a'), ('name', 'b')), ctx)
    ctx.emit(Return(t))
    text = program_to_str(prog)

    # Labels generados: L0 para el bloque de entrada
    expected = (
        "function sum(a, b):\n"
        "L0:\n"
        "  t0 = a + b\n"
        "  return t0"
    )
    assert text == expected


def test_unary_and_logical_bin():
    # expr: !x || y
    ctx, prog = make_ctx("logic", params=["x", "y"])
    not_x = ('un', '!', ('name', 'x'))
    expr = ('bin', '||', not_x, ('name', 'y'))
    t = gen_expr(expr, ctx)
    ctx.emit(Return(t))
    text = program_to_str(prog)

    expected = (
        "function logic(x, y):\n"
        "L0:\n"
        "  t0 = ! x\n"
        "  t1 = t0 || y\n"
        "  return t1"
    )
    assert text == expected


def test_ternary_generates_branches_and_assign():
    # expr: cond ? a : b
    ctx, prog = make_ctx("tern", params=["cond", "a", "b"])
    expr = ('tern', ('name', 'cond'), ('name', 'a'), ('name', 'b'))
    t = gen_expr(expr, ctx)
    ctx.emit(Return(t))
    text = program_to_str(prog)

    # Checamos la estructura (labels con sufijos then/else/end)
    # Los IDs de las etiquetas dependen del alloc; sabemos que L0 es el bloque,
    # y luego se generan L1_then, L2_else, L3_end en ese orden.
    expected = (
        "function tern(cond, a, b):\n"
        "L0:\n"
        "  if cond goto L1_then\n"
        "  goto L2_else\n"
        "L1_then:\n"
        "  t0 = a\n"
        "  goto L3_end\n"
        "L2_else:\n"
        "  t0 = b\n"
        "  goto L3_end\n"
        "L3_end:\n"
        "  return t0"
    )
    assert text == expected
