from src.ir.model import (
    Program, Function, BasicBlock, Label, Temp, Name, Const,
    Assign, BinOp, Return, LabelInstr
)
from src.ir.pretty import program_to_str

def test_pretty_minimal_function():
    fn = Function(name="suma", params=["a", "b"])
    bb = fn.new_block(Label("L0"))
    t0 = Temp("t0", "integer")
    a = Name("a", "integer")
    b = Name("b", "integer")
    bb.add(LabelInstr(Label("L0")))
    bb.add(BinOp(dst=t0, op="+", left=a, right=b))
    bb.add(Return(value=t0))

    prog = Program(functions=[fn])
    text = program_to_str(prog)

    expected = (
        "function suma(a, b):\n"
        "L0:\n"
        "  t0 = a + b\n"
        "  return t0"
    )
    assert text == expected
