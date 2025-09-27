# program/src/sema/tests/test_switch_strings.py
from antlr4 import InputStream, CommonTokenStream
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from program.src.sema.errors import ErrorReporter, E_OP_TYPES, E_DUPLICATE_ID
from program.src.sema.decl_collector import DeclarationCollector
from program.src.sema.type_linker import TypeLinker
from program.src.sema.typecheck_visitor import TypeCheckVisitor


def _analyze(source: str):
    """
    Corre el pipeline semántico sobre 'source' y retorna (reporter, tree)
    """
    inp = InputStream(source)
    lex = CompiscriptLexer(inp)
    tokens = CommonTokenStream(lex)
    parser = CompiscriptParser(tokens)
    tree = parser.program()

    rep = ErrorReporter()
    decl = DeclarationCollector(rep)
    decl.visit(tree)

    # Vincula tipos de anotaciones/param/retorno
    TypeLinker(rep, decl).link()

    # Chequeo de tipos
    TypeCheckVisitor(rep, decl).visit(tree)
    return rep, tree


def test_switch_string_ok():
    src = r'''
        var x: string = "b";
        switch (x) {
          case "a": { var y: integer = 1; }
          case "b": { var z: integer = 2; }
          default: { var w: integer = 3; }
        }
    '''
    rep, _ = _analyze(src)
    assert not rep.has_errors(), f"no debería fallar, errores: {rep.summary()}"


def test_switch_cond_no_string():
    src = r'''
        var x: integer = 10;
        switch (x) {  // x NO es string
          case "a": { }
        }
    '''
    rep, _ = _analyze(src)
    # Debe haber al menos un error de tipos por condición no-string
    assert any(e.code == E_OP_TYPES and "switch requiere 'string'" in e.message for e in rep.errors), rep.summary()


def test_case_label_no_string():
    src = r'''
        var x: string = "a";
        switch (x) {
          case 123: { }   // etiqueta no-string
          default: { }
        }
    '''
    rep, _ = _analyze(src)
    assert any(e.code == E_OP_TYPES and "Etiqueta de case debe ser 'string'" in e.message for e in rep.errors), rep.summary()


def test_case_literal_duplicado():
    src = r'''
        var x: string = "a";
        switch (x) {
          case "a": { var y: integer = 1; }
          case "a": { var z: integer = 2; }  // duplicado
        }
    '''
    rep, _ = _analyze(src)
    assert any(e.code == E_DUPLICATE_ID and "Etiqueta de case duplicada" in e.message for e in rep.errors), rep.summary()
