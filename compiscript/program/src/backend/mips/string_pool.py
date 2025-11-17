from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class StringPool:
    """
    Pool de strings para el backend MIPS.

    Características:
      - Deduplica: el mismo texto siempre recibe la misma etiqueta __str_N.
      - Orden estable: se guarda el orden de inserción para emitir .data determinista.
      - API:
          - ensure_label(texto) / get_label_for(texto) -> "__str_k"
          - add(texto) -> alias de ensure_label (compatibilidad)
          - pairs() -> lista de (label, texto), útil para tests u otras emisiones.
    """
    _map: Dict[str, str] = field(default_factory=dict)   # texto -> label
    _order: List[str] = field(default_factory=list)      # textos en orden de inserción

    def ensure_label(self, s: str) -> str:
        """Devuelve un label estable para el string s (lo crea si no existe)."""
        if s in self._map:
            return self._map[s]
        label = f"__str_{len(self._order)}"
        self._map[s] = label
        self._order.append(s)
        return label

    # Alias “oficial” que usan las plantillas para strings.
    def get_label_for(self, s: str) -> str:
        """Alias público de ensure_label, usado por templates._as_reg."""
        return self.ensure_label(s)

    # Alias de compatibilidad con la versión vieja de StringPool.
    def add(self, s: str) -> str:
        """Alias de ensure_label para compatibilidad con código viejo."""
        return self.ensure_label(s)

    def pairs(self) -> List[Tuple[str, str]]:
        """
        Devuelve [(label, texto), ...] en orden de inserción.
        Útil si en otro lado quieres iterar explícitamente el pool.
        """
        return [(self._map[s], s) for s in self._order]
