from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

def _escape_asciiz(s: str) -> str:
    """
    Escapa una cadena para .asciiz de MARS: \n, \t, \", \\
    (Si necesitas más escapes en el futuro, agrégales aquí.)
    """
    return (
        s.replace("\\", "\\\\")
         .replace("\"", "\\\"")
         .replace("\n", "\\n")
         .replace("\t", "\\t")
    )

@dataclass
class StringPool:
    """
    Deduplicador de strings. Provee etiquetas estables: __str_0, __str_1, ...
    """
    _map: Dict[str, str] = field(default_factory=dict)
    _order: List[str] = field(default_factory=list)  # para emisión determinista

    def ensure_label(self, s: str) -> str:
        if s in self._map:
            return self._map[s]
        label = f"__str_{len(self._order)}"
        self._map[s] = label
        self._order.append(s)
        return label

    def emit_data(self) -> List[str]:
        out: List[str] = []
        if not self._order:
            return out
        # No agregamos .data aquí; el caller lo hará una sola vez.
        for s in self._order:
            lab = self._map[s]
            esc = _escape_asciiz(s)
            out.append(f'{lab}: .asciiz "{esc}"')
        return out


@dataclass
class GlobalsTable:
    """
    Declaración simple de globales .word (4 bytes).
    """
    _defs: Dict[str, int] = field(default_factory=dict)
    _ordered: List[str] = field(default_factory=list)

    def define_word(self, name: str, init: int = 0) -> None:
        if name not in self._defs:
            self._ordered.append(name)
        self._defs[name] = int(init)

    def emit_data(self) -> List[str]:
        out: List[str] = []
        for name in self._ordered:
            val = self._defs[name]
            out.append(f"{name}: .word {val}")
        return out
