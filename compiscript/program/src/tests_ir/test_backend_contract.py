import pytest
from src.ir.model import *
from src.backend.mips.validate import validate_program

def make_prog_ok():
    fn = Function("f", [])
    bb = fn.new_block(Label("L0"))
    t0 = Temp("t0")
    bb.add(LabelInstr(Label("L0")))
    bb.add(BinOp(dst=t0, op="+", left=Const(1), right=Const(2)))
    bb.add(Return(t0))
    return Program([fn])

def test_contract_ok():
    validate_program(make_prog_ok())

def test_reject_unknown_instr():
    class Weird(Instr): pass
    p = make_prog_ok()
    p.functions[0].blocks[0].add(Weird())
    with pytest.raises(ValueError):
        validate_program(p)

def test_assign_dst_must_be_temp_or_name():
    p = make_prog_ok()
    p.functions[0].blocks[0].add(Assign(dst=Const(0), src=Const(1)))
    with pytest.raises(ValueError):
        validate_program(p)

def test_index_must_be_int_like():
    p = make_prog_ok()
    bb = p.functions[0].blocks[0]
    t0 = Temp("t1")
    arr = Temp("t2")
    bb.add(Load(dst=t0, array=arr, index=Const(1.5)))  # float -> inválido
    with pytest.raises(ValueError):
        validate_program(p)
