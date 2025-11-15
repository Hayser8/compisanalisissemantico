from __future__ import annotations
import os, subprocess, tempfile, shutil, textwrap
from typing import Tuple, Optional

def _write_tmp(text: str, suffix: str = ".asm") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="mips_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def _mars_jar() -> Optional[str]:
    jar = os.environ.get("MARS_JAR")
    if jar and os.path.exists(jar):
        return jar
    return None

def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

def have_mars() -> bool:
    return _mars_jar() is not None

def have_spim() -> bool:
    return _which("spim") is not None or _which("qtspim") is not None

def have_any_sim() -> bool:
    return have_mars() or have_spim()

def run_asm(asm_text: str, stdin: str = "") -> Tuple[int, str, str]:
    """
    Ejecuta ASM en MARS (si hay JAR en $MARS_JAR) o en SPIM (si está instalado).
    Retorna (returncode, stdout, stderr).
    """
    if have_mars():
        return _run_mars(asm_text, stdin)
    if have_spim():
        return _run_spim(asm_text, stdin)
    raise RuntimeError("No MIPS simulator found. Set MARS_JAR or install spim.")

def _run_mars(asm_text: str, stdin: str) -> Tuple[int, str, str]:
    asm_path = _write_tmp(asm_text, ".asm")
    jar = _mars_jar()
    # Flags típicas de MARS CLI: nc = no GUI, no delayed branching warnings en GUI.
    # Si tu jar requiere otros flags, ajusta aquí.
    cmd = ["java", "-jar", jar, "nc", asm_path]
    proc = subprocess.run(cmd, input=stdin.encode("utf-8"),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8", "ignore"), proc.stderr.decode("utf-8", "ignore")

def _run_spim(asm_text: str, stdin: str) -> Tuple[int, str, str]:
    asm_path = _write_tmp(asm_text, ".asm")
    spim = _which("spim") or _which("qtspim")
    # spim imprime un banner; lo dejamos tal cual (los tests pueden normalizar).
    cmd = [spim, "-file", asm_path]
    proc = subprocess.run(cmd, input=stdin.encode("utf-8"),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8", "ignore"), proc.stderr.decode("utf-8", "ignore")
