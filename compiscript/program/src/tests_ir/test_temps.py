from src.ir.temps import TempAllocator, LabelAllocator
from src.ir.model import Temp, Label


def test_temp_allocator_basic_sequence():
    ta = TempAllocator()
    t0 = ta.new_temp("integer")
    t1 = ta.new_temp("integer")
    t2 = ta.new_temp("float")

    assert t0.name == "t0"
    assert t1.name == "t1"
    assert t2.name == "t2"
    assert t0.type_hint == "integer"
    assert t2.type_hint == "float"


def test_temp_allocator_reuse_after_release():
    ta = TempAllocator()
    t0 = ta.new_temp("integer")
    t1 = ta.new_temp("integer")
    t2 = ta.new_temp("float")

    # Libero t1 y t2; el reciclaje es LIFO, así que reutiliza t2 primero
    ta.release(t1)
    ta.release(t2)

    r0 = ta.new_temp("boolean")
    r1 = ta.new_temp("string")
    r2 = ta.new_temp("integer")

    # r0 debe reutilizar el nombre de t2, r1 el de t1, r2 es nuevo t3
    assert r0.name == "t2" and r0.type_hint == "boolean"
    assert r1.name == "t1" and r1.type_hint == "string"
    assert r2.name == "t3" and r2.type_hint == "integer"


def test_temp_allocator_double_free_is_ignored():
    ta = TempAllocator()
    t0 = ta.new_temp()
    ta.release(t0)
    ta.release(t0)  # Ignorado

    r0 = ta.new_temp()
    r1 = ta.new_temp()

    # r0 debe reutilizar t0; r1 debe ser t1
    assert r0.name == t0.name
    assert r1.name == "t1"


def test_label_allocator_sequence_and_suffix():
    la = LabelAllocator()
    l0 = la.new_label()
    l1 = la.new_label("then")
    l2 = la.new_label("end")
    l3 = la.new_label()

    assert l0.name == "L0"
    assert l1.name == "L1_then"
    assert l2.name == "L2_end"
    assert l3.name == "L3"
