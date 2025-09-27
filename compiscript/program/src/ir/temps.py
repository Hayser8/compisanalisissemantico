from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Optional

from .model import Temp, Label


class TempAllocator:
    """
    Asignador de temporales con reciclaje simple (free-list).

    - new_temp(type_hint) -> Temp   : Entrega un Temp disponible.
      * Si hay nombres liberados, los reutiliza (LIFO).
      * Si no hay, crea un nombre nuevo t<N>.
    - release(Temp)                 : Marca el nombre del Temp como reutilizable.

    Notas:
    - El type_hint se adjunta al Temp retornado, pero el reciclaje no
      intenta compatibilizar por tipo (lo mantiene simple, el generador
      decide cuándo liberar).
    - Evita 'double-free' del mismo nombre con un set de control.
    """

    def __init__(self, prefix: str = "t") -> None:
        self.prefix = prefix
        self._next_id: int = 0
        self._free: List[str] = []
        self._free_set: Set[str] = set()

    def _fresh_name(self) -> str:
        name = f"{self.prefix}{self._next_id}"
        self._next_id += 1
        return name

    def new_temp(self, type_hint: Optional[str] = None) -> Temp:
        if self._free:
            name = self._free.pop()
            self._free_set.remove(name)
            return Temp(name=name, type_hint=type_hint)
        return Temp(name=self._fresh_name(), type_hint=type_hint)

    def release(self, temp: Temp) -> None:
        name = temp.name
        # Evitar doble liberación del mismo identificador
        if name not in self._free_set:
            self._free.append(name)
            self._free_set.add(name)

    def reset(self) -> None:
        """Reinicia el allocator (útil en tests)."""
        self._next_id = 0
        self._free.clear()
        self._free_set.clear()


class LabelAllocator:
    """
    Generador simple de etiquetas: L0, L1, ...

    - new_label(suffix=None) -> Label
      * Si 'suffix' se provee, genera 'L<N>_<suffix>' para facilitar lectura.
    """

    def __init__(self, prefix: str = "L") -> None:
        self.prefix = prefix
        self._next_id: int = 0

    def new_label(self, suffix: Optional[str] = None) -> Label:
        base = f"{self.prefix}{self._next_id}"
        self._next_id += 1
        if suffix:
            return Label(f"{base}_{suffix}")
        return Label(base)

    def reset(self) -> None:
        self._next_id = 0
