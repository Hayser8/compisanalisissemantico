# program/src/ir/tests_ir/test_regressions_ctx_arrays.py
import re

import pytest

from src.ir.adapter import IRAdapter
from src.ir.context import IRGenContext
from src.ir.model import Program, Name, Const, Temp, LabelInstr, Load, Store
from src.ir.pretty import program_to_str
from src.ir.gen_stmt import gen_stmt
from src.ir.gen_expr import gen_expr
from src.ir.lower_from_ast import lower_expr
from src.ir.temps import TempAllocator, LabelAllocator
from src.ast import nodes as A

# -----------------------------
# 1) "Memory leak" entre funciones (allocators no reseteados)
#    Este test ESPERA que t0/L0 se reinicien por función.
#    Con tu implementación actual, NO se reinician -> el test FALLA (evidencia el problema).
# -----------------------------
def test_allocators_should_reset_per_function_expected_behavior():
    adapter = IRAdapter.new()

    # Función 1: usa un binario para forzar un temp y un par de labels
    body1 = ('block', [
        ('expr', ('bin', '+', ('const', 1), ('const', 2))),
        ('return',),
    ])
    adapter.emit_function("f1", [], body1)

    # Función 2: misma estructura, debería "empezar de cero" si reseteamos allocators
    body2 = ('block', [
        ('expr', ('bin', '+', ('const', 3), ('const', 4))),
        ('return',),
    ])
    adapter.emit_function("f2", [], body2)

    txt = program_to_str(adapter.program)

    # Expectativa "ideal": que en cada función aparezca t0 (reinicio de temporales).
    f1_temps = re.findall(r"function f1\([^\)]*\):(.+?)function f2\(", txt, flags=re.S)
    f2_temps = re.findall(r"function f2\([^\)]*\):(.+)$", txt, flags=re.S)
    assert f1_temps, "No se encontró cuerpo de f1"
    assert f2_temps, "No se encontró cuerpo de f2"

    # En cada cuerpo debería existir al menos un temp y que sea t0
    assert "t0" in f1_temps[0], "Se esperaba que la f1 use t0 si el allocator se resetea por función"
    assert "t0" in f2_temps[0], "Se esperaba que la f2 vuelva a usar t0 (reset), pero parece que sigue creciendo"

# -----------------------------
# 2) Lowering de arrays debe ser DECLARATIVO
#    Con tu código actual, lower_expr(ArrayLiteral) -> ('call','__array__', [...])
#    El test espera ('array', [...]) -> FALLA y confirma el comentario del catedrático.
# -----------------------------
def test_lower_array_literal_should_be_declarative():
    # AST: [1,2,3]
    arr_ast = A.ArrayLiteral(elements=[
        A.IntLiteral(1),
        A.IntLiteral(2),
        A.IntLiteral(3),
    ])
    lowered = lower_expr(arr_ast)

    assert isinstance(lowered, tuple), "El lowering debe devolver una tupla"
    # Expectativa más declarativa para facilitar el backend MIPS:
    assert lowered and lowered[0] == 'array', (
        "Se esperaba ('array', [...]) en lugar de ('call','__array__',...) para arrays literales"
    )

# -----------------------------
# 3) Lectura y escritura arr[i] deben emitir Load/Store (esto DEBERÍA PASAR)
# -----------------------------
def _collect_instr_types(prog):
    kinds = []
    for fn in prog.functions:
        for bb in fn.blocks:
            for ins in bb.instrs:
                kinds.append(type(ins))
    return kinds

def test_index_read_and_write_emit_load_store():
    # Construimos un IR a mano: a = [10,20]; x = a[1]; a[0] = 99;
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=adapter_temp_alloc_fixture(), label_alloc=adapter_label_alloc_fixture())
    ctx.begin_function("main", params=[])

    # a = ('array', [10,20])  -> gen_expr emitirá __new_array + Store (ok para ahora)
    a_expr = ('array', [('const', 10), ('const', 20)])
    gen_stmt(('assign', ('name', 'a'), a_expr), ctx)

    # x = a[1]  -> Load
    read_expr = ('index', ('name', 'a'), ('const', 1))
    gen_stmt(('assign', ('name', 'x'), read_expr), ctx)

    # a[0] = 99 -> Store
    write_stmt = ('assign', ('index', ('name', 'a'), ('const', 0)), ('const', 99))
    gen_stmt(write_stmt, ctx)

    ctx.end_function()

    kinds = _collect_instr_types(prog)
    assert Load in kinds, "La lectura arr[i] debe emitir un Load"
    assert Store in kinds, "La escritura arr[i] debe emitir un Store"

# -----------------------------
# 4) end_function limpia current_function/current_block y el loop stack (DEBERÍA PASAR)
# -----------------------------
def test_end_function_clears_context_and_loop_stack():
    prog = Program()
    ctx = IRGenContext(program=prog, temp_alloc=adapter_temp_alloc_fixture(), label_alloc=adapter_label_alloc_fixture())

    ctx.begin_function("loopfn", params=[])
    # while(true) { break; }
    loop = ('while', ('const', True), ('block', [
        ('break',),
    ]))
    gen_stmt(loop, ctx)

    # Antes de cerrar, debe haber algo en el stack
    assert ctx._loop_stack == [], "El while usa push/pop y debe terminar vacío"
    ctx.end_function()
    assert ctx.current_function is None
    assert ctx.current_block is None
    assert ctx._loop_stack == []

# -----------------------------
# Helpers para tener allocators "limpios" en tests 3 y 4
# -----------------------------
from src.ir.temps import TempAllocator, LabelAllocator
def adapter_temp_alloc_fixture():
    return TempAllocator()
def adapter_label_alloc_fixture():
    return LabelAllocator()
