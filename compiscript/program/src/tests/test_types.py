# program/tests/test_types.py
import pytest
from src.sema.types import (
    BOOLEAN, INTEGER, FLOAT, STRING, NULL, VOID,
    ArrayType, ClassType,
    is_assignable, array_of, index_result,
    result_add, result_sub, result_mul, result_div, result_mod,
    result_logical_and, result_logical_or, result_logical_not,
    result_relational, result_equality,
    function_type, call_result, SemanticTypeError
)

# ---------- Aritmética ----------
def test_add_int_int_is_int():
    assert result_add(INTEGER, INTEGER) == INTEGER

def test_add_int_float_is_float():
    assert result_add(INTEGER, FLOAT) == FLOAT
    assert result_add(FLOAT, INTEGER) == FLOAT

def test_add_string_string_is_string():
    assert result_add(STRING, STRING) == STRING

def test_add_string_int_raises():
    with pytest.raises(SemanticTypeError):
        result_add(STRING, INTEGER)

def test_mul_float_int_is_float():
    assert result_mul(FLOAT, INTEGER) == FLOAT

def test_div_int_int_is_int_or_float():
    # En nuestro sistema, números unificados → int si ambos int, sino float
    assert result_div(INTEGER, INTEGER) == INTEGER
    assert result_div(INTEGER, FLOAT) == FLOAT

def test_mod_numeric_ok():
    assert result_mod(INTEGER, INTEGER) == INTEGER
    assert result_mod(FLOAT, INTEGER) == FLOAT

# ---------- Lógicas ----------
def test_logical_and_boolean_ok():
    assert result_logical_and(BOOLEAN, BOOLEAN) == BOOLEAN

def test_logical_and_raises_on_non_boolean():
    with pytest.raises(SemanticTypeError):
        result_logical_and(BOOLEAN, INTEGER)

def test_logical_not_ok():
    assert result_logical_not(BOOLEAN) == BOOLEAN

# ---------- Comparaciones ----------
def test_relational_numeric_ok():
    assert result_relational(INTEGER, FLOAT) == BOOLEAN

def test_relational_raises_on_string():
    with pytest.raises(SemanticTypeError):
        result_relational(STRING, STRING)

def test_equality_same_type_ok():
    assert result_equality(STRING, STRING) == BOOLEAN

def test_equality_numeric_cross_ok():
    assert result_equality(INTEGER, FLOAT) == BOOLEAN

def test_equality_incompatible_raises():
    with pytest.raises(SemanticTypeError):
        result_equality(STRING, INTEGER)

# ---------- Asignación ----------
def test_assign_same_type_ok():
    assert is_assignable(STRING, STRING)

def test_assign_int_to_float_promotion_ok():
    assert is_assignable(INTEGER, FLOAT)

def test_assign_float_to_int_fails():
    assert not is_assignable(FLOAT, INTEGER)

def test_assign_null_to_array_ok():
    assert is_assignable(NULL, array_of(INTEGER))

def test_assign_null_to_string_ok():
    assert is_assignable(NULL, STRING)

def test_assign_null_to_int_fails():
    assert not is_assignable(NULL, INTEGER)

# ---------- Arreglos ----------
def test_array_invariance():
    a_int = array_of(INTEGER)
    a_float = array_of(FLOAT)
    assert not is_assignable(a_int, a_float)
    assert not is_assignable(a_float, a_int)

def test_index_access_ok():
    a = array_of(STRING, rank=2)
    # a[i] : STRING[]
    t = index_result(a, INTEGER)
    assert isinstance(t, ArrayType)
    assert t.elem == STRING and t.rank == 1

def test_index_access_bad_index():
    with pytest.raises(SemanticTypeError):
        index_result(array_of(INTEGER), STRING)

# ---------- Funciones ----------
def test_function_type_and_call_ok():
    fn = function_type([INTEGER, FLOAT], STRING)
    assert call_result(fn, [INTEGER, FLOAT]) == STRING
    # Promoción int -> float en el segundo arg NO aplica porque comparamos asignabilidad:
    # INTEGER no asigna a FLOAT? Sí, int -> float permitido. Probamos:
    assert call_result(fn, [INTEGER, INTEGER]) == STRING  # segundo int se promociona a float

def test_function_call_arity_mismatch():
    fn = function_type([INTEGER], VOID)
    with pytest.raises(SemanticTypeError):
        call_result(fn, [])

def test_function_call_type_mismatch():
    fn = function_type([STRING], VOID)
    with pytest.raises(SemanticTypeError):
        call_result(fn, [INTEGER])
