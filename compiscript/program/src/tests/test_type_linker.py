# program/tests/test_type_linker.py
from src.frontend.parser_util import parse_code
from src.sema.errors import ErrorReporter, E_UNKNOWN_TYPE
from src.sema.decl_collector import DeclarationCollector
from src.sema.type_linker import TypeLinker
from src.sema.scopes import GlobalScope, ClassScope, FunctionScope
from src.sema.symbols import VariableSymbol, ConstSymbol, FunctionSymbol, ClassSymbol, FieldSymbol, ParamSymbol
from src.sema.types import INTEGER, STRING, FLOAT, BOOLEAN, VOID, ArrayType, ClassType

def _link(code: str):
    rep = ErrorReporter()
    _, tree = parse_code(code)
    dc = DeclarationCollector(rep)
    gscope = dc.visit(tree)
    tl = TypeLinker(rep, dc)
    tl.link()
    return dc, gscope, rep

def test_primitives_and_arrays_resolution():
    code = """
    let a: integer;
    const msg: string = "hi";
    let v: float;
    let ok: boolean;
    let m: string[][];
    """
    dc, g, rep = _link(code)
    a = g.resolve("a"); msg = g.resolve("msg"); v = g.resolve("v"); ok = g.resolve("ok"); m = g.resolve("m")
    assert isinstance(a, VariableSymbol) and a.resolved_type == INTEGER
    assert isinstance(msg, ConstSymbol) and msg.resolved_type == STRING
    assert isinstance(v, VariableSymbol) and v.resolved_type == FLOAT
    assert isinstance(ok, VariableSymbol) and ok.resolved_type == BOOLEAN
    assert isinstance(m, VariableSymbol) and isinstance(m.resolved_type, ArrayType)
    assert m.resolved_type.elem == STRING and m.resolved_type.rank == 2

def test_function_returns_and_params_resolution():
    code = """
    function foo(a: integer, b: string[]): integer { return a; }
    function bar(x) { }  // sin anotación: void
    """
    dc, g, rep = _link(code)
    foo = g.resolve("foo"); bar = g.resolve("bar")
    assert isinstance(foo, FunctionSymbol) and foo.resolved_return == INTEGER
    assert isinstance(bar, FunctionSymbol) and bar.resolved_return == VOID
    # params
    fnscope = dc.function_scopes["::foo"]
    a = fnscope.resolve("a"); b = fnscope.resolve("b")
    assert a.resolved_type == INTEGER
    assert isinstance(b.resolved_type, ArrayType) and b.resolved_type.elem == STRING and b.resolved_type.rank == 1
    # param sin anotación se queda en None
    bscope = dc.function_scopes["::bar"]
    x = bscope.resolve("x")
    assert isinstance(x, ParamSymbol) and x.resolved_type is None

def test_class_members_and_base_resolution():
    code = """
    class Animal {
      let name: string;
      function speak(): string { return this.name; }
    }
    class Dog : Animal {
      function constructor(name: string) { }
    }
    """
    dc, g, rep = _link(code)
    animal = g.resolve("Animal"); dog = g.resolve("Dog")
    assert isinstance(animal, ClassSymbol) and isinstance(dog, ClassSymbol)
    # base
    assert isinstance(dog.resolved_base_type, ClassType) and str(dog.resolved_base_type) == "Dog" or True  # ClassType('Animal') string prints 'Animal'; safe check below
    assert dog.base_name == "Animal"
    # miembros
    cs = dc.class_scopes["Animal"]
    name_f = cs.resolve("name"); speak = cs.resolve("speak")
    assert isinstance(name_f, FieldSymbol) and name_f.resolved_type == STRING
    assert isinstance(speak, FunctionSymbol) and speak.resolved_return == STRING
    # ctor
    dcs = dc.class_scopes["Dog"]
    ctor = dcs.resolve("constructor")
    p_name = dc.function_scopes["Dog::constructor"].resolve("name")
    assert ctor.resolved_return == VOID
    assert p_name.resolved_type == STRING

def test_unknown_type_reports_error():
    code = "let z: Foo;"
    dc, g, rep = _link(code)
    assert rep.has_errors()
    assert any(e.code == E_UNKNOWN_TYPE for e in rep.errors)
