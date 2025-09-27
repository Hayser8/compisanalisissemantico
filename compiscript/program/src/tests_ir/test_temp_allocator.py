from src.ir.temps import TempAllocator


def test_temp_recycle_basic():
    ta = TempAllocator()
    t0 = ta.new_temp()
    t1 = ta.new_temp()
    assert t0.name == "t0"
    assert t1.name == "t1"

    # Liberamos t0 y pedimos otro: debería reutilizar t0
    ta.free(t0)
    t2 = ta.new_temp()
    assert t2.name == "t0"  # reciclado

    # Si no liberamos t1, el siguiente nuevo será t2
    t3 = ta.new_temp()
    assert t3.name == "t2"
