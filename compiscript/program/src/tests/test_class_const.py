from src.sema.errors import E_ASSIGN_TO_CONST
from src.tests.test_typecheck_visitor import analyze, _codes

def test_const_field_in_class_is_immutable():
    code = """
    class C {
      const PI: integer;
      let v: integer;
    }
    let o: C = new C();
    o.PI = 3;   // debe fallar: const en clase
    o.v = 4;    // ok: mutable
    """
    rep = analyze(code)
    cs = _codes(rep)
    assert E_ASSIGN_TO_CONST in cs, rep.summary()
