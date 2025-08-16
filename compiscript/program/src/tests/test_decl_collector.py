# program/tests/test_decl_collector.py
from src.frontend.parser_util import parse_code
from src.sema.errors import ErrorReporter, E_DUPLICATE_ID, E_INHERIT_CYCLE, E_DUPLICATE_PARAM
from src.sema.decl_collector import DeclarationCollector
from src.sema.scopes import GlobalScope, ClassScope, FunctionScope
from src.sema.symbols import VariableSymbol, ConstSymbol, FunctionSymbol, ClassSymbol, FieldSymbol, ParamSymbol

def collect(code: str, expect_errors: int = 0):
    rep = ErrorReporter()
    _, tree = parse_code(code)
    dc = DeclarationCollector(rep)
    gscope = dc.visit(tree)
    assert isinstance(gscope, GlobalScope)
    if expect_errors == 0:
        assert not rep.has_errors(), rep.summary()
    else:
        assert len(rep.errors) == expect_errors, rep.summary()
    return dc, gscope, rep

def test_top_level_and_class_members():
    code = """
    const PI: integer = 314;
    let greeting: string;
    function foo(a: integer): integer { return a; }
    class Animal {
      let name: string;
      function speak(): string { return this.name; }
    }
    """
    dc, g, rep = collect(code)
    assert isinstance(g.resolve("PI"), ConstSymbol)
    assert isinstance(g.resolve("greeting"), VariableSymbol)
    assert isinstance(g.resolve("foo"), FunctionSymbol)
    animal = g.resolve("Animal"); assert isinstance(animal, ClassSymbol)
    # miembros de clase via class_scopes
    cs = dc.class_scopes["Animal"]; assert isinstance(cs, ClassScope)
    assert isinstance(cs.resolve("name"), FieldSymbol)
    assert isinstance(cs.resolve("speak"), FunctionSymbol)
    # parámetros en scope de función
    fnscope = dc.function_scopes["::foo"]; assert isinstance(fnscope, FunctionScope)
    assert isinstance(fnscope.resolve("a"), ParamSymbol)

def test_duplicate_ids_and_params():
    code = """
    let x: integer; let x: integer;
    function f(a: integer, a: integer) {}
    class C { let y: integer; let y: integer; }
    """
    dc, g, rep = collect(code, expect_errors=3)
    assert set(e.code for e in rep.errors) == {E_DUPLICATE_ID, E_DUPLICATE_PARAM}

def test_inheritance_cycle():
    code = """
    class A : B { }
    class B : A { }
    """
    dc, g, rep = collect(code, expect_errors=1)
    assert rep.errors[0].code == E_INHERIT_CYCLE

def test_constructor_flag():
    code = """
    class Dog {
      function constructor(name: string) { }
      function speak(): string { return "woof"; }
    }
    """
    dc, g, rep = collect(code)
    cs = dc.class_scopes["Dog"]
    ctor = cs.resolve("constructor"); speak = cs.resolve("speak")
    assert isinstance(ctor, FunctionSymbol) and ctor.is_constructor
    assert isinstance(speak, FunctionSymbol) and not speak.is_constructor
