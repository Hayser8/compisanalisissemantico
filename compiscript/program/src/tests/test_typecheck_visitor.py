# program/tests/test_typecheck.py
from src.frontend.parser_util import parse_code
from src.sema.errors import (
    ErrorReporter,
    E_UNDECLARED, E_ASSIGN_INCOMPAT, E_OP_TYPES, E_CALL_ARITY, E_INDEX_INVALID,
    E_MEMBER_NOT_FOUND, E_THIS_CONTEXT, E_BAD_BREAK_CONTINUE, E_COND_NOT_BOOL,
    E_RETURN_OUTSIDE, E_MISSING_RETURN, E_ASSIGN_TO_CONST, E_DEAD_CODE
)
from src.sema.decl_collector import DeclarationCollector
from src.sema.type_linker import TypeLinker
from src.sema.typecheck_visitor import TypeCheckVisitor

def analyze(code: str):
    rep = ErrorReporter()
    _, tree = parse_code(code)
    dc = DeclarationCollector(rep)
    dc.visit(tree)
    TypeLinker(rep, dc).link()
    tc = TypeCheckVisitor(rep, dc)
    tc.visit(tree)
    return rep

def _codes(rep): return [e.code for e in rep.errors]

# ---------- Positivos ----------

def test_ok_assign_and_calls_and_arrays():
    code = """
    let a: integer; a = 3;
    let b: float; b = a;          // promoción int->float
    function sum(x: integer, y: integer): integer { return x + y; }
    let r: integer; r = sum(a, 2);
    let xs: integer[] = [1,2,3];
    let x0: integer = xs[0];
    class A { let v: integer; function get(): integer { return this.v; } }
    let o: A = new A();
    """
    rep = analyze(code)
    assert not rep.has_errors(), rep.summary()

# ---------- Negativos por ámbitos/nombres ----------

def test_undeclared_variable_and_member():
    code = """
    y = 1;                // uso sin declarar
    class A { }
    let o: A = new A();
    o.x = 2;              // miembro no existe
    """
    rep = analyze(code)
    cs = _codes(rep)
    assert E_UNDECLARED in cs
    assert E_MEMBER_NOT_FOUND in cs

# ---------- Operadores / tipos ----------

def test_cond_not_boolean_and_op_types():
    code = """
    let s: string = "hi";
    if (s) { }            // condición no booleana
    let a: integer; a = 1;
    let t: string; t = s + s; // ok
    let bad: integer; bad = s + s; // incompatible
    """
    rep = analyze(code)
    cs = _codes(rep)
    assert E_COND_NOT_BOOL in cs
    assert E_ASSIGN_INCOMPAT in cs

# ---------- Retornos / flujo ----------

def test_return_outside_and_missing_return_and_dead_code():
    code = """
    return 1;  // fuera de función
    function f(a: integer): integer {
      if (a > 0) { return a; }
      // falta return en else
    }
    function g(): integer {
      return 1;
      let z: integer = 5;  // dead code
    }
    """
    rep = analyze(code)
    cs = _codes(rep)
    assert E_RETURN_OUTSIDE in cs
    assert E_MISSING_RETURN in cs
    assert E_DEAD_CODE in cs

# ---------- break/continue ----------

def test_break_continue_invalid():
    code = """
    break;
    continue;
    while (true) { break; continue; }
    """
    rep = analyze(code)
    cs = _codes(rep)
    # los dos primeros inválidos, los de dentro del while válidos
    assert cs.count(E_BAD_BREAK_CONTINUE) >= 2

# ---------- this / métodos / constructor ----------

def test_this_and_constructor_and_calls():
    code = """
    class C { 
      let n: integer; 
      function constructor(n: integer) { this.n = n; }
      function get(): integer { return this.n; }
    }
    let c: C = new C(1);
    let k: integer = c.get();
    let c2: C = new C("x");   // tipo incorrecto en ctor
    """
    rep = analyze(code)
    cs = _codes(rep)
    assert E_OP_TYPES in cs or E_CALL_ARITY in cs  # cualquiera de los dos por el ctor
    # 'this' siempre usado dentro de método: no debe dar error E_THIS_CONTEXT

def test_this_outside_method():
    code = """
    let a: integer;
    this = a;   // uso de this fuera de método
    """
    rep = analyze(code)
    assert E_THIS_CONTEXT in _codes(rep)

# ---------- arrays (índices y asignaciones) ----------

def test_array_index_and_assign_incompat():
    code = """
    let xs: integer[] = [1,2,3];
    xs["a"] = 1;         // índice inválido
    xs[0] = "z";         // incompatible
    """
    rep = analyze(code)
    cs = _codes(rep)
    assert E_INDEX_INVALID in cs
    assert E_ASSIGN_INCOMPAT in cs

# ---------- const re-assign ----------

def test_const_reassign():
    code = """
    const PI: integer = 314;
    PI = 3;   // no se puede
    """
    rep = analyze(code)
    assert E_ASSIGN_TO_CONST in _codes(rep)

def test_float_literal_and_promotion_and_forbidden_float_to_int():
    code = """
    let f: float = 1.25;
    let i: integer = 5;
    i = f;                 // no permitido: float -> integer
    let f2: float = i;     // permitido: int -> float (promoción)
    let g: float = 12e-1;  // literal con exponente
    let h: float = 12.0;   // literal con punto
    let k = 1.0 + i;       // inferencia: float
    """
    rep = analyze(code)
    cs = _codes(rep)
    # Debe existir al menos la incompatibilidad por i = f
    assert E_ASSIGN_INCOMPAT in cs, rep.summary()

def test_mod_with_float_is_allowed_by_rules():
    code = """
    let r: float = 5.0 % 2;
    """
    rep = analyze(code)
    assert not rep.has_errors(), rep.summary()

def test_switch_condition_must_be_boolean():
    code = """
    switch (1) {
      case 1:
        let a: integer; a = 0;
      default:
        let b: integer; b = 1;
    }
    """
    rep = analyze(code)
    assert E_COND_NOT_BOOL in _codes(rep), rep.summary()

def test_switch_boolean_condition_ok():
    code = """
    switch (true) {
      case true:
        let a: integer; a = 1;
      default:
        let b: integer; b = 2;
    }
    """
    rep = analyze(code)
    assert not rep.has_errors(), rep.summary()

def test_nested_function_call_and_return_and_capture():
    code = """
    function outer(a: integer): integer {
      let x: integer = 10;
      function inner(b: integer): integer {
        return a + x + b;
      }
      return inner(5);
    }
    """
    rep = analyze(code)
    assert not rep.has_errors(), rep.summary()