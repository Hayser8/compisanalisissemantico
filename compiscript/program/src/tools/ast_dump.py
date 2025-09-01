# src/tools/ast_dump.py
from __future__ import annotations
import sys, subprocess
from antlr4 import FileStream, CommonTokenStream
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from src.ast.builder_visitor import ASTBuilder
from src.ast.dot_export import ASTDotExporter

def _emit_dot_to_stdout(dot: str) -> None:
    # Quita BOM si viniera colado y normaliza finales de línea
    s = dot.lstrip("\ufeff").replace("\r\n", "\n")
    # Escribe binario UTF-8 "crudo" (evita recodificaciones de la consola)
    sys.stdout.buffer.write(s.encode("utf-8"))

def _emit_png_via_dot(dot: str, png_path: str) -> int:
    s = dot.lstrip("\ufeff").replace("\r\n", "\n").encode("utf-8")
    # Requiere 'dot' (Graphviz) en PATH
    proc = subprocess.run(
        ["dot", "-Tpng", "-o", png_path],
        input=s,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr.decode("utf-8", errors="replace"))
    return proc.returncode

def main(argv):
    if len(argv) < 2 or argv[1].startswith("-"):
        sys.stderr.write("Uso:\n")
        sys.stderr.write("  python -m src.tools.ast_dump <archivo.cps>\n")
        sys.stderr.write("  python -m src.tools.ast_dump <archivo.cps> --png <salida.png>\n")
        sys.exit(1)

    path = argv[1]
    out_mode_png = (len(argv) >= 4 and argv[2] == "--png")
    out_png_path = argv[3] if out_mode_png else None

    input_stream = FileStream(path, encoding="utf-8")
    lexer = CompiscriptLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    tree = parser.program()

    ast = ASTBuilder().visit(tree)
    dot = ASTDotExporter().to_dot(ast)

    if out_mode_png:
        rc = _emit_png_via_dot(dot, out_png_path)
        sys.exit(rc)
    else:
        _emit_dot_to_stdout(dot)

if __name__ == "__main__":
    main(sys.argv)
