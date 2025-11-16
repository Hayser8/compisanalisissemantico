from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List

from src.ir.model import Temp, Name, Const, Operand
from .frame_plan import FramePlan
from .emit_utils import asm_li, asm_lw_fp, asm_sw_fp, asm_comment

WORD = 4  # tamaño de palabra MIPS32

POOL_T = [f"$t{i}" for i in range(10)]  # $t0..$t9
POOL_S = [f"$s{i}" for i in range(8)]   # $s0..$s7


@dataclass
class RegAlloc:
    """
    Asignador mínimo de registros para MIPS.

    - $t*: caller-saved para temporales y, por defecto, también Names.
    - Soporte opcional para "pinnear" algunos Names a $s* (callee-saved) cuando
      estamos emitiendo una función completa: así el prólogo/epílogo guarda/restaura $s*.

    Es deliberadamente "structural": solo requiere que `plan` tenga ciertos
    atributos (local_off, param_home_off, param_names, need_param_homes, etc.),
    aunque no sea exactamente una instancia de FramePlan (ej. SimpleFramePlan del CLI).
    """
    plan: FramePlan

    # "$t0" -> "t3", "name:x", "const:1", etc.
    reg_owner: Dict[str, str] = field(default_factory=dict)

    # "t3" -> "$t0"
    temp_in_reg: Dict[str, str] = field(default_factory=dict)

    # nombre_temp / nombre_Name -> offset negativo de spill
    temp_spill_off: Dict[str, int] = field(default_factory=dict)

    _next_t: int = 0

    # mapeo de Names "pinneados" a $s* y set de $s* usados
    # ej: "x" -> "$s0"
    name_pins: Dict[str, str] = field(default_factory=dict)
    s_regs_in_use: List[str] = field(default_factory=list)

    # -------------------------------------------------
    # Normalización del plan (hacerlo "frame-plan-like")
    # -------------------------------------------------
    def __post_init__(self) -> None:
        """
        Asegura que `plan` tenga todos los campos mínimos que el regalloc/emitter
        esperan, aunque sea un SimpleFramePlan u otro stub.
        """
        # Mapa de locales
        if not hasattr(self.plan, "local_off") or self.plan.local_off is None:
            self.plan.local_off = {}

        # Mapa de homes de parámetros
        if not hasattr(self.plan, "param_home_off") or self.plan.param_home_off is None:
            self.plan.param_home_off = {}

        # Nombres de parámetros: normalizar a lista de strings
        raw_pnames = getattr(self.plan, "param_names", [])
        norm_pnames: List[str] = []
        for p in raw_pnames:
            if isinstance(p, str):
                norm_pnames.append(p)
            else:
                norm_pnames.append(getattr(p, "name", str(p)))
        self.plan.param_names = norm_pnames

        # Cuántos parámetros tienen "home" en el frame (por defecto, todos los que tengan entrada)
        if not hasattr(self.plan, "need_param_homes"):
            self.plan.need_param_homes = len(self.plan.param_home_off)

        # Bytes reservados para spills (para compatibilidad con FramePlan)
        if not hasattr(self.plan, "spill_bytes"):
            self.plan.spill_bytes = 0

        # Contador interno de spills ya usados
        if not hasattr(self.plan, "_spill_used_bytes"):
            self.plan._spill_used_bytes = 0

    # ---------------- Internos ----------------

    def _acquire_t(self) -> str:
        """
        Obtiene un $t* libre, si no hay, reutiliza uno (MVP).
        """
        for _ in range(len(POOL_T)):
            reg = POOL_T[self._next_t]
            self._next_t = (self._next_t + 1) % len(POOL_T)
            if reg not in self.reg_owner:
                self.reg_owner[reg] = "<reserved>"
                return reg

        # En caso de saturación, pisa alguno (MVP, no óptimo)
        reg = POOL_T[self._next_t]
        self._next_t = (self._next_t + 1) % len(POOL_T)
        self.reg_owner[reg] = "<reserved>"
        return reg

    def _alloc_spill_slot(self) -> int:
        """
        Asigna un nuevo slot de spill en el frame.

        Layout negativo (por debajo de $fp):
          - primero homes de parámetros,
          - luego locales,
          - luego spills.

        base_bytes = 4 * (#param_homes + #locals)
        El primer spill va en -(base_bytes + 4), el segundo en -(base_bytes + 8), etc.

        Además mantiene sincronizado plan._spill_used_bytes y plan.spill_bytes
        (para que cualquier FramePlan real pueda calcular un frame_size suficientemente grande).
        """
        base_bytes = WORD * (
            len(getattr(self.plan, "local_off", {})) +
            getattr(self.plan, "need_param_homes", 0)
        )

        used = getattr(self.plan, "_spill_used_bytes", 0)
        new_used = used + WORD
        setattr(self.plan, "_spill_used_bytes", new_used)

        # Actualizar "high-water mark" de spills en el plan (si alguien lo usa)
        prev_spill = getattr(self.plan, "spill_bytes", 0)
        if new_used > prev_spill:
            setattr(self.plan, "spill_bytes", new_used)

        # Offset negativo resultante
        return -(base_bytes + new_used)

    # --------- Global vs local para Names ---------

    def _is_global_name(self, nm: Name) -> bool:
        """
        Determina si un Name representa una variable global.

        Por ahora usamos la marca que debe haber dejado annotate_globals:
          - nm.is_global == True (si existe el atributo).
        """
        # Si por cualquier razón nm no es Name, devolvemos False por seguridad.
        if not isinstance(nm, Name):
            return False
        return bool(getattr(nm, "is_global", False))

    def _home_offset_of_name(self, nm: Name) -> Optional[int]:
        """
        Devuelve el offset negativo donde vive 'nm' en el frame, si tiene "home".

        Se busca primero en locales, luego entre parámetros con home.
        Para nombres marcados como globales, siempre devuelve None (no tienen home en frame).
        """
        # Globales: nunca viven en el frame
        if self._is_global_name(nm):
            return None

        # Local
        local_off = getattr(self.plan, "local_off", {})
        if nm.name in local_off:
            return local_off[nm.name]

        # Parámetro
        pnames: List[str] = getattr(self.plan, "param_names", [])
        if pnames:
            try:
                idx = pnames.index(nm.name)
            except ValueError:
                idx = -1
            if 0 <= idx < getattr(self.plan, "need_param_homes", 0):
                homes = getattr(self.plan, "param_home_off", {})
                if idx in homes:
                    return homes[idx]

        return None

    # ----------- Pinnear names a $s* -----------

    def pin_names_to_sregs(self, names: List[str]) -> List[str]:
        """
        Intenta asignar en orden cada name (string) a $s0..$s7.
        No toca los Names no listados (seguirán usando $t*).
        """
        used: List[str] = []
        i = 0
        for nm in names:
            if nm in self.name_pins:
                sreg = self.name_pins[nm]
                used.append(sreg)
                continue
            if i >= len(POOL_S):
                break
            sreg = POOL_S[i]
            i += 1
            self.name_pins[nm] = sreg
            if sreg not in self.s_regs_in_use:
                self.s_regs_in_use.append(sreg)
            used.append(sreg)
        return used

    # ----------- API pública usada por templates.py -----------

    def acquire_tmp_reg(self) -> str:
        return self._acquire_t()

    def reg_for_read(self, op: Operand, out: List[str]) -> str:
        reg, _ = self.ensure_in_reg(op, out)
        return reg

    def reg_for_write(self, dst: Operand, out: List[str]) -> str:
        """
        Para escribir en `dst` (Temp o Name).
        Para Temp, se reutiliza su registro si ya tiene; para otros, se da un $t*.
        """
        from src.ir.model import Temp as _Temp
        if isinstance(dst, _Temp):
            reg, _ = self.ensure_in_reg(dst, out)
            return reg
        return self._acquire_t()

    def store_if_name(self, dst: Operand, src_reg: str, out: List[str]) -> None:
        """
        Atajo llamado desde emitter/templates para guardar un Name en su home.
        """
        self.store_to_home_if_name(dst, src_reg, out)

    # ----------- Caller-save spills (usado antes de jal) -----------

    def spill_all_live_temps(self, out: List[str]) -> None:
        """
        Spillea TODOS los Temp/Name que actualmente viven en un $t*.
        Emite comentario 'caller-save spill <temp|name>'.
        """
        for tname, reg in list(self.temp_in_reg.items()):
            if tname not in self.temp_spill_off:
                self.temp_spill_off[tname] = self._alloc_spill_slot()
            asm_comment(out, f"caller-save spill {tname}")
            asm_sw_fp(out, reg, self.temp_spill_off[tname])

    # ---------------- API previa ----------------

    def release_all_temps(self) -> None:
        """
        Libera TODOS los $t* (se llama al final de emitir una TAC).
        No añade stores aquí; los spills explícitos se hacen con
        spill_all_live_temps() donde corresponda.
        """
        for reg in list(self.reg_owner.keys()):
            if reg.startswith("$t"):
                self.reg_owner.pop(reg, None)
        self.temp_in_reg.clear()
        self._next_t = 0

    def ensure_in_reg(self, op: Operand, out: List[str]) -> Tuple[str, bool]:
        """
        Garantiza que `op` esté en algún registro general y lo devuelve.

        Retorna (reg, True). El segundo valor se mantiene por compatibilidad
        con versiones previas que lo usaban para "was_loaded".
        """
        from src.ir.model import Temp as _Temp, Name as _Name, Const as _Const

        # ------------ Temp ------------
        if isinstance(op, _Temp):
            tname = op.name
            if tname in self.temp_in_reg:
                return self.temp_in_reg[tname], True
            reg = self._acquire_t()
            if tname in self.temp_spill_off:
                asm_lw_fp(out, reg, self.temp_spill_off[tname])
            self.reg_owner[reg] = tname
            self.temp_in_reg[tname] = reg
            return reg, True

        # ------------ Name ------------
        if isinstance(op, _Name):
            # ¿está pinneado a $s*?
            if op.name in self.name_pins:
                sreg = self.name_pins[op.name]
                off = self._home_offset_of_name(op)
                if off is None:
                    # Si no tiene home estático, darle un spill slot dedicado
                    if op.name not in self.temp_spill_off and not self._is_global_name(op):
                        self.temp_spill_off[op.name] = self._alloc_spill_slot()
                    off = self.temp_spill_off.get(op.name)
                if off is not None:
                    # Carga desde su home (último valor persistente) al $s*
                    asm_lw_fp(out, sreg, off)
                self.reg_owner[sreg] = f"name:{op.name}"
                # No lo añadimos a temp_in_reg: es "name"
                return sreg, True

            # default: usa $t*
            reg = self._acquire_t()
            off = self._home_offset_of_name(op)
            if off is None:
                # Name sin home estático -> spill dedicado (solo si no es global)
                if op.name not in self.temp_spill_off and not self._is_global_name(op):
                    self.temp_spill_off[op.name] = self._alloc_spill_slot()
                off = self.temp_spill_off.get(op.name)
            if off is not None:
                asm_lw_fp(out, reg, off)
            self.reg_owner[reg] = f"name:{op.name}"
            # Lo tratamos igual que un temp a nivel de spills
            if not self._is_global_name(op):
                self.temp_in_reg[op.name] = reg
            return reg, True

        # ------------ Const ------------
        if isinstance(op, _Const):
            reg = self._acquire_t()
            asm_li(out, reg, op.value)
            self.reg_owner[reg] = f"const:{op.value!r}"
            return reg, True

        # ------------ Fallback genérico ------------
        reg = self._acquire_t()
        asm_comment(out, f"ensure_in_reg fallback for {op!r}")
        self.reg_owner[reg] = "fallback"
        return reg, True

    def store_to_home_if_name(self, op: Operand, src_reg: str, out: List[str]) -> None:
        """
        Si `op` es Name, guarda src_reg en su home (local/param/spill).
        Si no, no hace nada.
        """
        from src.ir.model import Name as _Name

        if isinstance(op, _Name):
            # Globales: no se guardan en el frame; la lógica de Store/Load
            # de globales debe generar sw/lw usando la etiqueta en .data.
            if self._is_global_name(op):
                return

            off = self._home_offset_of_name(op)
            if off is None:
                # Name sin home estático -> usar/crear spill dedicado
                if op.name not in self.temp_spill_off:
                    self.temp_spill_off[op.name] = self._alloc_spill_slot()
                off = self.temp_spill_off[op.name]
            asm_sw_fp(out, src_reg, off)

    def spill_if_needed(self, t: Temp, out: List[str]) -> None:
        """
        Spillea un Temp concreto si todavía vive en un $t*.
        Usado al terminar ciertas llamadas para preservar resultados.
        """
        tname = t.name
        reg = self.temp_in_reg.get(tname)
        if not reg:
            return
        if tname not in self.temp_spill_off:
            self.temp_spill_off[tname] = self._alloc_spill_slot()
        asm_sw_fp(out, reg, self.temp_spill_off[tname])
