import pytest
from src.backend.mips.objects import LayoutRegistry

def test_inheritance_offsets_and_sizes_simple():
    layouts = LayoutRegistry()
    layouts.register_class("A", ["x", "y"])       # x=0, y=4
    layouts.register_class("B", ["z"], base="A")  # hereda x,y -> z=8
    layouts.build_all()

    # tamaños
    assert layouts.obj_size("A") == 8
    assert layouts.obj_size("B") == 12

    # offsets
    assert layouts.field_offset("x", "A") == 0
    assert layouts.field_offset("y", "A") == 4

    # en B, los heredados conservan offset
    assert layouts.field_offset("x", "B") == 0
    assert layouts.field_offset("y", "B") == 4
    # y su propio campo va después
    assert layouts.field_offset("z", "B") == 8

def test_inheritance_chain_three_levels():
    layouts = LayoutRegistry()
    layouts.register_class("A", ["a"])            # a=0
    layouts.register_class("B", ["b"], base="A")  # b=4
    layouts.register_class("C", ["c"], base="B")  # c=8
    layouts.build_all()

    assert layouts.obj_size("A") == 4
    assert layouts.obj_size("B") == 8
    assert layouts.obj_size("C") == 12

    assert layouts.field_offset("a", "C") == 0
    assert layouts.field_offset("b", "C") == 4
    assert layouts.field_offset("c", "C") == 8

def test_unknown_class_or_field():
    layouts = LayoutRegistry()
    layouts.register_class("A", ["x"])
    layouts.build_all()

    with pytest.raises(KeyError):
        layouts.obj_size("Nope")

    with pytest.raises(KeyError):
        layouts.field_offset("y", "A")  # no existe

def test_global_fallback_optional():
    # si no pasas class_name, puedes usar un orden global de campos
    layouts = LayoutRegistry()
    layouts.set_global_field_order(["x", "y", "z"])
    assert layouts.field_offset("y") == 4
    assert layouts.obj_size(None) == 12
