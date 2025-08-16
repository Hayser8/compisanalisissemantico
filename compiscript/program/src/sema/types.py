# program/src/sema/types.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple


# -----------------------------
# Excepciones
# -----------------------------
class SemanticTypeError(TypeError):
    pass


# -----------------------------
# Tipos base
# -----------------------------
@dataclass(frozen=True)
class Type:
    name: str

    def __str__(self) -> str:
        return self.name

    # Subtipo: por defecto, exacto
    def is_subtype_of(self, other: "Type") -> bool:
        return self == other


@dataclass(frozen=True)
class PrimitiveType(Type):
    pass


@dataclass(frozen=True)
class VoidType(Type):
    pass


@dataclass(frozen=True)
class NullType(Type):
    # null es subtipo de tipos por-referencia (clase, arreglo, string)
    def is_subtype_of(self, other: "Type") -> bool:
        return isinstance(other, (ClassType, ArrayType, PrimitiveType)) and other in (STRING,) or isinstance(other, (ClassType, ArrayType))


@dataclass(frozen=True)
class ArrayType(Type):
    elem: Type
    rank: int = 1  # T[], T[][], ...

    def __post_init__(self):
        if self.rank < 1:
            raise ValueError("rank debe ser >= 1")

    def __str__(self) -> str:
        return f"{self.elem}{'[]' * self.rank}"

    def is_subtype_of(self, other: "Type") -> bool:
        # Arreglos invariantes por simplicidad
        return isinstance(other, ArrayType) and self.elem == other.elem and self.rank == other.rank


@dataclass(frozen=True)
class ClassType(Type):
    # Sólo el nombre identifica la clase (no modelamos jerarquía aquí)
    pass


@dataclass(frozen=True)
class FunctionType(Type):
    params: Tuple[Type, ...]
    ret: Type

    def __str__(self) -> str:
        ps = ", ".join(str(p) for p in self.params)
        return f"({ps}) -> {self.ret}"

    def is_subtype_of(self, other: "Type") -> bool:
        # Invariancia simple de funciones para este proyecto (sin co/contra-varianza)
        return isinstance(other, FunctionType) and self.params == other.params and self.ret == other.ret


# Singletons de primitivos
BOOLEAN = PrimitiveType("boolean")
INTEGER = PrimitiveType("integer")
FLOAT   = PrimitiveType("float")   # si aún no está en gramática, igual lo soportamos semánticamente
STRING  = PrimitiveType("string")
VOID    = VoidType("void")
NULL    = NullType("null")


# Utilidades
def is_numeric(t: Type) -> bool:
    return t in (INTEGER, FLOAT)

def unify_numeric(a: Type, b: Type) -> Type:
    if not (is_numeric(a) and is_numeric(b)):
        raise SemanticTypeError(f"Se esperaba tipos numéricos, recibidos: {a}, {b}")
    return FLOAT if FLOAT in (a, b) else INTEGER

def is_boolean(t: Type) -> bool:
    return t == BOOLEAN

def is_string(t: Type) -> bool:
    return t == STRING

def is_reference_like(t: Type) -> bool:
    return isinstance(t, (ArrayType, ClassType)) or is_string(t)


# -----------------------------
# Reglas de asignación
# -----------------------------
def is_assignable(src: Type, dst: Type) -> bool:
    # igualdad exacta
    if src == dst:
        return True
    # promoción numérica: integer -> float
    if src == INTEGER and dst == FLOAT:
        return True
    # null -> reference-like (clase, arreglo, string)
    if src == NULL and is_reference_like(dst):
        return True
    # por defecto, no asignable
    return False


# -----------------------------
# Operadores binarios y unarios
# -----------------------------
def result_add(a: Type, b: Type) -> Type:
    # Soportamos concatenación string + string (como en ejemplos)
    if is_string(a) and is_string(b):
        return STRING
    # Numérico
    return unify_numeric(a, b)

def result_sub(a: Type, b: Type) -> Type:
    return unify_numeric(a, b)

def result_mul(a: Type, b: Type) -> Type:
    return unify_numeric(a, b)

def result_div(a: Type, b: Type) -> Type:
    return unify_numeric(a, b)

def result_mod(a: Type, b: Type) -> Type:
    # Aceptamos % sobre numéricos (estilo TypeScript: numbers)
    return unify_numeric(a, b)

def result_logical_and(a: Type, b: Type) -> Type:
    if is_boolean(a) and is_boolean(b):
        return BOOLEAN
    raise SemanticTypeError(f"Operación lógica requiere boolean: {a}, {b}")

def result_logical_or(a: Type, b: Type) -> Type:
    if is_boolean(a) and is_boolean(b):
        return BOOLEAN
    raise SemanticTypeError(f"Operación lógica requiere boolean: {a}, {b}")

def result_logical_not(t: Type) -> Type:
    if is_boolean(t):
        return BOOLEAN
    raise SemanticTypeError(f"'!' requiere boolean, recibido: {t}")

def result_relational(a: Type, b: Type) -> Type:
    # <, <=, >, >=
    unify_numeric(a, b)
    return BOOLEAN

def result_equality(a: Type, b: Type) -> Type:
    # ==, !=  — aceptamos igualdad cuando:
    #   - tipos idénticos, o
    #   - ambos numéricos (int/float)
    if a == b:
        return BOOLEAN
    if is_numeric(a) and is_numeric(b):
        return BOOLEAN
    raise SemanticTypeError(f"Igualdad requiere tipos compatibles, recibidos: {a}, {b}")


# -----------------------------
# Arreglos
# -----------------------------
def array_of(elem: Type, rank: int = 1) -> ArrayType:
    return ArrayType(name="array", elem=elem, rank=rank)

def index_result(t_arr: Type, t_index: Type) -> Type:
    if not isinstance(t_arr, ArrayType):
        raise SemanticTypeError(f"Indexación requiere arreglo, recibido: {t_arr}")
    if t_index != INTEGER:
        raise SemanticTypeError(f"Índice debe ser integer, recibido: {t_index}")
    # Si queda una sola dimensión, retorna el elemento; si no, reduce el rank
    if t_arr.rank == 1:
        return t_arr.elem
    return ArrayType(name="array", elem=t_arr.elem, rank=t_arr.rank - 1)


# -----------------------------
# Funciones
# -----------------------------
def function_type(params: List[Type], ret: Type) -> FunctionType:
    return FunctionType(name="fn", params=tuple(params), ret=ret)

def call_result(fn: Type, args: List[Type]) -> Type:
    if not isinstance(fn, FunctionType):
        raise SemanticTypeError(f"Llamada requiere función, recibido: {fn}")
    if len(args) != len(fn.params):
        raise SemanticTypeError(f"Aridad inválida: se esperaban {len(fn.params)}, recibidos {len(args)}")
    for i, (arg_t, param_t) in enumerate(zip(args, fn.params)):
        if not is_assignable(arg_t, param_t):
            raise SemanticTypeError(f"Argumento {i} incompatible: {arg_t} → {param_t}")
    return fn.ret
