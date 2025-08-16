# program/tests/test_symbols.py
from src.sema.symbols import (
    Symbol,
    VariableSymbol, ConstSymbol, ParamSymbol, FieldSymbol,
    FunctionSymbol, ClassSymbol
)

def test_variable_symbol_defaults():
    v = VariableSymbol(name="x", type_ann="integer")
    assert v.name == "x"
    assert v.kind == "var"
    assert v.mutable is True
    assert v.type_ann == "integer"

def test_const_symbol_defaults():
    c = ConstSymbol(name="PI", type_ann="integer")
    assert c.kind == "const"
    assert c.mutable is False
    assert c.type_ann == "integer"

def test_param_and_field_symbols():
    p = ParamSymbol(name="n", type_ann="integer")
    f = FieldSymbol(name="name", type_ann="string")
    assert p.kind == "param"
    assert f.kind == "field"
    assert p.type_ann == "integer"
    assert f.type_ann == "string"

def test_function_symbol_signature_and_flags():
    fn = FunctionSymbol(name="sumar", return_ann="integer")
    fn.params.append(ParamSymbol(name="a", type_ann="integer"))
    fn.params.append(ParamSymbol(name="b", type_ann="integer"))
    assert fn.kind == "func"
    assert fn.signature() == "(integer, integer) -> integer"
    # Flags
    m = FunctionSymbol(name="speak", is_method=True, return_ann="string")
    assert m.is_method is True and m.is_constructor is False
    ctor = FunctionSymbol(name="constructor", is_method=True, is_constructor=True)
    assert ctor.is_method is True and ctor.is_constructor is True

def test_class_symbol_with_base():
    dog = ClassSymbol(name="Dog", base_name="Animal")
    assert dog.kind == "class"
    assert dog.name == "Dog"
    assert dog.base_name == "Animal"

def test_equality_by_dataclass_values():
    v1 = VariableSymbol(name="x", type_ann="integer")
    v2 = VariableSymbol(name="x", type_ann="integer")
    assert v1 == v2  # dataclass equality por campos
