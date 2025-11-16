# compiscript/program/cli.py
import sys, json, argparse, os, subprocess, tempfile
from typing import Any, Dict, List, Tuple, Optional

from src.ir.annotate_globals import annotate_globals
from src.ir.debug_global import debug_dump_globals

# ---- Fase de parseo (tu helper existente) ----
from src.frontend.parser_util import parse_code

# ---- Semántica (ya en tu proyecto) ----
from src.sema.errors import ErrorReporter
from src.sema.decl_collector import DeclarationCollector
from src.sema.type_linker import TypeLinker
from src.sema.typecheck_visitor import TypeCheckVisitor
from src.sema.symbols import (
    VariableSymbol, ConstSymbol, FieldSymbol, ParamSymbol,
    FunctionSymbol, ClassSymbol
)

# ---- AST → IR ----
from src.ast.builder_visitor import ASTBuilder
from src.ir.lower_from_ast import lower_program as ast_lower_to_tuples
from src.ir.adapter import IRAdapter
from src.ir.pretty import program_to_str as ir_to_str

# ---- IR model ----
from src.ir.model import (
    Program, Function, Instr, LabelInstr, Goto, IfGoto, Assign, UnaryOp, BinOp, Return,
    Call, Load, Store, GetProp, SetProp, NewObject, Operand, Temp, Name, Const, Label,
    MakeClosure, CallClosure
)

# ---- Backend MIPS ----
from src.backend.mips.emitter import emit_full_program
from src.backend.mips.data import StringPool, GlobalsTable

WORD = 4  # tamaño de palabra en MIPS

# ============================================================
# Utilidades
# ============================================================

def _tostr(t) -> str:
    return str(t) if t is not None else "None"


def _serialize_errors(rep: ErrorReporter) -> List[Dict[str, Any]]:
    out = []
    for e in rep.errors:
        out.append({
            "code": e.code,
            "message": e.message,
            "line": getattr(e, "line", None),
            "col": getattr(e, "col", None),
        })
    return out


def _serialize_symbols(dc: DeclarationCollector) -> Dict[str, Any]:
    g = []
    for name, sym in dc.global_scope.items():
        if isinstance(sym, (VariableSymbol, ConstSymbol, FieldSymbol)):
            g.append({
                "name": name,
                "kind": sym.kind,
                "type": _tostr(getattr(sym, "resolved_type", None))
            })
        elif isinstance(sym, FunctionSymbol):
            g.append({
                "name": name,
                "kind": "func",
                "ret": _tostr(sym.resolved_return),
                "captured": sorted(list(sym.captured))
            })
        elif isinstance(sym, ClassSymbol):
            g.append({
                "name": name,
                "kind": "class",
                "base": getattr(sym, "base_name", None)
            })

    classes = {}
    for cname, cscope in dc.class_scopes.items():
        members = []
        for mname, msym in cscope.items():
            if isinstance(msym, FieldSymbol):
                members.append({
                    "name": mname,
                    "kind": "field",
                    "type": _tostr(msym.resolved_type),
                    "mutable": getattr(msym, "mutable", True)
                })
            elif isinstance(msym, FunctionSymbol):
                members.append({
                    "name": mname,
                    "kind": "method",
                    "ret": _tostr(msym.resolved_return)
                })
        classes[cname] = members

    funcs = {}
    for key, fscope in dc.function_scopes.items():
        params = []
        fsym = None
        if fscope.parent:
            fsym = fscope.parent.resolve_local(fscope.name)
        for pname, psym in fscope.items():
            if isinstance(psym, ParamSymbol):
                params.append({"name": pname, "type": _tostr(psym.resolved_type)})
        funcs[key] = {
            "params": params,
            "return": _tostr(getattr(fsym, "resolved_return", None)) if fsym else None,
            "captured": sorted(list(getattr(fsym, "captured", set()))) if fsym else [],
        }
    return {"globals": g, "classes": classes, "functions": funcs}


def analyze_source(source: str):
    rep = ErrorReporter()
    _, tree = parse_code(source)
    dc = DeclarationCollector(rep)
    dc.visit(tree)
    TypeLinker(rep, dc).link()
    TypeCheckVisitor(rep, dc).visit(tree)
    return rep, dc, tree


def build_ir_from_tree(tree) -> str:
    """
    Versión usada sólo para el modo --json (no necesitamos annotate aquí).
    """
    ast = ASTBuilder().visit(tree)
    fn_tuples = ast_lower_to_tuples(ast)
    adapter = IRAdapter.new()
    for fname, params, body in fn_tuples:
        adapter.emit_function(fname, params, body)
    return ir_to_str(adapter.program)


# ============================================================
# Layouts para objetos
# ============================================================

class SimpleLayoutRegistry:
    """
    Provee offsets de campos y tamaños de objetos al backend MIPS.

    - _field_offsets: Dict[strClass, Dict[fieldName, offset]]
    - _obj_sizes:     Dict[strClass, int]
    - obj_types:      Dict[strTempOrName, strClass]  (inyectado desde IR)
    """
    def __init__(self, field_offsets: Dict[str, Dict[str, int]], obj_sizes: Dict[str, int]):
        self._field_offsets = field_offsets
        self._obj_sizes = obj_sizes
        self._built = False
        self.obj_types: Dict[str, str] = {}

    def build_all(self):
        self._built = True

    # --- Tamaños ---

    def obj_size(self, *args, **kwargs) -> int:
        """
        Acepta:
          - obj_size(class_name="Clase")
          - obj_size("Clase")
          - obj_size(cls="Clase")
        """
        cls = kwargs.get("class_name") or kwargs.get("cls")
        if cls is None:
            if len(args) == 1:
                cls = args[0]
            else:
                print("[LAYOUT] WARN: obj_size sin class_name; devolviendo 4.")
                return 4
        return self._obj_sizes.get(cls, 4)

    def object_size(self, *args, **kwargs) -> int:
        return self.obj_size(*args, **kwargs)

    # --- Offsets de campos ---

    def field_offset(self, *args, **kwargs) -> int:
        """
        Acepta:
          - field_offset(cls, field)
          - field_offset(field, class_name=cls)
          - field_offset(cls=..., field=...) / field_offset(name=...)

        'field' puede ser string u objeto con atributo .name.

        Si no se pasa clase, intenta resolver por unicidad; si no puede,
        devuelve 0 y emite un WARN (no tira TypeError).
        """
        cls = kwargs.get("class_name") or kwargs.get("cls")
        field = kwargs.get("field") or kwargs.get("name")

        # Reacomodar args posicionales
        if cls is None and field is None and len(args) == 2:
            cls, field = args[0], args[1]
        elif field is None and len(args) == 1:
            field = args[0]

        # Normalizar nombre de campo
        if field is not None and not isinstance(field, str):
            field = getattr(field, "name", field)

        # Sin clase explícita: buscar por unicidad
        if cls is None:
            matches: List[Tuple[str, int]] = []
            for kls, fmap in self._field_offsets.items():
                if field in fmap:
                    matches.append((kls, fmap[field]))
            if len(matches) == 1:
                return matches[0][1]
            print(f"[LAYOUT] WARN: field_offset('{field}') ambiguo o desconocido; usando 0.")
            return 0

        # Con clase conocida
        fmap = self._field_offsets.get(cls, {})
        if field in fmap:
            return fmap[field]
        print(f"[LAYOUT] WARN: '{field}' no existe en clase '{cls}'; usando 0.")
        return 0


def _build_layouts_from_dc(dc: DeclarationCollector) -> SimpleLayoutRegistry:
    field_offsets: Dict[str, Dict[str, int]] = {}
    obj_sizes: Dict[str, int] = {}
    for cname, scope in dc.class_scopes.items():
        fields_in_order: List[str] = []
        for mname, msym in scope.items():
            if isinstance(msym, FieldSymbol):
                fields_in_order.append(mname)
        fmap: Dict[str, int] = {fname: i * WORD for i, fname in enumerate(fields_in_order)}
        field_offsets[cname] = fmap
        size = max(WORD, len(fields_in_order) * WORD)
        obj_sizes[cname] = size
    return SimpleLayoutRegistry(field_offsets, obj_sizes)


# ============================================================
# Tipos de objeto aproximados desde IR (para GetProp/SetProp)
# ============================================================

def _infer_obj_types(prog: Program) -> Dict[str, str]:
    types: Dict[str, str] = {}

    def _key_of(op: Operand) -> Optional[str]:
        if isinstance(op, Name):
            return op.name
        if isinstance(op, Temp):
            return op.name
        return None

    changed = True
    while changed:
        changed = False
        for fn in prog.functions:
            # OJO: tu Function usa .blocks; aquí asumimos que ya está adaptado
            instrs: List[Instr] = []
            for bb in getattr(fn, "blocks", []):
                instrs.extend(bb.instrs)

            for ins in instrs:
                if isinstance(ins, NewObject):
                    k = _key_of(ins.dst)
                    if k and k not in types:
                        types[k] = ins.class_name
                        changed = True
                elif isinstance(ins, Assign):
                    src_k = _key_of(ins.src)
                    dst_k = _key_of(ins.dst)
                    if src_k and dst_k and src_k in types and types.get(dst_k) != types[src_k]:
                        types[dst_k] = types[src_k]
                        changed = True
    return types


# ============================================================
# Plan de frame simple (homes de parámetros en offsets negativos)
# ============================================================

class SimpleFramePlan:
    def __init__(
        self,
        fn: Function,
        frame_size: int,
        local_off: Dict[str, int],
        param_home_off: Dict[int, int],
    ):
        self.fn = fn
        self.name = fn.name
        self.frame_size = frame_size
        self.local_off = local_off
        self.param_home_off = param_home_off

        # En tu IR los params suelen ser strings; normalizamos a lista de nombres
        self.param_names: List[Any] = list(getattr(fn, "params", []))

        self.need_param_homes: int = len(param_home_off)

        self.s_regs_in_use: List[str] = []

        # Campos para compatibilidad con el backend "real"
        self.spill_bytes: int = 0
        self._spill_used_bytes: int = 0
        self.saved_s_size: int = 0
        self.saved_ra_fp_size: int = 8


def _plan_for(fn: Function) -> SimpleFramePlan:
    # Parámetros explícitos según el IR (lo que sale en function sum2(x, y), etc.)
    nparams_ir = len(fn.params) if hasattr(fn, "params") else 0

    name = fn.name
    # Consideramos "método" a funciones con Class::metodo o Class__metodo
    # pero ignoramos nombres de runtime que empiezan con "__".
    is_method = ("::" in name) or ("__" in name and not name.startswith("__"))

    # 1) Homes de parámetros EXPLÍCITOS: -4, -8, -12, ...
    param_homes: Dict[int, int] = {i: -(4 * (i + 1)) for i in range(nparams_ir)}

    # 2) Locals: aquí vamos a reservar un slot para 'this' en métodos.
    local_offsets: Dict[str, int] = {}

    if is_method:
        # Slot local para 'this' justo debajo de los parámetros:
        # si hay 0 params → this en -4($fp)
        # si hay 1 param  → this en -8($fp), etc.
        local_offsets["this"] = -(4 * (nparams_ir + 1))

    # 3) Tamaño base del frame (param homes + locals + 8 bytes de $fp/$ra)
    total_slots = nparams_ir + len(local_offsets)  # cada slot = 4 bytes
    base_bytes = 4 * total_slots + 8              # +8 para fp/ra

    if base_bytes <= 0:
        base_bytes = 8
    # Alinear a múltiplo de 4
    if base_bytes % 4 != 0:
        base_bytes += (4 - base_bytes % 4)

    # Algo de margen; emit_function luego sube esto al mínimo global de 256 bytes
    frame_size = max(16, base_bytes)

    return SimpleFramePlan(fn, frame_size, local_offsets, param_homes)


# ============================================================
# Emisión de ASM MIPS (inyectando layouts + obj_types)
# ============================================================

def emit_mips_asm(prog: Program, layouts=None) -> str:
    # Pool real de strings (.asciiz) y tabla real de globales (.word)
    pool = StringPool()
    gtab = GlobalsTable()

    # Registrar globales descubiertas por annotate_globals
    for name in getattr(prog, "global_vars", set()):
        # Por ahora, todas como .word 0 (scalar de 4 bytes)
        gtab.define_word(name, 0)

    # Layouts para objetos (si no te pasaron uno)
    if layouts is None:
        layouts = SimpleLayoutRegistry(field_offsets={}, obj_sizes={})

    # Inferencia aprox de tipos de objeto (para GetProp/SetProp)
    try:
        obj_types = _infer_obj_types(prog)
    except Exception:
        obj_types = {}
    setattr(layouts, "obj_types", obj_types)

    # Emitir el programa MIPS completo
    asm = emit_full_program(
        prog,
        pool=pool,
        gtab=gtab,
        plan_for_fn=_plan_for,
        layouts=layouts,
    )
    return asm


# ============================================================
# Correr MARS (si está disponible)
# ============================================================

def _find_mars_jar() -> Optional[str]:
    env = os.environ.get("MARS_JAR")
    if env and os.path.exists(env):
        return env
    for p in [
        "src/tools/Mars4_5.jar", "/mars/Mars.jar", "/opt/mars/Mars.jar",
        "/opt/Mars.jar", "/tools/Mars.jar", "Mars.jar", "Mars4_5.jar"
    ]:
        if os.path.exists(p):
            return p
    return None


def run_in_mars(asm_text: str) -> int:
    import shutil

    # 1) Guardar en directorio temporal
    tmpdir = tempfile.mkdtemp(prefix="cps_mars_")
    asm_path = os.path.join(tmpdir, "out.asm")
    with open(asm_path, "w", encoding="utf-8") as f:
        f.write(asm_text)

    # 2) Copia adicional a un archivo estable en el proyecto
    try:
        stable_path = os.path.join(os.getcwd(), "out_last.asm")
        shutil.copy(asm_path, stable_path)
        print(f"[MARS] Copié ASM a {stable_path}")
    except Exception as ex:
        print(f"[MARS] WARN: no se pudo copiar ASM fijo: {ex}")

    # 3) Localizar el JAR de MARS
    mars = _find_mars_jar()
    if mars is None:
        print(
            f"[MARS] JAR no encontrado. ASM guardado en:\n"
            f"  {asm_path}\n"
            f"Ábrelo manualmente en MARS."
        )
        return 0

    # 4) Ejecutar MARS sobre el ASM
    cmd = ["java", "-jar", mars, asm_path]
    print(f"[MARS] Ejecutando: {' '.join(cmd)}")

    try:
        rc = subprocess.call(cmd)
        if rc == 0:
            print("[MARS] Ejecución completada correctamente (rc=0).")
        else:
            print(f"[MARS] MARS terminó con código {rc}. ASM en: {asm_path}")
        return rc
    except Exception as ex:
        print(f"[MARS] No se pudo ejecutar MARS: {ex}\nASM en: {asm_path}")
        return 1


# ============================================================
# Main CLI
# ============================================================

def main():
    ap = argparse.ArgumentParser(description="Compilador (semántica + IR + MIPS) de Compiscript")
    ap.add_argument("file", nargs="?", help="Archivo .cps a analizar (si se omite, lee stdin)")
    ap.add_argument("--json", action="store_true", help="Salida JSON (para IDE/tools)")
    ap.add_argument("--symbols", action="store_true", help="Incluir tabla de símbolos")
    ap.add_argument("--emit-ir", action="store_true", help="Generar y devolver IR (TAC)")
    ap.add_argument("--emit-mips", action="store_true", help="Generar MIPS")
    ap.add_argument("--run-mars", action="store_true", help="Generar MIPS y abrir/ejecutar en MARS")
    args = ap.parse_args()

    src = open(args.file, "r", encoding="utf-8").read() if args.file else sys.stdin.read()
    rep, dc, tree = analyze_source(src)

    # --- Modo JSON (para IDE) ---
    if args.json:
        payload = {
            "ok": not rep.has_errors(),
            "errors": _serialize_errors(rep),
            "symbols": _serialize_symbols(dc) if args.symbols else None,
        }
        if args.emit_ir and not rep.has_errors():
            try:
                payload["ir"] = build_ir_from_tree(tree)
            except Exception as ex:
                payload["ok"] = False
                payload["errors"].append({
                    "code": "IRGEN",
                    "message": f"Fallo generando IR: {ex}",
                    "line": None,
                    "col": None,
                })
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.exit(0 if not rep.has_errors() else 1)

    # Si hubo errores semánticos, salimos
    if rep.has_errors():
        print(rep.summary())
        sys.exit(1)

    print("OK  (sin errores)")
    if args.symbols:
        print(json.dumps(_serialize_symbols(dc), ensure_ascii=False, indent=2))

    # === Lowering a IR objeto (UNA sola vez) ===
    try:
        ast = ASTBuilder().visit(tree)
        fn_tuples = ast_lower_to_tuples(ast)
        adapter = IRAdapter.new()
        for fname, params, body in fn_tuples:
            adapter.emit_function(fname, params, body)
        prog: Program = adapter.program
    except Exception as ex:
        print(f"[IR] Error en lowering/adapter: {ex}")
        sys.exit(1)

    # === Anotar globales en el IR ===
    try:
        annotate_globals(prog)
    except Exception as ex:
        print(f"[IR] WARN: annotate_program falló: {ex}")

    # === IR pretty + debug de globales si se pide --emit-ir ===
    if args.emit_ir:
        try:
            debug_dump_globals(prog)
        except Exception as ex:
            print(f"[DEBUG] Error en debug_dump_globals: {ex}")
        print("\n--- IR (TAC) ---")
        print(ir_to_str(prog))

    # === Layouts desde símbolos ===
    layouts = _build_layouts_from_dc(dc)
    layouts.build_all()

    # === ASM MIPS / MARS ===
    if args.emit_mips or args.run_mars:
        try:
            asm_text = emit_mips_asm(prog, layouts=layouts)
        except Exception as ex:
            print(f"[MIPS] Error generando ASM: {ex}")
            sys.exit(1)

        print("\n--- MIPS ASM ---")
        print(asm_text)

        if args.run_mars:
            rc = run_in_mars(asm_text)
            sys.exit(rc)

    sys.exit(0)


if __name__ == "__main__":
    main()
