from src.ir.pretty import program_to_str
from src.ir.adapter import lower_program

def test_e2e_if_and_return():
    # function f(x, y) { if (x) return y; return; }
    body = (
        'block', [
            ('if', ('name', 'x'),
                   ('block', [('return', ('name', 'y'))]),
                   None),
            ('return',),
        ]
    )
    prog = lower_program([("f", ["x", "y"], body)])
    text = program_to_str(prog)

    expected = (
        "function f(x, y):\n"
        "L0:\n"
        "  if x goto L1_then\n"
        "  goto L2_end\n"
        "L1_then:\n"
        "  return y\n"
        "  goto L2_end\n"
        "L2_end:\n"
        "  return"
    )
    assert text == expected


def test_e2e_switch_string_bool():
    # function g(s, b, a, d) {
    #   switch (s) { case "a": return a; default: return d; }
    #   switch (b) { case true: return a; default: return d; }
    # }
    body = (
        'block', [
            ('switch',
                ('name', 's'),
                [
                    (('const', "a"), ('block', [('return', ('name', 'a'))])),
                ],
                ('block', [('return', ('name', 'd'))])
            ),
            ('switch',
                ('name', 'b'),
                [
                    (('const', True), ('block', [('return', ('name', 'a'))])),
                ],
                ('block', [('return', ('name', 'd'))])
            ),
        ]
    )
    prog = lower_program([("g", ["s", "b", "a", "d"], body)])
    text = program_to_str(prog)

    expected = (
        "function g(s, b, a, d):\n"
        "L0:\n"
        "  t0 = s == \"a\"\n"
        "  if t0 goto L1_case\n"
        "  goto L2_switch_default\n"
        "L1_case:\n"
        "  return a\n"
        "  goto L3_switch_end\n"
        "L2_switch_default:\n"
        "  return d\n"
        "  goto L3_switch_end\n"
        "L3_switch_end:\n"
        "  t1 = b == true\n"
        "  if t1 goto L4_case\n"
        "  goto L5_switch_default\n"
        "L4_case:\n"
        "  return a\n"
        "  goto L6_switch_end\n"
        "L5_switch_default:\n"
        "  return d\n"
        "  goto L6_switch_end\n"
        "L6_switch_end:"
    )
    assert text == expected
