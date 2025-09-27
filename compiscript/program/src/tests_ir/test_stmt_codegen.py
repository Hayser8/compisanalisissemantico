from src.ir.model import Program, Return
from src.ir.pretty import program_to_str
from src.ir.context import IRGenContext
from src.ir.temps import TempAllocator, LabelAllocator
from src.ir.gen_expr import gen_expr
from src.ir.gen_stmt import gen_stmt


def make_ctx(fn_name="f", params=None):
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function(fn_name, params or [])
    return ctx, prog


def test_if_else_codegen():
    # if (cond) { return a; } else { return b; }
    ctx, prog = make_ctx("iff", params=["cond", "a", "b"])
    stmt = ('if', ('name', 'cond'),
            ('block', [('return', ('name', 'a'))]),
            ('block', [('return', ('name', 'b'))]))
    gen_stmt(stmt, ctx)
    text = program_to_str(prog)

    expected = (
        "function iff(cond, a, b):\n"
        "L0:\n"
        "  if cond goto L1_then\n"
        "  goto L2_else\n"
        "L1_then:\n"
        "  return a\n"
        "  goto L3_end\n"
        "L2_else:\n"
        "  return b\n"
        "  goto L3_end\n"
        "L3_end:"
    )
    assert text == expected


def test_while_with_break_continue():
    # while (x) { continue; break; }
    ctx, prog = make_ctx("loop", params=["x"])
    stmt = ('while', ('name', 'x'),
            ('block', [
                ('continue',),
                ('break',),
            ]))
    gen_stmt(stmt, ctx)
    # Añadimos un return void para cerrar bien el ejemplo:
    gen_stmt(('return',), ctx)
    text = program_to_str(prog)

    expected = (
        "function loop(x):\n"
        "L0:\n"
        "  goto L1_while_head\n"
        "L1_while_head:\n"
        "  if x goto L2_while_body\n"
        "  goto L3_while_end\n"
        "L2_while_body:\n"
        "  goto L1_while_head\n"
        "  goto L3_while_end\n"
        "  goto L1_while_head\n"
        "L3_while_end:\n"
        "  return"
    )
    assert text == expected


def test_switch_string_and_bool():
    # switch (s) { case "a": return a; case "b": return b; default: return d; }
    ctx, prog = make_ctx("sw", params=["s", "a", "b", "d"])
    stmt = ('switch',
            ('name', 's'),
            [
                (('const', "a"), ('block', [('return', ('name', 'a'))])),
                (('const', "b"), ('block', [('return', ('name', 'b'))])),
            ],
            ('block', [('return', ('name', 'd'))])
    )
    gen_stmt(stmt, ctx)
    text1 = program_to_str(prog)

    expected1 = (
        "function sw(s, a, b, d):\n"
        "L0:\n"
        "  t0 = s == \"a\"\n"
        "  if t0 goto L1_case\n"
        "  t1 = s == \"b\"\n"
        "  if t1 goto L2_case\n"
        "  goto L3_switch_default\n"
        "L1_case:\n"
        "  return a\n"
        "  goto L4_switch_end\n"
        "L2_case:\n"
        "  return b\n"
        "  goto L4_switch_end\n"
        "L3_switch_default:\n"
        "  return d\n"
        "  goto L4_switch_end\n"
        "L4_switch_end:"
    )
    assert text1 == expected1

    # Segundo: switch (b) { case true: return a; default: return d; }
    ctx2, prog2 = make_ctx("swb", params=["b", "a", "d"])
    stmt2 = ('switch',
             ('name', 'b'),
             [(('const', True), ('block', [('return', ('name', 'a'))]))],
             ('block', [('return', ('name', 'd'))]))
    gen_stmt(stmt2, ctx2)
    text2 = program_to_str(prog2)

    expected2 = (
        "function swb(b, a, d):\n"
        "L0:\n"
        "  t0 = b == true\n"
        "  if t0 goto L1_case\n"
        "  goto L2_switch_default\n"
        "L1_case:\n"
        "  return a\n"
        "  goto L3_switch_end\n"
        "L2_switch_default:\n"
        "  return d\n"
        "  goto L3_switch_end\n"
        "L3_switch_end:"
    )
    assert text2 == expected2
