# program/cli.py
import sys, json, argparse, os
from typing import Any, Dict, List

# ---- Fase de parseo (tu helper existente) ----
from src.frontend.parser_util import parse_code

# ---- Semántica (ya en tu proyecto) ----
from src.sema.errors import ErrorReporter
from src.sema.decl_collector import DeclarationCollector
from src.sema.type_linker import TypeLinker
from src.sema.typecheck_visitor import TypeCheckVisitor
from src.sema.symbols import (
    Symbol, VariableSymbol, ConstSymbol, FieldSymbol, ParamSymbol,
    FunctionSymbol, ClassSymbol
)

# ---- AST → IR (nuevo en esta fase) ----
from src.ast.builder_visitor import ASTBuilder
from src.ir.lower_from_ast import lower_program as ast_lower_to_tuples
from src.ir.adapter import IRAdapter
from src.ir.pretty import program_to_str as ir_to_str


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
    # Globales
    g = []
    for name, sym in dc.global_scope.items():
        if isinstance(sym, (VariableSymbol, ConstSymbol, FieldSymbol)):
            g.append({"name": name, "kind": sym.kind, "type": _tostr(getattr(sym, "resolved_type", None))})
        elif isinstance(sym, FunctionSymbol):
            g.append({"name": name, "kind": "func", "ret": _tostr(sym.resolved_return), "captured": sorted(list(sym.captured))})
        elif isinstance(sym, ClassSymbol):
            g.append({"name": name, "kind": "class", "base": getattr(sym, "base_name", None)})

    # Clases
    classes = {}
    for cname, cscope in dc.class_scopes.items():
        members = []
        for mname, msym in cscope.items():
            if isinstance(msym, FieldSymbol):
                members.append({"name": mname, "kind": "field", "type": _tostr(msym.resolved_type), "mutable": getattr(msym, "mutable", True)})
            elif isinstance(msym, FunctionSymbol):
                members.append({"name": mname, "kind": "method", "ret": _tostr(msym.resolved_return)})
        classes[cname] = members

    # Func scopes (para ver params y capturas)
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
    dc = DeclarationCollector(rep); dc.visit(tree)
    TypeLinker(rep, dc).link()
    TypeCheckVisitor(rep, dc).visit(tree)
    return rep, dc, tree

def build_ir_from_tree(tree) -> str:
    """
    Construye AST → lowering a tuplas → IR (Program) → pretty string.
    Lanza excepciones si algo interno falla (no entra aquí si hay errores semánticos).
    """
    ast = ASTBuilder().visit(tree)
    fn_tuples = ast_lower_to_tuples(ast)  # List[(name, params, body_tuples)]
    adapter = IRAdapter.new()
    for fname, params, body in fn_tuples:
        adapter.emit_function(fname, params, body)
    return ir_to_str(adapter.program)

def main():
    ap = argparse.ArgumentParser(description="Compilador (semántica + IR) de Compiscript")
    ap.add_argument("file", nargs="?", help="Archivo .cps a analizar (si se omite, lee stdin)")
    ap.add_argument("--json", action="store_true", help="Salida JSON (para IDE/tools)")
    ap.add_argument("--symbols", action="store_true", help="Incluir tabla de símbolos")
    ap.add_argument("--emit-ir", action="store_true", help="Generar y devolver IR (TAC) si no hay errores")
    args = ap.parse_args()

    src = open(args.file, "r", encoding="utf-8").read() if args.file else sys.stdin.read()
    rep, dc, tree = analyze_source(src)

    # JSON (consumido por tu IDE)
    if args.json:
        payload = {
            "ok": not rep.has_errors(),
            "errors": _serialize_errors(rep),
            "symbols": _serialize_symbols(dc) if args.symbols else None,
        }
        # si piden IR y no hay errores, lo agregamos
        if args.emit_ir and not rep.has_errors():
            try:
                payload["ir"] = build_ir_from_tree(tree)
            except Exception as ex:
                # protegemos al IDE: reportamos el fallo del backend de IR como error suave
                payload["ok"] = False
                payload["errors"].append({"code": "IRGEN", "message": f"Fallo generando IR: {ex}", "line": None, "col": None})
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        # Conserva convención de salida
        sys.exit(0 if not rep.has_errors() else 1)

    # Modo humano (stdout)
    if rep.has_errors():
        print(rep.summary())
        sys.exit(1)
    else:
        print("OK ✅  (sin errores)")
        if args.symbols:
            print(json.dumps(_serialize_symbols(dc), ensure_ascii=False, indent=2))
        if args.emit_ir:
            print("\n--- IR (TAC) ---")
            print(build_ir_from_tree(tree))

if __name__ == "__main__":
    main()
