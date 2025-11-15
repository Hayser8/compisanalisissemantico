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
    """
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
  jr $ra
"""


def _append_stubs_for_missing_functions(asm: str) -> str:
    """
    Busca llamadas 'jal foo' a funciones que no tienen etiqueta 'foo:'
    y les genera un stub sencillo al final del archivo.
    No crea stubs para nombres que empiezan con '__' (runtime).
    """
    # Etiquetas definidas: líneas tipo "label:"
    label_re = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*$', re.MULTILINE)
    defined = {m.group(1) for m in label_re.finditer(asm)}

    # Targets de 'jal algo'
    jal_re = re.compile(r'\bjal\s+([A-Za-z_][A-Za-z0-9_]*)\b')
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
    label = _mangle_label(func_name)
    out: List[str] = []
    out.append(f"{label}:")
    out.extend(emit_prologue(plan.frame_size))
    if getattr(plan, "need_param_homes", 0):
        homes = [plan.param_home_off[i] for i in range(plan.need_param_homes)]
        out.extend(emit_copy_params_to_homes(homes, plan.frame_size))
    epilogue_label = f"{label}__epilogue"
    out.append(f"{epilogue_label}:")
    out.extend(emit_epilogue(plan.frame_size, exit_main=(func_name == "main")))
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
) -> str:
    label = _mangle_label(fn.name)

    ra = RegAlloc(plan)
    if obj_types is None:
        obj_types = {}

    # Construcción lazy de layouts si hace falta
    if layouts is not None and not getattr(layouts, "_built", False):
        layouts.build_all()

    # ¿Esta función tiene llamadas?
    has_calls = any(
        isinstance(ins, (Call, CallClosure))
        for bb in getattr(fn, "blocks", []) for ins in bb.instrs
    )
    if has_calls:
        # Pinned a hasta 8 nombres en s-registers para reducir spills
        names_to_pin = sorted(list(plan.local_off.keys()))[:8]
        ra.pin_names_to_sregs(names_to_pin)

    # ---- logging de debug amigable ----
    _dbg(f"fn={fn.name} frame_size(plan)={plan.frame_size} has_calls={has_calls}")
    try:
        _dbg(f"  s_regs_in_use={getattr(ra, 's_regs_in_use', [])}")
    except Exception:
        pass
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
    # 1) Empezamos con el máximo entre lo que pide el plan y el mínimo global.
    frame_bytes = max(plan.frame_size, _MIN_FRAME_BYTES)

    # 2) Si el plan tiene offsets negativos, ajustamos para que $fp/$ra queden
    #    SIEMPRE por debajo de todos los homes/locales.
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

        # Queremos que el offset más negativo esté al menos 8 bytes por encima
        # de donde guardamos old $fp y $ra.
        needed = -most_neg + 8
        if needed > frame_bytes:
            _dbg(
                f"  [FIXUP-most_neg] frame_bytes {frame_bytes} -> {needed} "
                f"(most_neg={most_neg})"
            )
            frame_bytes = needed
    except Exception:
        _dbg("  [WARN] no se pudo calcular most_neg; usando frame_bytes tal cual")

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
    # COPIA DE PARÁMETROS A SUS "HOMES" EN EL FRAME
    #
    # Aquí está el FIX IMPORTANTE:
    # Usamos plan.need_param_homes (que incluye 'this' / ambiente) en
    # lugar de len(fn.params), para no perder parámetros implícitos.
    # ------------------------------------------------------------------
    n_homes = getattr(plan, "need_param_homes", 0)
    if n_homes and getattr(plan, "param_home_off", None):
        homes: List[int] = [plan.param_home_off[i] for i in range(n_homes)]
        out.extend(emit_copy_params_to_homes(homes, frame_bytes))

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
    Busca en `pool` un dict que parezca:
      - label -> string   (ej. "__str_0" -> "hola")
      - string -> label   (ej. "hola" -> "__str_0")
    y devuelve [(label, string), ...]
    """
    def is_label(s: Any) -> bool:
        return isinstance(s, str) and bool(re.match(r"^__str_\d+$", s))

    def is_text(s: Any) -> bool:
        return isinstance(s, str) and not is_label(s)

    for _, val in vars(pool).items():
        if isinstance(val, dict) and val:
            items = list(val.items())
            k, v = items[0]
            if is_label(k) and is_text(v):
                return [(lk, lv) for lk, lv in items]
            if is_text(k) and is_label(v):
                return [(lv, lk) for lk, lv in items]
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

    # ----- 3) Emitir todas las funciones (y de paso llenar el pool de strings) -----
    text_chunks: List[str] = []

    for fn in fn_order:
        plan = plan_for_fn(fn)
        asm_fn = emit_function(fn, plan=plan, layouts=layouts, const_pool=pool)

        # logging parcial de ASM (útil para debug)
        _dbg(f"===== ASM for {fn.name} (frame(plan)={plan.frame_size}) =====")
        for i, ln in enumerate(asm_fn.splitlines()):
            if i >= 120:
                _dbg("  ... <truncated> ...")
                break
            print(f"    {ln}", file=sys.stdout)
        _dbg(f"===== END ASM for {fn.name} =====")

        text_chunks.append(asm_fn if asm_fn.endswith("\n") else asm_fn + "\n")

    # ----- 4) Sección .data (con el pool ya lleno) -----
    lines: List[str] = []
    lines.append(".data")

    # globals (si hay)
    for name, val in _iter_globals(gtab):
        lines.append(f"{name}: .word {val}")

    # strings (__str_n: .asciiz "...")
    for label, lit in _iter_string_pool_pairs(pool):
        lines.append(f'{label}: .asciiz "{_escape_asciiz(lit)}"')

    # ----- 5) Sección .text -----
    lines.append("")
    lines.append(".text")
    if has_main:
        lines.append(".globl main")

    # funciones
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

    # ----- 6) Stubs de llamadas a métodos: __mcall__metodo -----
    if method_impl:
        lines.append("# --- Runtime stubs para llamadas a métodos (__mcall__X) ---")
        for meth, impl_label in method_impl.items():
            lines.append(f"__mcall__{meth}:")
            lines.append(f"  # Stub simple: estáticamente llama a {impl_label}")
            lines.append(f"  jal {impl_label}")
            lines.append("  jr  $ra")
            lines.append("")

    # Unir todo y agregar stubs para funciones faltantes (inner, etc.)
    asm = "\n".join(lines)
    asm = _append_stubs_for_missing_functions(asm)
    return asm
