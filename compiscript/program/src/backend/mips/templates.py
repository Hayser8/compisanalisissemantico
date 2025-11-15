from __future__ import annotations
from typing import List, Optional
import struct  # para empaquetar floats como bits IEEE-754

from src.ir.model import (
    Instr, LabelInstr, Goto, IfGoto, Assign, UnaryOp, BinOp, Return,
    Call, Load, Store, GetProp, SetProp, NewObject,
    Operand, Temp, Name, Const, Label, MakeClosure, CallClosure
)
from .objects import LayoutRegistry, WORD  # para offsets/tamaños

# ---------------------------------------------------------------------
# Registros temporales usados POR LA PLANTILLA (evitamos los que RA usa para loads)
# ---------------------------------------------------------------------
R_RES = "$t0"   # registro de resultado (se puede clobber)
R_K1  = "$t4"   # const slot 1 (solo para Const)
R_K2  = "$t5"   # const slot 2 (solo para Const)
R_SCR = "$t3"   # scratch para direcciones / pushes


# =========================
#  Tracking “float-like”
# =========================
def _ensure_fp_state(ra):
    if not hasattr(ra, "_fp_like"):
        ra._fp_like = set()
    return ra._fp_like


def _mark_fp_like(ra, reg: str):
    _ensure_fp_state(ra).add(reg)


def _is_fp_like(ra, reg: str) -> bool:
    return reg in _ensure_fp_state(ra)


# =========================
#  Helpers para labels por función
# =========================
def _get_fn_label(kwargs) -> Optional[str]:
    """
    Extrae el label de la función actual, pasado desde emit_function
    como 'fn_label'. Si no existe, devuelve None (sin mangling).
    """
    fn_label = kwargs.get("fn_label")
    if isinstance(fn_label, str) and fn_label:
        return fn_label
    return None


def _mangle_block_label(raw: str, fn_label: Optional[str]) -> str:
    """
    Prefija labels de bloques (L0, L1_then, etc.) con el nombre de la función,
    para que en el ASM final no haya 'L0' repetidos en distintas funciones.

    Si el label ya empieza con 'fn_label__', se deja tal cual.
    """
    if not fn_label:
        return raw
    prefix = fn_label + "__"
    if raw.startswith(prefix):
        return raw
    return prefix + raw


def _emit_li_num(out: List[str], dst_reg: str, imm, *, ra=None):
    """
    Inmediatos:
      - int    -> li normal
      - float  -> li con bits IEEE-754 en hexa
      - bool   -> 0 / 1
      - None   -> 0
      - str    -> se intenta parsear a int o float; si NO se puede,
                  se lanza ValueError para que el caller lo trate como string literal.

    Si resulta ser float y se pasa 'ra', marca el dst como float-like.
    """
    val = imm

    # Normalizar bool / None
    if isinstance(val, bool):
        val = 1 if val else 0
    if val is None:
        val = 0

    # Si viene como string ("2.0", "0.5", "42"), intentar parsear
    if isinstance(val, str):
        s = val.strip()
        # primero intentar int
        try:
            val_int = int(s, 0)  # soporta "10", "0xFF", etc.
            val = val_int
        except ValueError:
            # luego intentar float
            try:
                val_float = float(s)
                val = val_float
            except ValueError:
                # Aquí NO sabemos mapear strings a labels,
                # eso lo debe hacer el caller (_as_reg) usando un pool.
                raise ValueError(
                    f"Const string no numérica no soportada en _emit_li_num: {val!r}. "
                    "Debe mapearse a un label (.asciiz) antes de llegar aquí."
                )

    # Ahora val ya no es string
    if isinstance(val, float):
        bits = struct.unpack(">I", struct.pack(">f", float(val)))[0]
        out.append(f"  li {dst_reg}, 0x{bits:08X}")
        if ra is not None:
            _mark_fp_like(ra, dst_reg)
    else:
        out.append(f"  li {dst_reg}, {val}")


def _emit_fp_binop(out: List[str], op: str, ra, dst: str, rx: str, ry: str):
    m = {"add": "add.s", "sub": "sub.s", "mul": "mul.s", "div": "div.s"}[op]
    out.append(f"  mtc1 {rx}, $f0")
    out.append(f"  mtc1 {ry}, $f1")
    out.append(f"  {m} $f2, $f0, $f1")
    out.append(f"  mfc1 {dst}, $f2")
    _mark_fp_like(ra, dst)


# =========================
#  Mapeo estable para Temp
# =========================
def _ensure_temp_map(ra) -> None:
    if not hasattr(ra, "_tmpl_temp_map"):
        ra._tmpl_temp_map = {}
        ra._tmpl_temp_pool = ["$t6", "$t7", "$t8", "$t9"]


def _reg_for_temp(ra, t: Temp) -> str:
    _ensure_temp_map(ra)
    m = ra._tmpl_temp_map
    if t.name not in m:
        m[t.name] = ra._tmpl_temp_pool.pop(0) if ra._tmpl_temp_pool else "$t9"
    return m[t.name]


# =========================
#  Comparaciones (0/1)
# =========================
def _emit_cmp(op: str, rd: str, rs: str, rt: str, out: List[str]) -> None:
    if op == "==":
        out.append(f"  seq {rd}, {rs}, {rt}")
    elif op == "!=":
        out.append(f"  sne {rd}, {rs}, {rt}")
    elif op == "<":
        out.append(f"  slt {rd}, {rs}, {rt}")
    elif op == "<=":
        out.append(f"  slt {rd}, {rt}, {rs}")
        out.append(f"  xori {rd}, {rd}, 1")
    elif op == ">":
        out.append(f"  slt {rd}, {rt}, {rs}")
    elif op == ">=":
        out.append(f"  slt {rd}, {rs}, {rt}")
        out.append(f"  xori {rd}, {rd}, 1")
    else:
        raise ValueError(f"Operador de comparación no soportado: {op}")


def _align8(n: int) -> int:
    return (n + 7) & ~7


# =========================
#  Helpers de carga/escritura
# =========================
def _as_reg(val, ra, out: List[str], *, const_slot: int = 1, pool=None) -> str:
    """
    Convierte un Operand (Const, Name, Temp) en un registro.

    Para Const de tipo string no numérica:
      - Usa `pool.get_label_for(text)` para obtener un label __str_n
      - Emite `la R_K*, label`
    """
    if isinstance(val, Const):
        v = val.value
        # bools se normalizan en _emit_li_num
        reg = R_K1 if const_slot == 1 else R_K2

        if isinstance(v, str):
            # Intentar tratarlo como número; si falla, usar pool de strings
            try:
                _emit_li_num(out, reg, v, ra=ra)
            except ValueError:
                if pool is not None and hasattr(pool, "get_label_for"):
                    label = pool.get_label_for(v)
                    out.append(f"  la {reg}, {label}")
                else:
                    # Fallback ultra-defensivo si no hay pool
                    out.append(
                        f"  li {reg}, 0  # WARN: const string {v!r} sin pool; usando 0"
                    )
            return reg

        # No string: usar _emit_li_num normal
        _emit_li_num(out, reg, v, ra=ra)
        return reg

    if isinstance(val, Name):
        return ra.reg_for_read(val, out)
    if isinstance(val, Temp):
        return _reg_for_temp(ra, val)
    raise TypeError(f"Valor no soportado: {val!r}")


def _store_into_dest(dst, src_reg: str, ra, out: List[str]) -> None:
    if isinstance(dst, Name):
        ra.store_if_name(dst, src_reg, out)
    elif isinstance(dst, Temp):
        r = _reg_for_temp(ra, dst)
        if r != src_reg:
            out.append(f"  move {r}, {src_reg}")
    elif dst is None:
        return
    else:
        raise TypeError(f"Destino no soportado: {dst!r}")


# =========================
#  Emisión principal
# =========================
def emit_for_instr(ins: Instr, ra, out: List[str], *, epilogue_label: str, **kwargs) -> None:
    """
    kwargs:
      - layouts: LayoutRegistry
      - obj_types: Dict[str,str]  (o layouts.obj_types)
      - fn_label: str  (label de la función actual, para manglear bloques)
      - const_pool: objeto con get_label_for(str) -> label (para strings)
    """
    layouts: LayoutRegistry | None = kwargs.get("layouts")
    obj_types = kwargs.get("obj_types") or (getattr(layouts, "obj_types", {}) if layouts else {}) or {}
    fn_label = _get_fn_label(kwargs)  # <-- para prefijar L0, L1_then, etc.
    const_pool = kwargs.get("const_pool")

    # 1) Etiquetas y saltos
    if isinstance(ins, LabelInstr):
        lab = _mangle_block_label(ins.label.name, fn_label)
        out.append(f"{lab}:")
        return

    if isinstance(ins, Goto):
        lab = _mangle_block_label(ins.target.name, fn_label)
        out.append(f"  j {lab}")
        return

    if isinstance(ins, IfGoto):
        if isinstance(ins.cond, Const):
            if ins.cond.value:
                lab = _mangle_block_label(ins.target.name, fn_label)
                out.append(f"  j {lab}")
            return
        rc = _as_reg(ins.cond, ra, out, pool=const_pool)
        lab = _mangle_block_label(ins.target.name, fn_label)
        out.append(f"  bne {rc}, $zero, {lab}")
        return

    # 2) Return
    if isinstance(ins, Return):
        if ins.value is not None:
            rv = _as_reg(ins.value, ra, out, pool=const_pool)
            out.append(f"  move $v0, {rv}")
        out.append(f"  j {epilogue_label}")
        return

    # 3) Asignación
    if isinstance(ins, Assign):
        rs = _as_reg(ins.src, ra, out, pool=const_pool)
        _store_into_dest(ins.dst, rs, ra, out)
        return

    # 4) UnaryOp
    if isinstance(ins, UnaryOp):
        rv = _as_reg(ins.value, ra, out, pool=const_pool)
        if ins.op in ("+", "-") and _is_fp_like(ra, rv):
            if ins.op == "+":
                _store_into_dest(ins.dst, rv, ra, out)
                return
            else:
                _emit_li_num(out, R_K2, 0.0, ra=ra)
                _emit_fp_binop(out, "sub", ra, R_RES, R_K2, rv)
                _store_into_dest(ins.dst, R_RES, ra, out)
                return
        if ins.op == "-":
            out.append(f"  subu {R_RES}, $zero, {rv}")
        elif ins.op == "~":
            out.append(f"  nor {R_RES}, {rv}, $zero")
        elif ins.op == "!":
            out.append(f"  sltiu {R_RES}, {rv}, 1")
        elif ins.op == "+":
            out.append(f"  move {R_RES}, {rv}")
        else:
            raise ValueError(f"Operador unario no soportado: {ins.op}")
        _store_into_dest(ins.dst, R_RES, ra, out)
        return

    # 5) BinOp
    if isinstance(ins, BinOp):
        # Shifts con inmediato
        if ins.op in ("<<", ">>", ">>>") and isinstance(ins.right, Const) and isinstance(ins.right.value, int):
            rl = _as_reg(ins.left, ra, out, pool=const_pool)
            sh = int(ins.right.value) & 31
            if ins.op == "<<":
                out.append(f"  sll {R_RES}, {rl}, {sh}")
            elif ins.op == ">>":
                # FIX: faltaba el registro fuente en tu versión
                out.append(f"  sra {R_RES}, {rl}, {sh}")
            else:
                out.append(f"  srl {R_RES}, {rl}, {sh}")
            _store_into_dest(ins.dst, R_RES, ra, out)
            return

        rl = _as_reg(ins.left,  ra, out, const_slot=1, pool=const_pool)
        rr = _as_reg(ins.right, ra, out, const_slot=2, pool=const_pool)
        op = ins.op

        # Si alguno es float-like -> usar COP1 para + - * /.
        if _is_fp_like(ra, rl) or _is_fp_like(ra, rr):
            if   op == "+": _emit_fp_binop(out, "add", ra, R_RES, rl, rr)
            elif op == "-": _emit_fp_binop(out, "sub", ra, R_RES, rl, rr)
            elif op == "*": _emit_fp_binop(out, "mul", ra, R_RES, rl, rr)
            elif op == "/": _emit_fp_binop(out, "div", ra, R_RES, rl, rr)
            else:
                # Otros operan a nivel entero (bits / lógicos 0/1)
                if op in ("&", "&&"):
                    out.append(f"  and {R_RES}, {rl}, {rr}")
                elif op in ("|", "||"):
                    out.append(f"  or {R_RES}, {rl}, {rr}")
                elif op == "^":
                    out.append(f"  xor {R_RES}, {rl}, {rr}")
                elif op in ("==", "!=", "<", "<=", ">", ">="):
                    _emit_cmp(op, R_RES, rl, rr, out)
                elif op in ("<<", ">>", ">>>"):
                    out.append(
                        f"  sllv {R_RES}, {rl}, {rr}" if op == "<<" else
                        f"  srav {R_RES}, {rl}, {rr}" if op == ">>" else
                        f"  srlv {R_RES}, {rl}, {rr}"
                    )
                elif op == "%":
                    out.append(f"  div {rl}, {rr}")
                    out.append(f"  mfhi {R_RES}")
                else:
                    raise ValueError(f"Operador binario no soportado: {op}")
            _store_into_dest(ins.dst, R_RES, ra, out)
            return

        # Todo entero
        if   op == "+":  out.append(f"  addu {R_RES}, {rl}, {rr}")
        elif op == "-":  out.append(f"  subu {R_RES}, {rl}, {rr}")
        elif op == "*":  out.append(f"  mul {R_RES}, {rl}, {rr}")
        elif op == "/":
            out.append(f"  div {rl}, {rr}")
            out.append(f"  mflo {R_RES}")
        elif op == "%":
            out.append(f"  div {rl}, {rr}")
            out.append(f"  mfhi {R_RES}")
        elif op == "<<":   out.append(f"  sllv {R_RES}, {rl}, {rr}")
        elif op == ">>":   out.append(f"  srav {R_RES}, {rl}, {rr}")
        elif op == ">>>":  out.append(f"  srlv {R_RES}, {rl}, {rr}")
        elif op in ("&", "&&"):
            out.append(f"  and {R_RES}, {rl}, {rr}")
        elif op in ("|", "||"):
            out.append(f"  or {R_RES}, {rl}, {rr}")
        elif op == "^":
            out.append(f"  xor {R_RES}, {rl}, {rr}")
        elif op in ("==", "!=", "<", "<=", ">", ">="):
            _emit_cmp(op, R_RES, rl, rr, out)
        else:
            raise ValueError(f"Operador binario no soportado: {op}")
        _store_into_dest(ins.dst, R_RES, ra, out)
        return

    # 6) Call (intrínsecos MARS y normal)
    if isinstance(ins, Call):
        if ins.func == "__print_int":
            a0 = _as_reg(ins.args[0], ra, out, pool=const_pool)
            if a0 != "$a0":
                out.append(f"  move $a0, {a0}")
            out.append("  li $v0, 1")
            out.append("  syscall")
            return

        if ins.func == "__read_int":
            out.append("  li $v0, 5")
            out.append("  syscall")
            if ins.dst is not None:
                _store_into_dest(ins.dst, "$v0", ra, out)
            return

        if ins.func == "__exit":
            out.append("  li $v0, 10")
            out.append("  syscall")
            return

        ra.spill_all_live_temps(out)

        n = len(ins.args)
        extra = max(0, n - 4)
        extra_bytes = _align8(extra * WORD)
        if extra_bytes:
            out.append(f"  addiu $sp, $sp, -{extra_bytes}")
            for i in range(4, n):
                r = _as_reg(ins.args[i], ra, out, const_slot=2, pool=const_pool)
                out.append(f"  sw {r}, {(i - 4) * WORD}($sp)")

        upto = min(n, 4)
        for i in range(upto):
            r = _as_reg(ins.args[i], ra, out,
                        const_slot=1 if i == 0 else 2,
                        pool=const_pool)
            if r != f"$a{i}":
                out.append(f"  move $a{i}, {r}")

        out.append(f"  jal {ins.func}")
        if extra_bytes:
            out.append(f"  addiu $sp, $sp, {extra_bytes}")

        if ins.dst is not None:
            _store_into_dest(ins.dst, "$v0", ra, out)
            if isinstance(ins.dst, Temp):
                out.append(f"  # caller-save spill {ins.dst.name}")
                ra.spill_if_needed(ins.dst, out)
        return

    # 7) Load  (array[idx])
    if isinstance(ins, Load):
        rbase = ra.reg_for_read(ins.array, out)
        ridx = ra.reg_for_read(ins.index, out)
        out.append(f"  sll {R_SCR}, {ridx}, 2")
        out.append(f"  addu {R_SCR}, {rbase}, {R_SCR}")
        out.append(f"  lw {R_RES}, 0({R_SCR})")
        _store_into_dest(ins.dst, R_RES, ra, out)
        return

    # 8) Store (array[idx] = value)
    if isinstance(ins, Store):
        rbase = ra.reg_for_read(ins.array, out)
        ridx = ra.reg_for_read(ins.index, out)
        rval = _as_reg(ins.value, ra, out, pool=const_pool)
        out.append(f"  sll {R_SCR}, {ridx}, 2")
        out.append(f"  addu {R_SCR}, {rbase}, {R_SCR}")
        out.append(f"  sw {rval}, 0({R_SCR})")
        return

    # 9) Objetos
    if isinstance(ins, NewObject):
        if layouts is None:
            raise ValueError("NewObject requiere LayoutRegistry")
        size = layouts.obj_size(ins.class_name)
        out.append("  li $v0, 9")
        out.append(f"  li $a0, {size}")
        out.append("  syscall")
        if ins.dst is not None:
            _store_into_dest(ins.dst, "$v0", ra, out)
        return

    if isinstance(ins, GetProp):
        if layouts is None:
            raise ValueError("GetProp requiere LayoutRegistry")
        cls_name = None
        if isinstance(ins.obj, Name) and ins.obj.name in obj_types:
            cls_name = obj_types[ins.obj.name]
        elif isinstance(ins.obj, Temp) and ins.obj.name in obj_types:
            cls_name = obj_types[ins.obj.name]
        off = layouts.field_offset(ins.prop, class_name=cls_name)
        rbase = ra.reg_for_read(ins.obj, out)
        out.append(f"  lw {R_RES}, {off}({rbase})")
        _store_into_dest(ins.dst, R_RES, ra, out)
        return

    if isinstance(ins, SetProp):
        if layouts is None:
            raise ValueError("SetProp requiere LayoutRegistry")
        cls_name = None
        if isinstance(ins.obj, Name) and ins.obj.name in obj_types:
            cls_name = obj_types[ins.obj.name]
        elif isinstance(ins.obj, Temp) and ins.obj.name in obj_types:
            cls_name = obj_types[ins.obj.name]
        off = layouts.field_offset(ins.prop, class_name=cls_name)
        rbase = ra.reg_for_read(ins.obj, out)
        rval = _as_reg(ins.value, ra, out, pool=const_pool)
        out.append(f"  sw {rval}, {off}({rbase})")
        return

    # 10) ==== CLOSURES ====
    if isinstance(ins, MakeClosure):
        code_label = ins.code.name if isinstance(ins.code, Label) else str(ins.code)
        k = len(ins.captures)
        if k > 0:
            out.append("  li $v0, 9")
            out.append(f"  li $a0, {k * WORD}")
            out.append("  syscall")
            r_env = R_SCR
            out.append(f"  move {r_env}, $v0")
            for i, cap in enumerate(ins.captures):
                rc = _as_reg(cap, ra, out, pool=const_pool)
                out.append(f"  sw {rc}, {i * WORD}({r_env})")
        else:
            r_env = "$zero"
        out.append(f"  la $a0, {code_label}")
        out.append(f"  move $a1, {r_env}")
        ra.spill_all_live_temps(out)
        out.append("  jal __make_closure")
        if ins.dst is not None:
            _store_into_dest(ins.dst, "$v0", ra, out)
        return

    if isinstance(ins, CallClosure):
        ra.spill_all_live_temps(out)
        n = len(ins.args)
        extra = max(0, n - 3)
        extra_bytes = _align8(extra * WORD)
        if extra_bytes:
            out.append(f"  addiu $sp, $sp, -{extra_bytes}")
            for i in range(3, n):
                r = _as_reg(ins.args[i], ra, out, const_slot=2, pool=const_pool)
                out.append(f"  sw {r}, {(i - 3) * WORD}($sp)")
        rcl = _as_reg(ins.closure, ra, out, pool=const_pool)
        if rcl != "$a0":
            out.append(f"  move $a0, {rcl}")
        for i, arg in enumerate(ins.args[:3]):
            r = _as_reg(arg, ra, out,
                        const_slot=1 if i == 0 else 2,
                        pool=const_pool)
            if r != f"$a{i+1}":
                out.append(f"  move $a{i+1}, {r}")
        out.append("  jal __closure_apply")
        if extra_bytes:
            out.append(f"  addiu $sp, $sp, {extra_bytes}")
        if ins.dst is not None:
            _store_into_dest(ins.dst, "$v0", ra, out)
            if isinstance(ins.dst, Temp):
                out.append(f"  # caller-save spill {ins.dst.name}")
                ra.spill_if_needed(ins.dst, out)
        return

    raise ValueError(f"Instrucción TAC no soportada aún por plantillas: {type(ins).__name__}")
