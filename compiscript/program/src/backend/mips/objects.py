# program/src/backend/mips/objects.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

WORD = 4  # MIPS32: tamaño de palabra


@dataclass
class ClassLayout:
    name: str
    own_fields: List[str]
    base_name: Optional[str] = None

    field_off: Dict[str, int] = field(default_factory=dict)
    size_bytes: int = 0

    def build_from_base(self, base: Optional["ClassLayout"]) -> None:
        self.field_off.clear()
        off = 0
        if base is not None:
            # hereda offsets tal cual
            for fname, foff in base.field_off.items():
                self.field_off[fname] = foff
            off = base.size_bytes

        for f in self.own_fields:
            if f in self.field_off:
                raise ValueError(
                    f"Campo '{f}' ya existe en la jerarquía de {self.name} (heredado)."
                )
            self.field_off[f] = off
            off += WORD

        self.size_bytes = off

    def offset_of(self, field: str) -> int:
        if field not in self.field_off:
            raise KeyError(f"Campo {field} no existe en {self.name}")
        return self.field_off[field]


@dataclass
class LayoutRegistry:
    classes: Dict[str, ClassLayout] = field(default_factory=dict)
    global_field_off: Dict[str, int] = field(default_factory=dict)

    def register_class(self, name: str, fields: List[str], base: Optional[str] = None) -> None:
        if name in self.classes:
            raise ValueError(f"Clase duplicada: {name}")
        self.classes[name] = ClassLayout(name=name, own_fields=list(fields), base_name=base)

    def build_all(self) -> None:
        """Calcula offsets/tamaños respetando herencia (topo-sort)."""
        indeg: Dict[str, int] = {n: 0 for n in self.classes}
        adj: Dict[str, List[str]] = {n: [] for n in self.classes}

        # ⚠️ .items() (no .items)
        for name, cl in self.classes.items():
            if cl.base_name:
                if cl.base_name not in self.classes:
                    raise ValueError(f"Clase base '{cl.base_name}' no registrada (usada por {name}).")
                indeg[name] += 1
                adj[cl.base_name].append(name)

        # Kahn
        from collections import deque
        q = deque([n for n, d in indeg.items() if d == 0])
        order: List[str] = []
        while q:
            u = q.popleft()
            order.append(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)

        if len(order) != len(self.classes):
            raise ValueError("Ciclo en la jerarquía de clases.")

        for name in order:
            cl = self.classes[name]
            base_layout = self.classes.get(cl.base_name) if cl.base_name else None
            cl.build_from_base(base_layout)

        # marca “construido” para lazy-build en el emitter
        setattr(self, "_built", True)

    def set_global_field_order(self, fields: List[str]) -> None:
        self.global_field_off.clear()
        off = 0
        for f in fields:
            self.global_field_off[f] = off
            off += WORD

    def obj_size(self, class_name: Optional[str], *, fallback_fields: List[str] | None = None) -> int:
        if class_name:
            if class_name not in self.classes:
                raise KeyError(f"Clase '{class_name}' no registrada")
            return self.classes[class_name].size_bytes
        if fallback_fields:
            return len(fallback_fields) * WORD
        if self.global_field_off:
            max_off = max(self.global_field_off.values())
            return max_off + WORD
        return 0

    def field_offset(self, field: str, class_name: str | None = None) -> int:
        if class_name:
            if class_name not in self.classes:
                raise KeyError(f"Clase '{class_name}' no registrada")
            return self.classes[class_name].offset_of(field)
        if field in self.global_field_off:
            return self.global_field_off[field]
        raise KeyError(f"No offset para campo '{field}' (sin clase)")
