from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

WORD = 8  # 64-bit por simplicidad


@dataclass
class FrameLayout:
    """
    Modelo simple de registro de activación (stack frame) relativo a FP (frame pointer).

    Convenciones (ejemplo típico x86-64 System V simplificado):
      [FP + 16]  arg2
      [FP + 8 ]  arg1
      [FP + 0 ]  return address   (no lo usamos, pero existe)
      [FP - 8 ]  saved FP         (o al revés, según convención; aquí ignoramos)
      [FP - 16]  local1
      [FP - 24]  local2
      ...

    Decisiones:
      - Params: offsets positivos, empezando en +8 y creciendo.
      - Locals: offsets negativos, empezando en -8 y decreciendo.
      - Tamaño fijo por símbolo: WORD.
      - No solapamos offsets; mantenemos mapas separados.
    """
    name: str
    params: List[str] = field(default_factory=list)
    locals: List[str] = field(default_factory=list)

    # Asignación final
    param_offset: Dict[str, int] = field(default_factory=dict)
    local_offset: Dict[str, int] = field(default_factory=dict)

    _sealed: bool = False

    def add_param(self, name: str) -> None:
        self._ensure_mutable()
        if name in self.params:
            raise ValueError(f"Parámetro duplicado: {name}")
        if name in self.locals:
            raise ValueError(f"Nombre usado como local: {name}")
        self.params.append(name)

    def add_local(self, name: str) -> None:
        self._ensure_mutable()
        if name in self.locals:
            raise ValueError(f"Local duplicado: {name}")
        if name in self.params:
            raise ValueError(f"Nombre usado como parámetro: {name}")
        self.locals.append(name)

    def seal(self) -> None:
        """Asigna offsets y sella el frame para evitar cambios posteriores."""
        self._ensure_mutable()

        # Params: +8, +16, +24, ...
        off = WORD
        for p in self.params:
            self.param_offset[p] = off
            off += WORD

        # Locals: -8, -16, -24, ...
        off = -WORD
        for v in self.locals:
            self.local_offset[v] = off
            off -= WORD

        self._sealed = True

    def _ensure_mutable(self) -> None:
        if self._sealed:
            raise RuntimeError("FrameLayout sellado; no se puede modificar")

    def offset_of(self, name: str) -> Optional[int]:
        if name in self.param_offset:
            return self.param_offset[name]
        if name in self.local_offset:
            return self.local_offset[name]
        return None

    def frame_size_bytes(self) -> int:
        """Tamaño necesario para locals (zona negativa)."""
        if not self._sealed:
            raise RuntimeError("Debe sellar el frame antes de consultar el tamaño")
        # locals ocupan |locals| * WORD
        return len(self.locals) * WORD
