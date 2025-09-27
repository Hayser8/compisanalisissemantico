from src.ir.adapter import IRAdapter
from src.ir.pretty import program_to_str

def test_frame_attached_to_function():
    # function f(a, b) { return; } con locales x, y, z
    adapter = IRAdapter.new()
    body = ('block', [('return',)])
    adapter.emit_function("f", ["a", "b"], body, locals=["x", "y", "z"])

    # IR sigue intacto
    txt = program_to_str(adapter.program)
    expected = (
        "function f(a, b):\n"
        "L0:\n"
        "  return"
    )
    assert txt == expected

    # Y tenemos frame con offsets esperados
    fr = adapter.frames["f"]
    # Params: +8, +16
    assert fr.offset_of("a") == 8
    assert fr.offset_of("b") == 16
    # Locals: -8, -16, -24
    assert fr.offset_of("x") == -8
    assert fr.offset_of("y") == -16
    assert fr.offset_of("z") == -24
    # Tamaño de la zona de locals
    assert fr.frame_size_bytes() == 24
