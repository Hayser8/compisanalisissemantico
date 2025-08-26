from __future__ import annotations
from PySide6.QtCore import QObject, Signal, QProcess
import json, os, sys
from typing import Optional, Dict

# ---- Zero-config path discovery ----

def _candidates_for_cli(base_dir: str) -> list[str]:
    here = os.path.abspath(base_dir)
    repo = os.path.abspath(os.path.join(here, os.pardir))  # repo root (.. from ide folder)
    cands = [
        os.path.join(repo, 'cli.py'),
        os.path.join(repo, 'program', 'cli.py'),
        os.path.join(repo, 'compiscript', 'program', 'cli.py'),
        os.path.join(here, 'cli.py'),
    ]
    return [os.path.abspath(p) for p in cands]

def _pick_program_dir(cli_path: str) -> str:
    if cli_path and os.path.isfile(cli_path):
        base = os.path.dirname(cli_path)
        if os.path.basename(base).lower() == 'program':
            return base
        sib = os.path.join(os.path.dirname(base), 'program')
        if os.path.isdir(sib):
            return sib
        return os.path.dirname(cli_path)
    # Fallback to repo/program if exists
    here = os.path.abspath(os.path.dirname(__file__))
    repo = os.path.abspath(os.path.join(here, os.pardir))
    rp = os.path.join(repo, 'program')
    return rp if os.path.isdir(rp) else repo

def find_defaults() -> Dict[str, str]:
    here = os.path.dirname(__file__)
    cli_path = ''
    for p in _candidates_for_cli(here):
        if os.path.isfile(p):
            cli_path = p
            break
    program_dir = _pick_program_dir(cli_path)
    python_path = sys.executable or 'python3'
    return {'python_path': python_path, 'cli_path': cli_path, 'program_dir': program_dir}


class CliRunner(QObject):
    output = Signal(str)
    finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proc: Optional[QProcess] = None
        self.defaults = find_defaults()
        self._buf: str = ''

    def run_file(self, file_path: str) -> None:
        # Kill previous run if any
        if self.proc:
            try:
                self.proc.kill()
            except Exception:
                pass
            self.proc = None

        cli = self.defaults.get('cli_path')
        py = self.defaults.get('python_path', sys.executable or 'python3')

        if not cli or not os.path.isfile(cli):
            self.output.emit('[IDE] No se encontró cli.py (buscado en root del repo y en compiscript/program).\n')
            self.finished.emit({'ok': False, 'errors': [{'message': 'cli.py no encontrado'}]})
            return

        workdir = os.path.dirname(cli)
        self._buf = ''
        # Log comando y cwd con saltos de línea
        self.output.emit(
            f'[IDE] exec: "{py}" "{cli}" --json --symbols "{file_path}"\n'
            f'[IDE] cwd: {workdir}\n'
        )

        # Configura proceso
        self.proc = QProcess(self)
        self.proc.setWorkingDirectory(workdir)
        self.proc.setProgram(py)
        self.proc.setArguments([cli, '--json', '--symbols', file_path])
        self.proc.setProcessChannelMode(QProcess.MergedChannels)

        # Señales
        self.proc.started.connect(lambda: self.output.emit('[IDE] process started\n'))
        self.proc.errorOccurred.connect(lambda e: self.output.emit(f'[IDE] process error: {e}\n'))
        self.proc.readyReadStandardOutput.connect(self._on_ready)
        self.proc.readyReadStandardError.connect(self._on_ready)
        self.proc.finished.connect(self._on_finished)

        # Start!
        self.proc.start()

    def _on_ready(self):
        if not self.proc:
            return
        out = bytes(self.proc.readAllStandardOutput()).decode('utf-8', errors='replace')
        if out:
            self._buf += out
            self.output.emit(out)
        err = bytes(self.proc.readAllStandardError()).decode('utf-8', errors='replace')
        if err:
            self._buf += err
            self.output.emit(err)

    def _on_finished(self, code: int, _status):
        # Asegura salto de línea final en el Output
        if self._buf and not self._buf.endswith('\n'):
            self.output.emit('\n')

        raw = self._buf
        data = {'ok': False, 'errors': [{'message': f'No JSON en salida (exit={code})'}], 'raw': raw}
        try:
            start = raw.find('{')
            if start >= 0:
                data = json.loads(raw[start:])
        except Exception as e:
            data = {'ok': False, 'errors': [{'message': f'Fallo al parsear JSON: {e} (exit={code})'}], 'raw': raw}

        self.finished.emit(data)
        self.proc = None
        self._buf = ''
