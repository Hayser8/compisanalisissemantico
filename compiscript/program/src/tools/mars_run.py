# program/src/tools/mars_run.py
from __future__ import annotations
import os
import sys
import subprocess
import tempfile
import glob

# --- Asegurar import "from src...." como en los tests ---
HERE = os.path.dirname(__file__)                 # .../program/src/tools
PROGRAM_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # .../program
if PROGRAM_ROOT not in sys.path:
    sys.path.insert(0, PROGRAM_ROOT)

# (Opcional) Si tienes un emitter propio, lo usamos; si no, generamos ASM mínimo.
try:
    from src.backend.mips.emitter import emit_program_stub  # type: ignore
    HAVE_EMITTER = True
except Exception:
    HAVE_EMITTER = False

from src.ir.model import Program, Function, BasicBlock, Label, LabelInstr, Return

def tiny_prog() -> Program:
    fn = Function(name="main", params=[])
    bb = fn.new_block(Label("L0"))
    bb.add(LabelInstr(Label("L0")))
    bb.add(Return(None))
    return Program(functions=[fn])

def default_stub() -> str:
    # ASM mínimo que arranca y sale (syscall 10)
    return (
        ".text\n"
        ".globl main\n"
        "main:\n"
        "  # demo: no hace nada, solo sale\n"
        "  li $v0, 10\n"
        "  syscall\n"
    )

def find_mars_jar() -> str | None:
    # 1) Variable de entorno
    env = os.environ.get("MARS_JAR")
    if env and os.path.exists(env):
        return env

    # 2) Candidatos comunes en la carpeta tools
    candidates = [
        os.path.join(HERE, "MARS.jar"),
        os.path.join(HERE, "Mars.jar"),
        os.path.join(HERE, "Mars4_5.jar"),
    ]
    # 3) Cualquier Mars*.jar
    candidates.extend(sorted(glob.glob(os.path.join(HERE, "Mars*.jar"))))

    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def main():
    prog = tiny_prog()
    asm_text = emit_program_stub(prog) if HAVE_EMITTER else default_stub()

    with tempfile.NamedTemporaryFile(suffix=".asm", delete=False, mode="w") as f:
        f.write(asm_text)
        asm_path = f.name
    print(f"[info] ASM generado en: {asm_path}")

    mars_jar = find_mars_jar()
    if not mars_jar:
        print("[warn] No se encontró ningún Mars*.jar en program/src/tools ni en $MARS_JAR")
        print("       Abre el .asm anterior en MARS manualmente (File > Open).")
        return

    print(f"[info] Usando MARS: {mars_jar}")
    try:
        subprocess.run(["java", "-jar", mars_jar, asm_path], check=False)
    except FileNotFoundError:
        print("[error] Java no encontrado. Asegúrate de tener `java` en el PATH.")
        print("        Alternativa: abre el .asm manualmente en MARS.")

if __name__ == "__main__":
    main()
