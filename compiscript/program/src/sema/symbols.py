# program/src/sema/symbols.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

# Para anotar sin crear dependencias en tiempo de ejecución
if TYPE_CHECKING:
    from .types import Type, ClassType


@dataclass
class Symbol:
    name: str
    # Clase base genérica; las subclases fijan kind por defecto.
    kind: str = field(default="symbol")
    # Anotación textual del tipo (p. ej., "integer", "string[]", "Perro")
    type_ann: Optional[str] = None


@dataclass
class VariableSymbol(Symbol):
    kind: str = field(default="var", init=False)
    mutable: bool = True
    # Tipo resuelto (TypeLinker lo llena)
    resolved_type: Optional["Type"] = None


@dataclass
class ConstSymbol(Symbol):
    kind: str = field(default="const", init=False)
    mutable: bool = False
    resolved_type: Optional["Type"] = None


@dataclass
class ParamSymbol(Symbol):
    kind: str = field(default="param", init=False)
    resolved_type: Optional["Type"] = None


@dataclass
class FieldSymbol(Symbol):
    kind: str = field(default="field", init=False)
    resolved_type: Optional["Type"] = None


@dataclass
class FunctionSymbol(Symbol):
    kind: str = field(default="func", init=False)
    params: List[ParamSymbol] = field(default_factory=list)
    return_ann: Optional[str] = None
    is_method: bool = False
    is_constructor: bool = False
    # Retorno resuelto (TypeLinker lo llena)
    resolved_return: Optional["Type"] = None

    def signature(self) -> str:
        ps = ", ".join(p.type_ann if p.type_ann else "any" for p in self.params)
        ret = self.return_ann if self.return_ann else "void"
        return f"({ps}) -> {ret}"


@dataclass
class ClassSymbol(Symbol):
    kind: str = field(default="class", init=False)
    base_name: Optional[str] = None  # Nombre de la clase base, si existe
    # Clase base resuelta (TypeLinker la llena si existe y es válida)
    resolved_base_type: Optional["ClassType"] = None
