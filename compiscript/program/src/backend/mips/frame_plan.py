# program/src/backend/mips/frame_plan.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

WORD = 4  # MIPS32 (MARS usa 4 bytes por palabra)


def _align(n: int, k: int) -> int:
    r = n % k
    return n if r == 0 else n + (k - r)


@dataclass
class FramePlan:
    """
    Plan del frame por función (relativo a $fp).

    Convención usada junto con emit_prologue/emit_epilogue:
      - Se reservan `frame_size` bytes en la pila.
      - En el prólogo se hace:
            addiu $sp, $sp, -frame_size
            sw   $fp, 0($sp)
            sw   $ra, 4($sp)
            # opcionalmente se guardan $s* en 8($sp), 12($sp), ...
            addiu $fp, $sp, frame_size   # $fp apunta al "tope lógico" del frame

      - Desde la perspectiva de $fp:
            offsets negativos  -> zona de la función (homes de parámetros, locales, spills)
            offsets más negativos aún -> guarda de $fp/$ra y (si aplica) $s*

      - Este plan SOLO describe la zona negativa asociada a parámetros, locales y spills.
        La reserva para $fp/$ra (8 bytes) se suma aparte en frame_size.

    Layout lógico de la zona negativa (debajo de $fp):
        -4($fp)   : param0 home        (si need_param_homes >= 1)
        -8($fp)   : param1 home        (si need_param_homes >= 2)
        ...
        -(4*k)    : homes de params
        a partir de ahí: locals y luego spills

    frame_size = negative_size + 8 (slots de $fp/$ra), alineado a 8 bytes.
    """
    func_name: str
    param_names: List[str] = field(default_factory=list)   # solo para metadata
    local_names: List[str] = field(default_factory=list)
    need_param_homes: int = 0    # cuántos params van en $a* y requieren home slots (0..4)
    spill_bytes: int = 0         # bytes reservados para spills de temporales (múltiplo de 4 idealmente)
    save_s_regs: List[str] = field(default_factory=list)  # reservado para pasos posteriores/análisis

    # Salidas (rellenadas por build):
    param_home_off: Dict[int, int] = field(default_factory=dict)  # i -> offset negativo (solo 0..3)
    local_off: Dict[str, int] = field(default_factory=dict)       # name -> offset negativo
    frame_size: int = 0                                           # tamaño total del frame (bytes)
    negative_size: int = 0                                        # bytes usados por zona negativa (sin contar $fp/$ra)

    def build(self) -> "FramePlan":
        """
        Calcula offsets negativos para:
          - homes de parámetros,
          - locales,
          - región de spills (spill_bytes),
        y el frame_size total (incluye 8 bytes para $fp/$ra).

        Importante:
          - Limpia param_home_off/local_off antes de reconstruir,
            para evitar basura si se reutiliza el mismo FramePlan.
          - Alinea spill_bytes a múltiplo de WORD.
          - Alinea frame_size a 8 bytes.
        """
        # Limpiar resultados previos por seguridad si se reusa la instancia
        self.param_home_off.clear()
        self.local_off.clear()

        # 1) Param homes (hasta 4): -4, -8, -12, -16 ...
        neg = 0
        # Solo creamos homes hasta need_param_homes (0..4). Si luego el emitter
        # decide copiar menos parámetros, es responsabilidad del emitter no
        # acceder a índices que no existan aquí.
        for i in range(self.need_param_homes):
            neg += WORD
            self.param_home_off[i] = -neg

        # 2) Locals: continúan debajo, uno por WORD
        for name in self.local_names:
            neg += WORD
            self.local_off[name] = -neg

        # 3) Spills: si se pide presupuesto de spills, se reserva bloque contiguo
        if self.spill_bytes:
            # Alinear spills a múltiplo de palabra y reflejarlo en el campo
            self.spill_bytes = _align(self.spill_bytes, WORD)
            neg += self.spill_bytes

        # Tamaño de la zona negativa (solo params + locals + spills)
        self.negative_size = neg

        # 4) Slots de $fp/$ra: 8 bytes adicionales
        total = self.negative_size + 8

        # 5) Alinea frame a 8 para seguridad
        self.frame_size = _align(total, 8)
        return self

    # Helpers de consulta
    def home_offset_for_param_index(self, idx: int) -> int:
        return self.param_home_off[idx]

    def offset_of_local(self, name: str) -> int:
        return self.local_off[name]
