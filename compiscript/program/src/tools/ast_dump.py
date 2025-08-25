# src/tools/ast_dump.py
from __future__ import annotations
import sys
from antlr4 import FileStream, CommonTokenStream
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from src.ast.builder_visitor import ASTBuilder
from src.ast.dot_export import ASTDotExporter

def main(argv):
    if len(argv) < 2:
        print("Uso: python -m src.tools.ast_dump <archivo.cps>", file=sys.stderr)
        sys.exit(1)
    path = argv[1]
    input_stream = FileStream(path, encoding="utf-8")
    lexer = CompiscriptLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    tree = parser.program()

    ast = ASTBuilder().visit(tree)
    dot = ASTDotExporter().to_dot(ast)
    print(dot)

if __name__ == "__main__":
    main(sys.argv)
