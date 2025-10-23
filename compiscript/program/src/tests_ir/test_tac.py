# program/src/tests_ir/test_tac_senior_suite.py
import re
from typing import List

import pytest

from src.ir.adapter import IRAdapter
from src.ir.context import IRGenContext
from src.ir.model import (
    Program,
    LabelInstr, Assign, UnaryOp, BinOp, IfGoto, Goto, Call, Return,
    Load, Store, GetProp, SetProp, NewObject,
)
from src.ir.pretty import program_to_str
from src.ir.gen_stmt import gen_stmt
from src.ir.gen_expr import gen_expr
from src.ir.temps import TempAllocator, LabelAllocator
from src.ast import nodes as A  # Necesario para tests que bajan desde AST declarativo


def _instrs_of(prog: Program) -> List:
    return [ins for fn in prog.functions for bb in fn.blocks for ins in bb.instrs]

def _find_calls(prog: Program, func_name: str) -> List[Call]:
    return [ins for ins in _instrs_of(prog) if isinstance(ins, Call) and ins.func == func_name]


# ---------------------------------------------------------------------------
# 1) Allocators se resetean por función (t0/L0 en cada una)
# ---------------------------------------------------------------------------
def test_allocators_reset_per_function():
    adapter = IRAdapter.new()

    body = ('block', [
        ('expr', ('bin', '+', ('const', 1), ('const', 2))),
        ('return',),
    ])
    adapter.emit_function("f1", [], body)
    adapter.emit_function("f2", [], body)

    txt = program_to_str(adapter.program)

    # Extrae los cuerpos de cada función
    f1 = re.findall(r"function f1\([^\)]*\):(.+?)function f2\(", txt, flags=re.S)[0]
    f2 = re.findall(r"function f2\([^\)]*\):(.+)$",        txt, flags=re.S)[0]

    assert "t0 = 1 + 2" in f1
    assert "t0 = 1 + 2" in f2, "Los temporales deberían reiniciarse por función (t0 en f2)"

    # También labels reiniciadas: tolera línea en blanco tras el header
    assert re.search(r"^\s*L0:\s*$", f1, flags=re.M), "El cuerpo de f1 debe comenzar con L0:"
    assert re.search(r"^\s*L0:\s*$", f2, flags=re.M), "El cuerpo de f2 debe comenzar con L0:"


# ---------------------------------------------------------------------------
# 2) Limpieza de loop stack con while anidados + break/continue
# ---------------------------------------------------------------------------
def test_nested_loops_break_continue_cleanup():
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("nested", [])

    inner = ('while', ('name', 'c2'), ('block', [
        ('continue',),
        ('break',),
    ]))
    outer = ('while', ('name', 'c1'), ('block', [
        inner,
        ('continue',),
        ('break',),
    ]))
    gen_stmt(outer, ctx)
    ctx.end_function()

    assert ctx._loop_stack == []
    assert ctx.current_block is None and ctx.current_function is None


# ---------------------------------------------------------------------------
# 3) switch sin fallthrough: cada case y default salta a end
# ---------------------------------------------------------------------------
def test_switch_no_fallthrough():
    ctx = IRGenContext(program=Program(), temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("sw", ["s"])
    stmt = ('switch',
            ('name', 's'),
            [
                (('const', "a"), ('block', [('return', ('const', 1))])),
                (('const', "b"), ('block', [('return', ('const', 2))])),
            ],
            ('block', [('return', ('const', 0))]),
    )
    gen_stmt(stmt, ctx)
    txt = program_to_str(ctx.program)
    ctx.end_function()

    # Captura cada bloque case COMPLETO hasta la próxima etiqueta o EOF
    case_blocks = re.findall(r"(L\d+_case:\n(?:[^\n]*\n)*(?=(?:L\d+:|$)))", txt)
    for cb in case_blocks:
        assert re.search(r"^\s+goto L\d+_switch_end\s*$", cb, flags=re.M), f"Falta salto a end en:\n{cb}"

    # Default (si existe) también debe saltar a end
    default_block = re.search(r"(L\d+_switch_default:\n(?:[^\n]*\n)*(?=(?:L\d+:|$)))", txt)
    if default_block:
        assert re.search(r"^\s+goto L\d+_switch_end\s*$", default_block.group(1), flags=re.M)


# ---------------------------------------------------------------------------
# 4) Arrays declarativos → __new_array + Store por cada elemento
# ---------------------------------------------------------------------------
def test_array_literal_declarative_codegen():
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("arr", [])
    # Pipeline declarativo ('array', [...])
    gen_stmt(('assign', ('name', 'a'),
             ('array', [('const',10), ('const',20), ('const',30)])), ctx)
    ctx.end_function()

    calls_new = _find_calls(prog, "__new_array")
    assert len(calls_new) == 1 and len(calls_new[0].args) == 1, "Debe haber una sola reserva del array"
    stores = [ins for ins in _instrs_of(prog) if isinstance(ins, Store)]
    assert len(stores) == 3, "Debe haber un Store por elemento del literal de array"


# ---------------------------------------------------------------------------
# 5) arr[i] lectura y escritura con índices constantes y dinámicos
# ---------------------------------------------------------------------------
def test_index_read_write_static_and_dynamic_index():
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("ix", [])

    # a = ('array', [1,2])
    gen_stmt(('assign', ('name','a'), ('array', [('const',1), ('const',2)])), ctx)

    # x = a[1]
    gen_stmt(('assign', ('name','x'), ('index', ('name','a'), ('const',1))), ctx)

    # i = 0; y = a[i]; a[i] = 99
    gen_stmt(('assign', ('name','i'), ('const',0)), ctx)
    gen_stmt(('assign', ('name','y'), ('index', ('name','a'), ('name','i'))), ctx)
    gen_stmt(('assign', ('index', ('name','a'), ('name','i')), ('const', 99)), ctx)

    ctx.end_function()

    instrs = _instrs_of(prog)
    assert any(isinstance(x, Load)  for x in instrs), "Lectura arr[i] debe generar Load"
    assert any(isinstance(x, Store) for x in instrs), "Escritura arr[i] debe generar Store"


# ---------------------------------------------------------------------------
# 6) foreach desazucarado: usa __len__, while, Load y i = i + 1
# ---------------------------------------------------------------------------
def test_foreach_lowering_shape():
    # foreach (v in [7,8]) print(v);
    body = A.Block([A.PrintStmt(A.Identifier("v"))])
    fe = A.ForeachStmt(var_name="v", iterable=A.ArrayLiteral([A.IntLiteral(7), A.IntLiteral(8)]), body=body)

    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("fe", [])
    from src.ir.lower_from_ast import lower_stmt as LOWER
    gen_stmt(LOWER(fe), ctx)
    ctx.end_function()

    calls_len = _find_calls(prog, "__len__")
    assert calls_len, "foreach debe llamar a __len__ sobre el iterable"
    assert any(isinstance(x, Load) for x in _instrs_of(prog)), "foreach debe cargar arr[i] con Load"
    assert any(isinstance(x, BinOp) and x.op == '+' for x in _instrs_of(prog)), "foreach debe incrementar i"


# ---------------------------------------------------------------------------
# 7) Ternario: etiquetas then/else/end y asignación al mismo temp de salida
# ---------------------------------------------------------------------------
def test_ternary_codegen_structure():
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("tern", [])

    t = gen_expr(('tern', ('name','c'), ('const', 1), ('const', 2)), ctx)
    gen_stmt(('return', t), ctx)
    ctx.end_function()

    txt = program_to_str(prog)
    assert "then" in txt and "else" in txt and "end" in txt, "El ternario debe generar labels then/else/end"
    assigns = [ln for ln in txt.splitlines() if re.search(r"^\s*t\d+ = ", ln)]
    assert any("= 1" in a for a in assigns) and any("= 2" in a for a in assigns)


# ---------------------------------------------------------------------------
# 8) Propiedades: get/set generan GetProp/SetProp
# ---------------------------------------------------------------------------
def test_property_get_set():
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("props", [])

    # x = obj.p ; obj.p = 42
    gen_stmt(('assign', ('name','obj'), ('new','C',[])), ctx)
    gen_stmt(('assign', ('name','x'), ('prop', ('name','obj'), 'p')), ctx)
    gen_stmt(('assign', ('prop', ('name','obj'), 'p'), ('const', 42)), ctx)

    ctx.end_function()

    instrs = _instrs_of(prog)
    assert any(isinstance(i, GetProp) for i in instrs)
    assert any(isinstance(i, SetProp) for i in instrs)


# ---------------------------------------------------------------------------
# 9) Call devuelve en temp (dst no None)
# ---------------------------------------------------------------------------
def test_call_returns_temp():
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("callf", [])
    r = gen_expr(('call', 'foo', [('const', 1)]), ctx)
    gen_stmt(('return', r), ctx)
    ctx.end_function()

    calls = _find_calls(prog, "foo")
    assert calls and calls[0].dst is not None, "Las llamadas que retornan valor deben tener dst temp"


# ---------------------------------------------------------------------------
# 10) Pretty de constantes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("expr,frag", [
    (('const', "hola"), '"hola"'),
    (('const', True),   'true'),
    (('const', False),  'false'),
    (('const', None),   'null'),
])
def test_pretty_constants(expr, frag):
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=TempAllocator(), label_alloc=LabelAllocator())
    ctx.begin_function("pretty", [])
    v = gen_expr(expr, ctx)
    gen_stmt(('return', v), ctx)
    ctx.end_function()

    txt = program_to_str(prog)
    assert frag in txt


# ---------------------------------------------------------------------------
# 11) FrameLayout por función: offsets de params y locals sellados
# ---------------------------------------------------------------------------
def test_frame_layout_attached_in_adapter():
    adapter = IRAdapter.new()
    body = ('block', [('return',)])
    adapter.emit_function("ff", ["a", "b"], body, locals=["x", "y"])

    fl = adapter.frames.get("ff")
    assert fl is not None, "Debe existir FrameLayout para la función"
    # Params positivos (+8, +16, ...)
    assert fl.offset_of("a") == 8 and fl.offset_of("b") == 16
    # Locals negativos (-8, -16, ...)
    assert fl.offset_of("x") == -8 and fl.offset_of("y") == -16
