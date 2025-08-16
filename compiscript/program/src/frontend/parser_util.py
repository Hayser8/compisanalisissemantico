# program/src/frontend/parser_util.py
from __future__ import annotations
from antlr4 import InputStream, CommonTokenStream
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser

def parse_code(text: str):
    inp = InputStream(text)
    lexer = CompiscriptLexer(inp)
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    tree = parser.program()
    return parser, tree
