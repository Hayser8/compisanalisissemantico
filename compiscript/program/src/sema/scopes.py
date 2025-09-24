# program/src/sema/scopes.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Iterable, Tuple
from .symbols import Symbol

@dataclass
class Scope:
    """
    Scope genérico:
    - kind: 'global' | 'class' | 'function' | 'block'
    - parent: scope contenedor (cadena léxica)
    - _symbols: tabla local de símbolos
    """
    name: str
    kind: str
    parent: Optional["Scope"] = None
    _symbols: Dict[str, Symbol] = field(default_factory=dict)

    # Declaración local: False si ya existía en ESTE scope (prohibir redeclaración local)
    def declare(self, sym: Symbol) -> bool:
        if sym.name in self._symbols:
            return False
        self._symbols[sym.name] = sym
        return True
    
    # alias para legibilidad
    def lookup_current(self, name: str) -> Optional[Symbol]:
        return self.resolve_local(name)
    # Búsqueda local
    def resolve_local(self, name: str) -> Optional[Symbol]:
        return self._symbols.get(name)

    # Búsqueda en la cadena de scopes (sombras respetadas)
    def resolve(self, name: str) -> Optional[Symbol]:
        s: Optional[Scope] = self
        while s is not None:
            hit = s._symbols.get(name)
            if hit is not None:
                return hit
            s = s.parent
        return None

    def resolve_with_scope(self, name: str):
        s: Optional[Scope] = self
        while s is not None:
            hit = s._symbols.get(name)
            if hit is not None:
                return hit, s
            s = s.parent
        return None, None

    # Utilidades
    def __contains__(self, name: str) -> bool:
        return name in self._symbols

    def items(self) -> Iterable[Tuple[str, Symbol]]:
        return self._symbols.items()

    def __len__(self) -> int:
        return len(self._symbols)


class GlobalScope(Scope):
    def __init__(self) -> None:
        super().__init__(name="::global::", kind="global", parent=None)


class ClassScope(Scope):
    def __init__(self, name: str, parent: Scope) -> None:
        super().__init__(name=name, kind="class", parent=parent)


class FunctionScope(Scope):
    def __init__(self, name: str, parent: Scope) -> None:
        super().__init__(name=name, kind="function", parent=parent)


class BlockScope(Scope):
    def __init__(self, name: str, parent: Scope) -> None:
        super().__init__(name=name, kind="block", parent=parent)


class ScopeStack:
    """
    Pequeño helper para Visitors:
    - push/pop de scopes
    - acceso al scope actual
    - helpers para entrar a bloque/función/clase
    """
    def __init__(self, root: Optional[Scope] = None) -> None:
        self._stack = [root if root is not None else GlobalScope()]

    @property
    def current(self) -> Scope:
        return self._stack[-1]

    @property
    def global_scope(self) -> Scope:
        return self._stack[0]

    def push(self, scope: Scope) -> None:
        self._stack.append(scope)

    def pop(self) -> Scope:
        if len(self._stack) == 1:
            raise RuntimeError("No se puede hacer pop del global scope")
        return self._stack.pop()

    # Helpers de conveniencia
    def enter_block(self, name: str = "{block}") -> BlockScope:
        blk = BlockScope(name=name, parent=self.current)
        self.push(blk)
        return blk

    def enter_function(self, name: str) -> FunctionScope:
        fn = FunctionScope(name=name, parent=self.current)
        self.push(fn)
        return fn

    def enter_class(self, name: str) -> ClassScope:
        cl = ClassScope(name=name, parent=self.current)
        self.push(cl)
        return cl

    def current_function_scope(self) -> Optional[FunctionScope]:
        for s in reversed(self._stack):
            if isinstance(s, FunctionScope):
                return s
        return None

    def function_path(self) -> list[str]:
        return [s.name for s in self._stack if isinstance(s, FunctionScope)]
