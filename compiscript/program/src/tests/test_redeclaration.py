from src.sema.errors import E_DUPLICATE_ID, E_OP_TYPES, E_COND_NOT_BOOL
# Reusamos el helper del propio repo para analizar código
from src.tests.test_switch_strings import _analyze  # ya existe en tu suite

def _codes(rep):
    return [e.code for e in rep.errors]

def test_no_shadow_in_block():
    src = r'''
        var x: integer = 10;
        {
            let x: integer; x = 20;  // redeclaración en scope interno -> prohibida
        }
    '''
    rep, _ = _analyze(src)
    assert E_DUPLICATE_ID in _codes(rep), rep.summary()

def test_switch_condition_integer_emits_both_errors():
    # Si la condición no es ni boolean ni string, emitimos ambos errores
    src = r'''
        var x: integer = 10;
        switch (x) {
          case "a": { }
        }
    '''
    rep, _ = _analyze(src)
    msgs = [e.message for e in rep.errors]
    has_bool_err = any(e.code == E_COND_NOT_BOOL and "switch requiere 'boolean'" in e.message for e in rep.errors)
    has_str_err  = any(e.code == E_OP_TYPES and "switch requiere 'string'" in e.message for e in rep.errors)
    assert has_bool_err and has_str_err, rep.summary()

def test_switch_boolean_ok():
    src = r'''
        switch (true) {
          case true: { }
          default: { }
        }
    '''
    rep, _ = _analyze(src)
    assert not rep.has_errors(), rep.summary()

def test_switch_string_ok_and_duplicates():
    src = r'''
        switch ("a") {
          case "a": { }
          case "a": { }   // duplicado
          default: { }
        }
    '''
    rep, _ = _analyze(src)
    # Debe haber al menos un duplicado
    assert any(e.code == E_DUPLICATE_ID and 'Etiqueta de case duplicada' in e.message for e in rep.errors), rep.summary()
