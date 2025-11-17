from __future__ import annotations
from typing import List, Dict, Callable, Tuple, Any
import re
import sys

from src.ir.model import (
    Program,
    Function,
    NewObject,
    Call,
    CallClosure,
    Name,
)
from .emit_utils import emit_prologue, emit_epilogue, emit_copy_params_to_homes
from .frame_plan import FramePlan
from .regalloc import RegAlloc
from .templates import emit_for_instr
from .objects import LayoutRegistry
from .closures import emit_runtime_closures

# Tamaño mínimo de frame en bytes para cualquier función.
# 256 bytes = 64 palabras de 4 bytes. Más que suficiente para los tests
# y evita que los locales pisen los slots de $fp/$ra.
_MIN_FRAME_BYTES = 256


def _emit_simple_stub(name: str) -> str:
    """
    Stub muy simple para una función sin definición.
    Convención:
      - prólogo/epílogo estándar
      - devuelve su primer argumento (a0) en v0

    IMPORTANTE: el epílogo incluye un 'nop' en el delay slot
    del 'beq $ra, $zero, __cps_halt' para evitar saltar a 0x0.
    """
    if name == "print_int":
        return f"""print_int:
  addiu $sp, $sp, -16
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 16

  li $v0, 1       # print_int
  syscall

  li $v0, 11      # print_char
  li $a0, 10      # '\\n'
  syscall

print_int__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 16
  beq $ra, $zero, __cps_halt
  nop
  jr $ra
"""

    if name == "print_str":
        return f"""print_str:
  addiu $sp, $sp, -16
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 16

  li $v0, 4       # print_string
  syscall

  li $v0, 11      # print_char
  li $a0, 10      # '\\n'
  syscall

print_str__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 16
  beq $ra, $zero, __cps_halt
  nop
  jr $ra
"""

    # 🔁 Resto de funciones desconocidas: stub genérico como antes
    return f"""{name}:
  # Auto-generated stub: returns its first argument (a0) unchanged
  addiu $sp, $sp, -16
  sw $fp, 0($sp)
  sw $ra, 4($sp)
  addiu $fp, $sp, 16
  sw $a0, -4($fp)
{name}__L0:
  lw $t0, -4($fp)
  move $v0, $t0
  j {name}__epilogue
{name}__epilogue:
  lw $fp, 0($sp)
  lw $ra, 4($sp)
  addiu $sp, $sp, 16
  beq $ra, $zero, __cps_halt
  nop
  jr $ra
"""


def _append_stubs_for_missing_functions(asm: str) -> str:
    """
    Busca llamadas 'jal foo' a funciones que no tienen etiqueta 'foo:'
    y les genera un stub sencillo al final del archivo.
    No crea stubs para nombres que empiezan con '__' (runtime).
    """
    # Etiquetas definidas: líneas tipo "label:"
    label_re = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$", re.MULTILINE)
    defined = {m.group(1) for m in label_re.finditer(asm)}

    # Targets de 'jal algo'
    jal_re = re.compile(r"\bjal\s+([A-Za-z_][A-Za-z0-9_]*)\b")
    called = {m.group(1) for m in jal_re.finditer(asm)}

    # Falta definición
    missing = sorted(
        name for name in called
        if name not in defined and not name.startswith("__")
    )

    if not missing:
        return asm

    parts = [asm, "", "# --- Auto-generated stubs for missing functions ---"]
    for name in missing:
        parts.append(_emit_simple_stub(name))

    return "\n".join(parts)


def _mangle_label(name: str) -> str:
    """Convierte nombres IR a labels MIPS válidos: Class::method -> Class__method"""
    return name.replace("::", "__")


def _dbg(msg: str) -> None:
    print(f"[EMITTER] {msg}", file=sys.stdout)


# ---------------------------------------------------------------------
# Pequeño fix genérico para FramePlan basado en los parámetros del IR
# ---------------------------------------------------------------------
def _fixup_frame_plan_for_params(fn: Function, plan: FramePlan) -> FramePlan:
    """
    Garantiza que el FramePlan tenga homes de parámetros consistentes con el IR.

    - Completa plan.param_names si está vacío usando fn.params.
    - Sube need_param_homes a al menos min(len(params), 4) si venía muy bajo.
    - Reconstruye los offsets llamando de nuevo a plan.build().

    Esto es genérico: funciona para funciones normales, métodos y closures
    sin quemar nombres como 'Animal', 'Dog', 'pokeArray', etc.
    """
    ir_params = list(getattr(fn, "params", []) or [])
    param_names_from_ir: List[str] = []

    for idx, p in enumerate(ir_params):
        pname = getattr(p, "name", None) or getattr(p, "id", None)
        if not pname:
            pname = f"_p{idx}"
        param_names_from_ir.append(pname)

    # Si el planner no llenó param_names, usamos los del IR.
    if not getattr(plan, "param_names", None):
        plan.param_names = param_names_from_ir
    else:
        # Si la lista existente es más corta, la extendemos.
        if len(plan.param_names) < len(param_names_from_ir):
            extra = param_names_from_ir[len(plan.param_names):]
            plan.param_names.extend(extra)

    nparams = len(param_names_from_ir)
    desired_homes = min(nparams, 4)

    # Solo subimos need_param_homes; no lo bajamos si el planner ya lo dejó más alto.
    if plan.need_param_homes < desired_homes:
        plan.need_param_homes = desired_homes

    # Reconstruir layout (param_home_off, local_off, frame_size, etc.).
    if hasattr(plan, "build"):
        plan.build()

    return plan


# ---------------------------------------------------------------------
# Stubs muy simples usados en pruebas rápidas (no el pipeline real)
# ---------------------------------------------------------------------
def emit_program_stub(prog: Program) -> str:
    lines: List[str] = []
    lines.append(".data")
    lines.append("")
    lines.append(".text")
    lines.append(".globl main")
    lines.append("main:")
    lines.append("  li $v0, 10")
    lines.append("  syscall")
    return "\n".join(lines)


def emit_function_skeleton(func_name: str, plan: FramePlan) -> List[str]:
    """
    Esqueleto mínimo de función, útil para depuración rápida.
    Aquí no usamos $s* ni nada complejo.
    """
    label = _mangle_label(func_name)
    out: List[str] = []
    out.append(f"{label}:")
    out.extend(emit_prologue(plan.frame_size, save_s=[]))
    if getattr(plan, "need_param_homes", 0):
        homes = [plan.param_home_off[i] for i in range(plan.need_param_homes)]
        out.extend(emit_copy_params_to_homes(homes, plan.frame_size))
    epilogue_label = f"{label}__epilogue"
    out.append(f"{epilogue_label}:")
    out.extend(emit_epilogue(plan.frame_size, restore_s=[], exit_main=(func_name == "main")))
    return out


# ---------------------------------------------------------------------
# Emisión de función completa (con regalloc + plantillas)
# ---------------------------------------------------------------------
def emit_function(
    fn: Function,
    *,
    plan: FramePlan,
    layouts: LayoutRegistry | None = None,
    obj_types: Dict[str, str] | None = None,
    const_pool: Any | None = None,
    global_names: set[str] | None = None,
) -> str:
    label = _mangle_label(fn.name)

    ra = RegAlloc(plan)
    if obj_types is None:
        obj_types = {}

    # Conjunto de nombres globales (se lo pasa emit_full_program)
    if global_names is None:
        global_names = set()
    # Lo guardamos en el regalloc (luego regalloc.py lo usará para loads/stores)
    setattr(ra, "global_names", set(global_names))

    # Construcción lazy de layouts si hace falta
    if layouts is not None and not getattr(layouts, "_built", False):
        layouts.build_all()

    # ¿Esta función tiene llamadas?
    has_calls = any(
        isinstance(ins, (Call, CallClosure))
        for bb in getattr(fn, "blocks", []) for ins in bb.instrs
    )
    if has_calls:
        # Pinnear hasta 8 nombres en s-registers para reducir spills,
        # pero solo locales (no globals).
        globals_set = getattr(ra, "global_names", set())
        names_to_pin = sorted(
            [nm for nm in getattr(plan, "local_off", {}).keys() if nm not in globals_set]
        )[:8]
        ra.pin_names_to_sregs(names_to_pin)

    # ---- logging de debug amigable ----
    _dbg(f"fn={fn.name} frame_size(plan)={plan.frame_size} has_calls={has_calls}")
    try:
        _dbg(f"  s_regs_in_use={getattr(ra, 's_regs_in_use', [])}")
    except Exception:
        pass
    # NUEVO: nombres de parámetros que ve el emitter
    try:
        pnames = [
            getattr(p, "name", None) or getattr(p, "id", None) or str(p)
            for p in getattr(fn, "params", []) or []
        ]
        _dbg(f"  params={pnames}")
    except Exception:
        _dbg("  params=<no disponible>")
    try:
        locs = {k: plan.local_off[k] for k in sorted(plan.local_off.keys())}
        _dbg(f"  local_off={locs}")
    except Exception:
        _dbg("  local_off=<no disponible>")
    try:
        _dbg(f"  param_home_off={getattr(plan, 'param_home_off', {})}")
        _dbg(f"  need_param_homes={getattr(plan, 'need_param_homes', 0)}")
    except Exception:
        _dbg("  param_home_off=<no disponible>")

    # ----- Cálculo robusto del tamaño de frame -----
    frame_bytes = max(plan.frame_size, _MIN_FRAME_BYTES)

    # Asegurar que el frame cubre todas las homes negativas (param/local/spill)
    try:
        all_offs: List[int] = []
        ph = getattr(plan, "param_home_off", None)
        lo = getattr(plan, "local_off", None)
        if isinstance(ph, dict):
            all_offs.extend(ph.values())
        if isinstance(lo, dict):
            all_offs.extend(lo.values())
        all_offs.append(0)

        most_neg = min(all_offs)
        _dbg(f"  most_neg_offset={most_neg}")

        needed = -most_neg + 8  # 8 bytes para old $fp/$ra
        if needed > frame_bytes:
            _dbg(
                f"  [FIXUP-most_neg] frame_bytes {frame_bytes} -> {needed} "
                f"(most_neg={most_neg})"
            )
            frame_bytes = needed
    except Exception:
        _dbg("  [WARN] no se pudo calcular most_neg; usando frame_bytes tal cual")

    # Asegurar espacio extra para guardar/restaurar $s* (callee-saved)
    try:
        n_s = len(getattr(ra, "s_regs_in_use", []))
    except Exception:
        n_s = 0

    if n_s:
        neg_size = getattr(plan, "negative_size", 0)
        base_needed = neg_size + 8 + 4 * n_s  # params+locals+spills + fp/ra + s*
        if frame_bytes < base_needed:
            aligned = (base_needed + 7) & ~7  # alinear a 8
            _dbg(
                f"  [FIXUP-sregs] frame_bytes {frame_bytes} -> {aligned} "
                f"(negative_size={neg_size}, n_s={n_s})"
            )
            frame_bytes = aligned

    _dbg(f"  frame_bytes(final)={frame_bytes}")
    # -----------------------------------

    body: List[str] = []
    epilogue_label = f"{label}__epilogue"

    def _emit_with_caller_flush(ins, ra_local: RegAlloc, out_local: List[str]):
        # flush de caller antes de llamadas
        if isinstance(ins, (Call, CallClosure)):
            tgt = ins.func if isinstance(ins, Call) else "<closure>"
            _dbg(f"  call in {fn.name} -> {tgt} (argc={len(ins.args)})")
            names = sorted(list(ra_local.plan.local_off.keys()))
            _dbg(f"    flushing names: {names}")
            for nm in names:
                rcur = ra_local.reg_for_read(Name(nm), out_local)
                try:
                    ra_local.store_if_name(Name(nm), rcur, out_local)
                except Exception as e:
                    _dbg(f"    [WARN] store_if_name({nm}) lanzó {e!r}")

        emit_for_instr(
            ins,
            ra_local,
            out_local,
            epilogue_label=epilogue_label,
            layouts=layouts,
            obj_types=obj_types,
            fn_label=label,
            const_pool=const_pool,
        )
        ra_local.release_all_temps()

    # Recorremos el cuerpo y vamos llenando 'body'
    for bb in getattr(fn, "blocks", []):
        for ins in bb.instrs:
            if isinstance(ins, NewObject) and getattr(ins, "dst", None) is not None:
                obj_types[getattr(ins.dst, "name", "")] = ins.class_name
            _emit_with_caller_flush(ins, ra, body)

    # Ahora que ya tenemos el cuerpo, podemos emitir todo junto:
    out: List[str] = []
    out.append(f"{label}:")
    out.extend(
        emit_prologue(frame_bytes, save_s=getattr(ra, "s_regs_in_use", []))
    )

    # ------------------------------------------------------------------
    # COPIA DE PARÁMETROS A SUS "HOMES" EN EL FRAME (GENÉRICA)
    # ------------------------------------------------------------------
    ph = getattr(plan, "param_home_off", None)
    local_off = getattr(plan, "local_off", {}) or {}
    params = getattr(fn, "params", []) or []
    a_regs = ["$a0", "$a1", "$a2", "$a3"]
    need_param_homes = getattr(plan, "need_param_homes", 0)

    if isinstance(ph, dict) and need_param_homes:
        # Caso general guiado 100% por FramePlan: índices 0..need_param_homes-1
        for idx in range(need_param_homes):
            if idx >= len(a_regs):
                break
            off = ph.get(idx)
            if off is None:
                continue
            out.append(f"  sw {a_regs[idx]}, {off}($fp)")
    else:
        # Fallback: usar los parámetros del IR y local_off (por nombre)
        for idx, param in enumerate(params):
            if idx >= len(a_regs):
                break

            off = None

            if isinstance(ph, dict) and idx in ph:
                off = ph[idx]
            else:
                pname = getattr(param, "name", None) or getattr(param, "id", None)
                if pname and pname in local_off:
                    off = local_off[pname]

            if off is None:
                continue

            out.append(f"  sw {a_regs[idx]}, {off}($fp)")

    # Cuerpo de la función
    out.extend(body)

    # Epílogo
    out.append(f"{epilogue_label}:")
    out.extend(
        emit_epilogue(
            frame_bytes,
            restore_s=getattr(ra, "s_regs_in_use", []),
            exit_main=(fn.name == "main"),
        )
    )
    return "\n".join(out)


# ---------------------------------------------------------------------
# Helpers para sección .data
# ---------------------------------------------------------------------
def _escape_asciiz(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
    )


def _iter_string_pool_pairs(pool: Any) -> List[Tuple[str, str]]:
    """
    Devuelve [(label, string), ...] a partir del pool.

    Soporta:
      - StringPool actual (texto -> label, con atributo _order)
      - Diccionarios label->texto
      - Diccionarios texto->label
      - Método pool.pairs() que ya devuelva (label, texto)
    """

    def is_label(s: Any) -> bool:
        return isinstance(s, str) and bool(re.match(r"^__str_\d+$", s))

    def is_text(s: Any) -> bool:
        return isinstance(s, str) and not is_label(s)

    # --- Caso 1: StringPool “oficial”: _order (lista de textos) + _map (texto -> label)
    order = getattr(pool, "_order", None)
    smap = getattr(pool, "_map", None)
    if isinstance(order, list) and isinstance(smap, dict) and order:
        pairs: List[Tuple[str, str]] = []
        for s in order:
            lab = smap.get(s)
            if isinstance(lab, str):
                pairs.append((lab, s))   # (label, texto)
        return pairs

    # --- Caso 2: cualquier dict interno que parezca mapping de strings
    for _, val in vars(pool).items():
        if isinstance(val, dict) and val:
            items = list(val.items())
            k, v = items[0]

            # caso: label -> texto
            if is_label(k) and is_text(v):
                return [(lk, lv) for (lk, lv) in items]

            # caso: texto -> label
            if is_text(k) and is_label(v):
                # OJO: aquí sí devolvemos (label, texto)
                return [(v, k) for (k, v) in items]

    # --- Caso 3: método pairs() ya devuelve (label, texto)
    if hasattr(pool, "pairs"):
        try:
            pairs = list(pool.pairs())
            return pairs
        except Exception:
            pass

    return []


def _iter_globals(gtab: Any) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    for _, val in vars(gtab).items():
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(k, str) and isinstance(v, int):
                    out.append((k, v))
    return out


# ---------------------------------------------------------------------
# Emisión de programa completo (.data + .text)
# ---------------------------------------------------------------------
def emit_full_program(
    prog: Program,
    *,
    pool: Any,
    gtab: Any,
    plan_for_fn: Callable[[Function], FramePlan],
    layouts: LayoutRegistry | None = None,
) -> str:
    has_main = any(fn.name == "main" for fn in prog.functions)

    # ----- 0) Globals: nombres y valores -----
    global_pairs = _iter_globals(gtab)              # [(name, val), ...]
    global_names = {name for (name, _) in global_pairs}

    # ----- 1) Detectar métodos Clase::metodo o Clase__metodo -----
    method_impl: Dict[str, str] = {}
    for fn in prog.functions:
        cls: str | None = None
        meth: str | None = None

        if "::" in fn.name:
            cls, meth = fn.name.split("::", 1)
        elif "__" in fn.name:
            cls, meth = fn.name.split("__", 1)
        else:
            continue

        if not meth or meth == "constructor":
            continue

        impl_label = _mangle_label(fn.name)
        if meth not in method_impl:
            method_impl[meth] = impl_label

    # ----- 2) Orden de funciones: main primero si existe -----
    fn_order: List[Function] = []
    main_fn = next((fn for fn in prog.functions if fn.name == "main"), None)
    if main_fn is not None:
        fn_order.append(main_fn)
        fn_order.extend(fn for fn in prog.functions if fn is not main_fn)
    else:
        fn_order.extend(prog.functions)

    # ----- 3) Emitir todas las funciones -----
    text_chunks: List[str] = []

    for fn in fn_order:
        plan = plan_for_fn(fn)
        # FIX GENÉRICO: ajustar homes de parámetros en función de fn.params
        plan = _fixup_frame_plan_for_params(fn, plan)

        asm_fn = emit_function(
            fn,
            plan=plan,
            layouts=layouts,
            const_pool=pool,           # <- mismo pool para strings
            global_names=global_names,
        )

        _dbg(f"===== ASM for {fn.name} (frame(plan)={plan.frame_size}) =====")
        for i, ln in enumerate(asm_fn.splitlines()):
            if i >= 120:
                _dbg("  ... <truncated> ...")
                break
            print(f"    {ln}", file=sys.stdout)
        _dbg(f"===== END ASM for {fn.name} =====")

        text_chunks.append(asm_fn if asm_fn.endswith("\n") else asm_fn + "\n")

    # ----- 4) Sección .data -----
    lines: List[str] = []
    lines.append(".data")

    # Globals (mesmas que usará RegAlloc luego como labels)
    for name, val in global_pairs:
        lines.append(f"{name}: .word {val}")

    # String pool
    for label, lit in _iter_string_pool_pairs(pool):
        lines.append(f'{label}: .asciiz "{_escape_asciiz(lit)}"')

    # ----- 5) Sección .text -----
    lines.append("")
    lines.append(".text")
    if has_main:
        lines.append(".globl main")

    lines.extend(text_chunks)

    # runtime de closures
    runtime = emit_runtime_closures()
    if runtime and not runtime.endswith("\n"):
        runtime += "\n"
    lines.append(runtime)

    # runtime de arrays
    array_runtime = (
        "__new_array:\n"
        "  # $a0 = length (en elementos)\n"
        "  sll  $a0, $a0, 2       # *4 bytes por elemento\n"
        "  li   $v0, 9            # syscall sbrk\n"
        "  syscall\n"
        "  move $t0, $v0          # base del array también en $t0\n"
        "  jr   $ra\n"
        "\n"
    )
    lines.append(array_runtime)

    # ===== Runtime de STRINGS (genérico) =====
    str_runtime = (
        "# --- Runtime de strings ---\n"
        "__str_eq:\n"
        "  # a0 = s1, a1 = s2\n"
        "  move $t0, $a0          # ptr s1\n"
        "  move $t1, $a1          # ptr s2\n"
        "__str_eq_loop:\n"
        "  lbu  $t2, 0($t0)\n"
        "  lbu  $t3, 0($t1)\n"
        "  bne  $t2, $t3, __str_eq_not\n"
        "  beq  $t2, $zero, __str_eq_yes   # ambos son '\\0'\n"
        "  addiu $t0, $t0, 1\n"
        "  addiu $t1, $t1, 1\n"
        "  j    __str_eq_loop\n"
        "__str_eq_yes:\n"
        "  li   $v0, 1\n"
        "  jr   $ra\n"
        "__str_eq_not:\n"
        "  li   $v0, 0\n"
        "  jr   $ra\n"
        "\n"
        "__str_concat:\n"
        "  # a0 = s1, a1 = s2\n"
        "  move $t0, $a0          # s1\n"
        "  move $t1, $a1          # s2\n"
        "  # len(s1) en t2\n"
        "  move $t4, $t0\n"
        "  li   $t2, 0\n"
        "__str_len1_loop:\n"
        "  lbu  $t5, 0($t4)\n"
        "  beq  $t5, $zero, __str_len1_done\n"
        "  addiu $t2, $t2, 1\n"
        "  addiu $t4, $t4, 1\n"
        "  j    __str_len1_loop\n"
        "__str_len1_done:\n"
        "  # len(s2) en t3\n"
        "  move $t4, $t1\n"
        "  li   $t3, 0\n"
        "__str_len2_loop:\n"
        "  lbu  $t5, 0($t4)\n"
        "  beq  $t5, $zero, __str_len2_done\n"
        "  addiu $t3, $t3, 1\n"
        "  addiu $t4, $t4, 1\n"
        "  j    __str_len2_loop\n"
        "__str_len2_done:\n"
        "  # total = len1 + len2 + 1 (para '\\0') en t6\n"
        "  addu $t6, $t2, $t3\n"
        "  addiu $t6, $t6, 1\n"
        "  # pedir memoria con sbrk\n"
        "  li   $v0, 9\n"
        "  move $a0, $t6\n"
        "  syscall\n"
        "  move $t7, $v0          # dst\n"
        "  move $t4, $t7          # cursor de escritura\n"
        "  # copiar s1\n"
        "  move $t8, $t0\n"
        "__str_copy1_loop:\n"
        "  lbu  $t5, 0($t8)\n"
        "  beq  $t5, $zero, __str_copy1_done\n"
        "  sb   $t5, 0($t4)\n"
        "  addiu $t8, $t8, 1\n"
        "  addiu $t4, $t4, 1\n"
        "  j    __str_copy1_loop\n"
        "__str_copy1_done:\n"
        "  # copiar s2\n"
        "  move $t8, $t1\n"
        "__str_copy2_loop:\n"
        "  lbu  $t5, 0($t8)\n"
        "  beq  $t5, $zero, __str_copy2_done\n"
        "  sb   $t5, 0($t4)\n"
        "  addiu $t8, $t8, 1\n"
        "  addiu $t4, $t4, 1\n"
        "  j    __str_copy2_loop\n"
        "__str_copy2_done:\n"
        "  # terminador nulo\n"
        "  sb   $zero, 0($t4)\n"
        "  move $v0, $t7\n"
        "  jr   $ra\n"
        "\n"
    )
    lines.append(str_runtime)

    # ----- 6) Stubs de llamadas a métodos: __mcall__metodo -----
    if method_impl:
        lines.append("# --- Runtime stubs para llamadas a métodos (__mcall__X) ---")
        for meth, impl_label in method_impl.items():
            lines.append(f"__mcall__{meth}:")
            lines.append("  # Stub simple: estáticamente llama a " + impl_label)
            lines.append(f"  jal {impl_label}")
            lines.append("  jr  $ra")
            lines.append("")

    asm = "\n".join(lines)
    asm = _append_stubs_for_missing_functions(asm)
    return asm
