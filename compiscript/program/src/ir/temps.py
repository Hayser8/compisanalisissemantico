# program/src/ir/temps.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from .model import Temp, Label


@dataclass
class TempAllocator:
    """
    crea temporales y recicla ids simples.
    - new_temp(): da t<n>
    - free()/release(): devuelve el id a la lista libre
    - reset(): deja todo como nuevo
    """
    _next_id: int = 0
    _free: List[int] = None  

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
        n = getattr(t, "name", "")
        if not isinstance(n, str) or not n.startswith("t"):
            return
        try:
            tid = int(n[1:])
        except Exception:
            return
        if 0 <= tid < self._next_id and tid not in self._free:
            self._free.append(tid)

    def release(self, t: Temp) -> None:
        self.free(t)

    def reset(self) -> None:
        self._next_id = 0
        self._free.clear()


@dataclass
class LabelAllocator:
    """
    genera etiquetas simples: L0, L1, ...
    new_label('hint') -> L<n>_hint
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
