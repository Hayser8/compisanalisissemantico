# program/tests/test_scopes.py
from src.sema.scopes import (
    Scope, GlobalScope, ClassScope, FunctionScope, BlockScope, ScopeStack
)
from src.sema.symbols import VariableSymbol, ConstSymbol, FieldSymbol, ParamSymbol, FunctionSymbol, ClassSymbol

def test_global_declare_and_resolve():
    g = GlobalScope()
    v = VariableSymbol(name="x", type_ann="integer")
    f = FunctionSymbol(name="foo", return_ann="integer")
    assert g.declare(v) is True
    assert g.declare(f) is True
    assert g.resolve("x") is v
    assert g.resolve("foo") is f

def test_redeclaration_in_same_scope_fails():
    g = GlobalScope()
    assert g.declare(VariableSymbol(name="x", type_ann="integer")) is True
    assert g.declare(VariableSymbol(name="x", type_ann="integer")) is False  # misma tabla

def test_shadowing_in_child_scope():
    g = GlobalScope()
    assert g.declare(VariableSymbol(name="x", type_ann="integer")) is True
    fn = FunctionScope(name="f", parent=g)
    # sombrear x
    xv = VariableSymbol(name="x", type_ann="string")
    assert fn.declare(xv) is True
    assert fn.resolve("x") is xv           # local primero
    assert fn.resolve("x") is not g.resolve("x")
    # pero lo global sigue existiendo
    assert g.resolve("x") is not None

def test_chain_resolution_block_function_global():
    g = GlobalScope()
    g.declare(VariableSymbol(name="a", type_ann="integer"))
    fn = FunctionScope(name="f", parent=g)
    fn.declare(VariableSymbol(name="b", type_ann="integer"))
    blk = BlockScope(name="{b}", parent=fn)
    blk.declare(VariableSymbol(name="c", type_ann="integer"))

    # c en bloque
    assert blk.resolve("c").name == "c"
    # b en función
    assert blk.resolve("b").name == "b"
    # a en global
    assert blk.resolve("a").name == "a"
    # no existe z
    assert blk.resolve("z") is None

def test_class_scope_is_isolated_from_global():
    g = GlobalScope()
    dog_cls = ClassScope(name="Dog", parent=g)
    dog_cls.declare(FieldSymbol(name="name", type_ann="string"))
    # miembro solo en clase
    assert dog_cls.resolve("name").name == "name"
    assert g.resolve("name") is None

def test_scope_stack_push_pop_and_helpers():
    st = ScopeStack()  # tiene un GlobalScope dentro
    g = st.global_scope
    assert isinstance(g, GlobalScope)
    # entrar a clase
    c = st.enter_class("Animal")
    assert isinstance(st.current, ClassScope)
    # declarar campo
    assert st.current.declare(FieldSymbol(name="age", type_ann="integer")) is True
    # entrar a función
    f = st.enter_function("speak")
    assert isinstance(st.current, FunctionScope)
    # declarar param
    assert st.current.declare(ParamSymbol(name="vol", type_ann="integer")) is True
    # entrar a bloque
    b = st.enter_block()
    assert isinstance(st.current, BlockScope)
    # resolver a través de la cadena (param en función, campo en clase)
    assert st.current.resolve("vol").name == "vol"
    assert st.current.resolve("age").name == "age"
    # volver hacia arriba
    st.pop()  # block
    assert isinstance(st.current, FunctionScope)
    st.pop()  # function
    assert isinstance(st.current, ClassScope)
    st.pop()  # class
    assert isinstance(st.current, GlobalScope)
