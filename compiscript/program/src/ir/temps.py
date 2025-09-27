# program/src/ir/temps.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from .model import Temp, Label


@dataclass
class TempAllocator:
    """
    Asignador de temporales con reciclaje (free-list).

    - new_temp(type_hint) -> Temp
        * Reutiliza IDs liberados (LIFO) si existen.
        * Si no hay, crea un nombre nuevo t<N>.
    - free(Temp) -> None
        * Marca el temporal como disponible para reutilización.
    - release(Temp) -> None
        * Alias de free(...) por compatibilidad.

    Nota: no hacemos tracking de tipos en el reciclaje (simple).
    """
    _next_id: int = 0
    _free: List[int] = None  # inicializado en __post_init__

    def __post_init__(self) -> None:
        if self._free is None:
            self._free = []

    def new_temp(self, type_hint: Optional[str] = None) -> Temp:
        if self._free:
            tid = self._free.pop()
            return Temp(name=f"t{tid}", type_hint=type_hint)
        tid = self._next_id
        self._next_id += 1
        return Temp(name=f"t{tid}", type_hint=type_hint)

    def free(self, t: Temp) -> None:
        """
        Libera el ID del temp para que pueda reutilizarse.
        Seguridad básica: sólo acepta nombres 't<numero>'.
        Evita duplicados en la free-list y no reintroduce IDs que no existieron.
        """
        n = getattr(t, "name", "")
        if not isinstance(n, str) or not n.startswith("t"):
            return
        try:
            tid = int(n[1:])
        except Exception:
            return
        # sólo IDs ya emitidos y no repetidos
        if 0 <= tid < self._next_id and tid not in self._free:
            self._free.append(tid)

    # Alias por compatibilidad con versiones previas
    def release(self, t: Temp) -> None:
        self.free(t)

    def reset(self) -> None:
        """Reinicia el allocator (útil en tests)."""
        self._next_id = 0
        self._free.clear()


@dataclass
class LabelAllocator:
    """
    Generador simple de etiquetas: L0, L1, ...
    new_label('hint') -> L<N>_hint
    """
    _next_id: int = 0
    prefix: str = "L"

    def new_label(self, suffix: Optional[str] = None) -> Label:
        i = self._next_id
        self._next_id += 1
        base = f"{self.prefix}{i}"
        return Label(f"{base}_{suffix}") if suffix else Label(base)

    def reset(self) -> None:
        self._next_id = 0
