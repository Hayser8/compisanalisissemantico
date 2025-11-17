# tests/test_emitter_regressions.py
import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # /program
CLI = [sys.executable, str(PROJECT_ROOT / "cli.py")]


def run_cli(args):
    """
    Ejecuta `cli.py` con los argumentos dados y regresa el objeto CompletedProcess.

    Por defecto usa como cwd la raíz del proyecto para que `samples/` se resuelva bien.
    """
    proc = subprocess.run(
        CLI + args,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc


def get_emitter_block(output: str, fn_name: str):
    """
    Extrae el bloque de logs del emitter para una función dada.

    Busca líneas desde:
        [EMITTER] fn=<fn_name> ...
    hasta antes del siguiente:
        [EMITTER] fn=...
    """
    lines = output.splitlines()
    start = None
    for i, line in enumerate(lines):
        if f"[EMITTER] fn={fn_name} " in line:
            start = i
            break

    assert start is not None, f"No se encontró bloque del emitter para {fn_name!r}"

    end = None
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("[EMITTER] fn="):
            end = j
            break

    if end is None:
        end = len(lines)

    return lines[start:end]


def parse_param_home_off(block):
    """
    A partir de un bloque del emitter, devuelve (param_home_off, need_param_homes).

    param_home_off: dict mapeando índice de parámetro -> offset en stack
    need_param_homes: int (o None si no se encuentra)
    """
    mapping = {}
    need = None

    for line in block:
        if "param_home_off=" in line:
            # Ejemplo: "[EMITTER]   param_home_off={0: -4, 1: -8}"
            m = re.search(r"param_home_off=({.*})", line)
            assert m, f"No se pudo parsear param_home_off en línea: {line}"
            mapping = ast.literal_eval(m.group(1))

        if "need_param_homes=" in line:
            m = re.search(r"need_param_homes=(\d+)", line)
            assert m, f"No se pudo parsear need_param_homes en línea: {line}"
            need = int(m.group(1))

    return mapping, need


def extract_function_prologue(stdout: str, label: str, context_lines: int = 5):
    """
    Devuelve unas cuantas líneas alrededor del label de una función MIPS.

    label: por ejemplo "Animal__speak" o "runAll".
    """
    lines = stdout.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == f"{label}:":
            # Tomamos unas cuantas líneas antes y después del label
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            return "\n".join(lines[start:end])

    raise AssertionError(f"No se encontró el label {label!r} en el ASM")


@pytest.mark.emitter
def test_runAll_calls_pokeArray_with_two_args():
    """
    runAll debe llamar a pokeArray con 2 argumentos (el arreglo de ints y el de floats).

    En el log del emitter debería aparecer algo como:
        [EMITTER]   call in runAll -> pokeArray (argc=2)

    Este test fallará si el compiler sigue emitiendo (argc=0).
    """
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    # ok_all_post debería compilar "bien" (aunque con bugs de runtime)
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")

    lines = [
        line
        for line in all_output.splitlines()
        if "call in runAll -> pokeArray" in line
    ]
    assert lines, "Se esperaba al menos una llamada de runAll a pokeArray en el emitter"

    assert any(
        "(argc=2)" in line for line in lines
    ), (
        "runAll debe pasar 2 argumentos a pokeArray (argc=2); "
        "el emitter sigue reportando otra aridad"
    )


@pytest.mark.emitter
def test_pokeArray_has_param_homes_for_two_parameters():
    """
    pokeArray usa dos parámetros en el cuerpo (dos arreglos), así que el planner
    debe asignarles slots en stack (param_home_off) y contar need_param_homes >= 2.
    """
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    block = get_emitter_block(all_output, "pokeArray")
    param_home_off, need = parse_param_home_off(block)

    # En la versión correcta, esperamos que existan al menos 2 parámetros homed.
    assert (
        need is not None and need >= 2
    ), f"pokeArray debería tener al menos 2 parámetros homed; need_param_homes={need}"
    assert len(param_home_off) >= 2, (
        "pokeArray usa dos parámetros en el cuerpo, pero param_home_off no tiene "
        "al menos 2 entradas"
    )


@pytest.mark.emitter
def test_Animal_speak_spills_this_to_stack():
    """
    Los métodos deben guardar 'this' (a0) en el frame de stack.

    En particular, Animal__speak debería tener en su prólogo un 'sw $a0, ...'
    antes de usar -4($fp) como puntero 'this' en el cuerpo.
    """
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")

    # 1) A nivel de emitter: debe existir al menos un parámetro homed (this)
    block = get_emitter_block(all_output, "Animal::speak")
    param_home_off, need = parse_param_home_off(block)

    assert (
        need is not None and need >= 1
    ), f"Animal::speak debería al menos homear 'this'; need_param_homes={need}"
    assert param_home_off, (
        "Animal::speak no tiene ningún parámetro homed en param_home_off; "
        "debería al menos existir una entrada para 'this'"
    )

    # 2) En el ASM: el prólogo de Animal__speak debe guardar $a0 en el frame
    prologue = extract_function_prologue(proc.stdout, "Animal__speak")
    assert "sw $a0" in prologue, (
        "El prólogo de Animal__speak debería guardar $a0 (this) en el stack "
        "antes de leer -4($fp) en el cuerpo"
    )


@pytest.mark.emitter
def test_Dog_constructor_homes_this_and_explicit_param():
    """
    El constructor de Dog debería tener slots separados para 'this' y para el
    parámetro explícito (si lo hay) en param_home_off.

    En ok_all_post, Dog::constructor escribe en -8($fp) y -4($fp), así que
    esperamos al menos 2 entradas en param_home_off (this + otro).
    """
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    block = get_emitter_block(all_output, "Dog::constructor")
    param_home_off, need = parse_param_home_off(block)

    # Debería haber al menos this + 1 parámetro explícito
    assert (
        need is not None and need >= 2
    ), f"Dog::constructor debería homear this + al menos 1 parámetro; need_param_homes={need}"
    assert len(param_home_off) >= 2, (
        "Dog::constructor parece usar dos valores en stack (this y otro), "
        "pero param_home_off no tiene al menos 2 entradas"
    )


@pytest.mark.emitter
def test_A_get_spills_this_and_uses_param_home():
    """
    A::get accede a campos a partir de 'this', así que:

    - Debe tener 'this' homed (param_home_off no vacío).
    - El ASM debe guardar $a0 en el frame antes de usar offsets sobre $fp.
    """
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    block = get_emitter_block(all_output, "A::get")
    param_home_off, need = parse_param_home_off(block)

    assert (
        need is not None and need >= 1
    ), f"A::get debería al menos homear 'this'; need_param_homes={need}"
    assert param_home_off, (
        "A::get no tiene ningún parámetro homed en param_home_off; "
        "debería al menos existir 'this'"
    )

    prologue = extract_function_prologue(proc.stdout, "A__get")
    assert "sw $a0" in prologue, (
        "El prólogo de A__get debería guardar $a0 (this) en el stack "
        "para luego usarlo al acceder a 0($t0) y 4($t0)"
    )
