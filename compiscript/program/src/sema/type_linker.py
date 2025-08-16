# program/src/sema/type_linker.py
from __future__ import annotations
from typing import Optional

from .errors import ErrorReporter, E_UNKNOWN_TYPE
from .symbols import (
    VariableSymbol, ConstSymbol, ParamSymbol, FieldSymbol, FunctionSymbol, ClassSymbol
)
from .scopes import Scope
from . import symbols as symmod  # para acceder a tipos resueltos en los símbolos (atributos)
from .types import (
    BOOLEAN, INTEGER, FLOAT, STRING, VOID,
    ClassType, ArrayType, array_of, Type
)
from .decl_collector import DeclarationCollector


class TypeLinker:
    """
    Pasada 2: Resolver anotaciones de tipo → objetos Type.
    - Variables, consts, campos, parámetros, returns de funciones/métodos
    - Clases base (Dog : Animal) → valida existencia y resuelve a ClassType
    - Reporta E_UNKNOWN_TYPE cuando el identificador de tipo no existe como clase
    """
    def __init__(self, reporter: ErrorReporter, decl: DeclarationCollector) -> None:
        self.reporter = reporter
        self.decl = decl
        self.global_scope: Scope = decl.global_scope

    # ------------------ API principal ------------------
    def link(self) -> None:
        # Top-level
        for _, sym in self.global_scope.items():
            if isinstance(sym, (VariableSymbol, ConstSymbol)):
                if sym.type_ann:
                    sym.resolved_type = self._parse_type_str(sym.type_ann)
            elif isinstance(sym, FunctionSymbol):
                sym.resolved_return = self._resolve_return(sym.return_ann)
            elif isinstance(sym, ClassSymbol):
                # Resolver base
                if sym.base_name:
                    base_sym = self.global_scope.resolve(sym.base_name)
                    if not isinstance(base_sym, ClassSymbol):
                        # usar ctx de la clase si está disponible en decl
                        ctx = self.decl.class_nodes.get(sym.name)
                        self.reporter.error(E_UNKNOWN_TYPE, f"Clase base desconocida: {sym.base_name}", ctx=ctx)
                    else:
                        sym.resolved_base_type = ClassType(sym.base_name)

        # Clases: miembros (campos y métodos)
        for cname, cscope in self.decl.class_scopes.items():
            for _, ms in cscope.items():
                if isinstance(ms, FieldSymbol):
                    if ms.type_ann:
                        ms.resolved_type = self._parse_type_str(ms.type_ann)
                elif isinstance(ms, FunctionSymbol):
                    ms.resolved_return = self._resolve_return(ms.return_ann)

        # Parámetros: funciones top-level y métodos (usamos los function_scopes recolectados)
        for key, fnscope in self.decl.function_scopes.items():
            for _, ps in fnscope.items():
                if isinstance(ps, ParamSymbol) and ps.type_ann:
                    ps.resolved_type = self._parse_type_str(ps.type_ann)

    # ------------------ Helpers ------------------
    def _resolve_return(self, ann: Optional[str]) -> Type:
        # Sin anotación → void
        if not ann:
            return VOID
        return self._parse_type_str(ann)

    def _parse_type_str(self, s: str) -> Type:
        """
        Convierte 'integer', 'string[]', 'Animal[][]' en objetos Type.
        Valida que identificadores de clase existan como ClassSymbol.
        """
        base = s
        rank = 0
        # contar sufijos []
        while base.endswith("[]"):
            base = base[:-2]
            rank += 1

        base_l = base  # compiscript es case-sensitive por default; no forzamos lower
        prim = self._map_primitive(base_l)
        if prim is not None:
            t: Type = prim
        else:
            # Debe ser una clase declarada
            csym = self.global_scope.resolve(base_l)
            if not isinstance(csym, ClassSymbol):
                self.reporter.error(E_UNKNOWN_TYPE, f"Tipo desconocido: {base_l}")
                # Continuamos para no frenar toda la pasada
                t = ClassType(base_l)
            else:
                t = ClassType(base_l)

        if rank > 0:
            t = array_of(t, rank)
        return t

    def _map_primitive(self, name: str) -> Optional[Type]:
        if name == "integer":
            return INTEGER
        if name == "string":
            return STRING
        if name == "boolean":
            return BOOLEAN
        if name == "float":
            return FLOAT
        if name == "void":
            return VOID
        return None
