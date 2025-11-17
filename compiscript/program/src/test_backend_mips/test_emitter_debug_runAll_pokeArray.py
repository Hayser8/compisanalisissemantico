# tests/test_emitter_debug_runAll_pokeArray.py
from pathlib import Path
import sys
import subprocess

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI = [sys.executable, str(PROJECT_ROOT / "cli.py")]


def run_cli(args):
    return subprocess.run(
        CLI + args,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def get_emitter_block(output: str, fn_name: str):
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


@pytest.mark.emitter
def test_runAll_emitter_block_y_llamadas():
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")

    # 1) Ver el bloque de runAll
    block = get_emitter_block(all_output, "runAll")
    print("==== BLOQUE EMITTER runAll ====")
    for line in block:
        print(line)
    print("================================")

    # 2) Buscar cualquier log de llamada desde runAll
    call_lines = [l for l in all_output.splitlines() if "call in runAll" in l]
    print("==== LÍNEAS CALL EN runAll ====")
    for l in call_lines:
        print(l)
    print("================================")

    # Asegurarnos de que al menos hay una llamada desde runAll,
    # sin exigir todavía que sea pokeArray ni argc=2.
    assert call_lines, "runAll debería tener al menos una llamada registrada en el emitter"


import ast
import re

def parse_param_home_off_raw(block):
    """
    Igual que parse_param_home_off pero con prints de depuración.
    """
    mapping = {}
    need = None

    print("==== BLOQUE EMITTER pokeArray ====")
    for line in block:
        print(line)
    print("==================================")

    for line in block:
        if "param_home_off=" in line:
            m = re.search(r"param_home_off=({.*})", line)
            assert m, f"No se pudo parsear param_home_off en línea: {line}"
            txt = m.group(1)
            print(f"param_home_off crudo -> {txt!r}")
            mapping = ast.literal_eval(txt)

        if "need_param_homes=" in line:
            m = re.search(r"need_param_homes=(\d+)", line)
            assert m, f"No se pudo parsear need_param_homes en línea: {line}"
            need = int(m.group(1))
            print(f"need_param_homes -> {need}")

    return mapping, need


@pytest.mark.emitter
def test_pokeArray_debug_param_homes():
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    block = get_emitter_block(all_output, "pokeArray")

    param_home_off, need = parse_param_home_off_raw(block)

    # Por ahora solo pedimos que haya línea con need_param_homes
    assert need is not None, "No se pudo leer need_param_homes para pokeArray"
    # Y vemos qué valor real está reportando (con prints)
    print(f"DEBUG: pokeArray need_param_homes={need}, param_home_off={param_home_off}")


@pytest.mark.emitter
def test_IR_runAll_pokeArray_argc_viene_del_IR():
    """
    Este test verifica directamente la ARIDAD de las llamadas a pokeArray
    desde runAll, usando el debug del emitter:

        [EMITTER]   [CALL] in runAll -> pokeArray (argc=N)

    Si nunca vemos N == 2, el problema está en el IR (len(ins.args)),
    NO en el emitter.
    """
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")

    # Buscar todas las líneas de debug de llamadas a pokeArray desde runAll
    lines = [
        line
        for line in all_output.splitlines()
        if "[CALL] in runAll -> pokeArray" in line
    ]
    assert lines, (
        "No se encontró ningún debug '[CALL] in runAll -> pokeArray' en la salida. "
        "Eso indicaría que el IR ni siquiera está generando un Call a pokeArray "
        "desde runAll, o que cambió el formato del log."
    )

    # Extraer todos los argc que ve el emitter (que vienen de len(ins.args))
    argcs = []
    for line in lines:
        m = re.search(r"\(argc=(\d+)\)", line)
        assert m, f"No se pudo parsear 'argc' en la línea: {line!r}"
        argcs.append(int(m.group(1)))

    # Este assert es el "fuerte": si no hay ningún 2, el IR está mal
    if 2 not in argcs:
        pytest.fail(
            "IR de runAll está construyendo llamadas a pokeArray con argc="
            f"{argcs} (según len(ins.args) en el emitter), pero nunca con argc=2. "
            "Esto indica que el problema está en la construcción del IR/visitor "
            "para ok_all_post.cps (no se están pasando los dos arreglos como args), "
            "NO en el emitter."
        )
        
@pytest.mark.emitter
def test_IR_vs_FramePlan_pokeArray_identifica_quien_rompe():
    """
    Este test compara:
      - nparams que ve el IR para pokeArray (desde [PLAN-FIXUP])
      - need_param_homes que termina viendo el emitter para pokeArray

    Y falla con un mensaje que dice explícitamente si el problema está:
      - en el IR (fn.params de pokeArray no tiene 2 params), o
      - en el FramePlan/fixup (no está homeando 2 params aunque el IR sí tenga 2).
    """
    proc = run_cli(["samples/ok_all_post.cps", "--emit-mips"])
    assert proc.returncode == 0, proc.stderr

    all_output = (proc.stdout or "") + "\n" + (proc.stderr or "")

    # 1) Leer nparams desde la línea [PLAN-FIXUP] fn=pokeArray ...
    fixup_lines = [
        line
        for line in all_output.splitlines()
        if "[PLAN-FIXUP]" in line and "fn=pokeArray" in line
    ]
    assert fixup_lines, (
        "No se encontró ninguna línea '[PLAN-FIXUP] fn=pokeArray ...' en la salida. "
        "Verifica que el debug de _fixup_frame_plan_for_params siga activo."
    )

    # En teoría debería haber solo una, pero por si acaso tomamos la primera.
    line_fix = fixup_lines[0]
    m_nparams = re.search(r"nparams=(\d+)", line_fix)
    assert m_nparams, f"No se pudo parsear 'nparams' en: {line_fix!r}"
    nparams = int(m_nparams.group(1))

    # 2) Leer need_param_homes desde el bloque del emitter para pokeArray
    #    Usamos el mismo helper que tus otros tests si quieres, pero aquí
    #    lo hacemos directo con regex para que sea más claro.
    need_lines = [
        line
        for line in all_output.splitlines()
        if "[EMITTER]   need_param_homes=" in line and "fn=pokeArray" not in line
    ]
    # OJO: la línea de need_param_homes NO repite el nombre de función,
    # así que nos toca acotar mejor usando el bloque alrededor.
    # Para hacerlo robusto, filtramos por el bloque de fn=pokeArray:

    lines = all_output.splitlines()
    start = None
    for i, line in enumerate(lines):
        if "[EMITTER] fn=pokeArray " in line:
            start = i
            break

    assert start is not None, "No se encontró el bloque del emitter para pokeArray"

    end = None
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("[EMITTER] fn="):
            end = j
            break
    if end is None:
        end = len(lines)

    block = lines[start:end]

    need = None
    for line in block:
        if "need_param_homes=" in line:
            m_need = re.search(r"need_param_homes=(\d+)", line)
            assert m_need, f"No se pudo parsear need_param_homes en: {line!r}"
            need = int(m_need.group(1))
            break

    assert need is not None, (
        "No se encontró ninguna línea con 'need_param_homes=' en el bloque de pokeArray. "
        "Revisa que el emitter siga imprimiendo ese campo."
    )

    # 3) Diagnóstico fuerte: decidir QUIÉN está rompiendo
    if nparams < 2:
        pytest.fail(
            "IR de pokeArray solo tiene nparams="
            f"{nparams} en fn.params (según [PLAN-FIXUP]). "
            "Eso significa que el problema está en la construcción del IR/visitor "
            "para pokeArray (no está viendo los dos parámetros del cuerpo), "
            "NO en el FramePlan ni en el emitter."
        )

    # Si llegamos aquí, el IR sí ve >=2 parámetros.
    if need < 2:
        pytest.fail(
            "El IR de pokeArray reporta nparams="
            f"{nparams} (>= 2), pero el emitter ve need_param_homes={need}. "
            "Esto indica que el FramePlan/fixup NO está reservando homes para "
            "los dos parámetros, así que el bug está en la lógica del planner/"
            "_fixup_frame_plan_for_params, no en el IR."
        )