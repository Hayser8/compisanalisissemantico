from __future__ import annotations
from typing import List, Tuple

class StringPool:
    """
    Pool mínimo para cadenas.
    - add(texto) -> devuelve una etiqueta __str_N
    - pairs() -> lista de tuplas (label, texto) que emit_full_program sabe leer
    """
    def __init__(self) -> None:
        self._pairs: List[Tuple[str, str]] = []

    def add(self, s: str) -> str:
        lab = f"__str_{len(self._pairs)}"
        self._pairs.append((lab, s))
        return lab

    # emit_full_program usa _iter_string_pool_pairs que intenta
    # llamar métodos sin args que devuelvan lista de (label, texto).
    def pairs(self) -> List[Tuple[str, str]]:
        return list(self._pairs)
