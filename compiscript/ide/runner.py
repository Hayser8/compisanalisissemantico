from __future__ import annotations
from PySide6.QtCore import QObject, Signal, QProcess
import json, os, sys, shutil
from typing import Optional, Dict

# ---- Zero-config path discovery ----
def _candidates_for_cli(base_dir: str) -> list[str]:
    here = os.path.abspath(base_dir)
    repo = os.path.abspath(os.path.join(here, os.pardir))  
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

    # base: usa el Python actual
    python_path = sys.executable or 'python3'

    # preferir venv local del compilador: program/.venv
    if program_dir:
        if os.name == 'nt':
            pvenv = os.path.join(program_dir, '.venv', 'Scripts', 'python.exe')
        else:
            pvenv = os.path.join(program_dir, '.venv', 'bin', 'python')
        if os.path.isfile(pvenv):
            python_path = pvenv

    return {'python_path': python_path, 'cli_path': cli_path, 'program_dir': program_dir}

def _docker_available() -> bool:
    return shutil.which('docker') is not None

class CliRunner(QObject):
    output = Signal(str)     
    finished = Signal(dict)  

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proc: Optional[QProcess] = None
        self.defaults = find_defaults()
        self._buf: str = ''
        self._mode: str = 'python'  
        self._file_path: str = ''

    def run_file(self, file_path: str) -> None:
        # reset
        if self.proc:
            try: self.proc.kill()
            except Exception: pass
            self.proc = None

        self._buf = ''
        self._mode = 'python'
        self._file_path = os.path.abspath(file_path)

        if not (self.defaults.get('cli_path') and os.path.isfile(self.defaults['cli_path'])):
            if _docker_available():
                self._mode = 'docker'
                self._run_docker(self._file_path)
                return
            self.output.emit('[IDE] No se encontró cli.py y Docker no está disponible.\n')
            self.finished.emit({'ok': False, 'errors': [{'message': 'cli.py no encontrado'}]})
            return

        self._run_python(self._file_path)

    def _wire_process(self):
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.started.connect(lambda: self.output.emit(f'[IDE] {self._mode} process started\n'))
        self.proc.errorOccurred.connect(lambda e: self.output.emit(f'[IDE] {self._mode} process error: {e}\n'))
        self.proc.readyReadStandardOutput.connect(self._on_ready)
        self.proc.readyReadStandardError.connect(self._on_ready)
        self.proc.finished.connect(self._on_finished)

    def _run_python(self, file_path: str):
        cli = self.defaults['cli_path']
        py = self.defaults.get('python_path', sys.executable or 'python3')
        workdir = os.path.dirname(cli)

        self.output.emit(
            f'[IDE] exec(py): "{py}" "{cli}" --json --symbols "{file_path}"\n'
            f'[IDE] cwd: {workdir}\n'
        )

        self.proc = QProcess(self)
        self.proc.setWorkingDirectory(workdir)
        self.proc.setProgram(py)
        self.proc.setArguments([cli, '--json', '--symbols', file_path])
        self._wire_process()
        self.proc.start()

    def _run_docker(self, file_path: str):
        prog_dir = self.defaults.get('program_dir') or os.path.dirname(self.defaults.get('cli_path', ''))
        host_dir = os.path.abspath(prog_dir)
        if not os.path.isdir(host_dir):
            self.output.emit(f'[IDE] Docker fallback: program_dir no existe: {host_dir}\n')
            self.finished.emit({'ok': False, 'errors': [{'message': 'program_dir inválido'}]})
            return

        try:
            rel = os.path.relpath(file_path, host_dir)
        except Exception:
            rel = os.path.basename(file_path)
        rel = rel.replace('\\', '/')
        container_file = f'/program/{rel}'

        image = 'csp-image'
        args = [
            'docker', 'run', '--rm', '-i',
            '-v', f'{host_dir}:/program',
            '-w', '/program',
            image, 'python3', '/program/cli.py', '--json', '--symbols', container_file
        ]

        self.output.emit('[IDE] Fallback a Docker\n')
        self.output.emit(f"[IDE] exec(docker): {' '.join(args)}\n")

        self.proc = QProcess(self)
        self.proc.setProgram(args[0])
        self.proc.setArguments(args[1:])
        self._wire_process()
        self.proc.start()

    def _on_ready(self):
        if not self.proc: return
        out = bytes(self.proc.readAllStandardOutput()).decode('utf-8', errors='replace')
        err = bytes(self.proc.readAllStandardError()).decode('utf-8', errors='replace')
        if out:
            self._buf += out
            self.output.emit(out)
        if err:
            self._buf += err
            self.output.emit(err)

    def _on_finished(self, code: int, _status):
        raw = self._buf
        if raw and not raw.endswith('\n'):
            self.output.emit('\n')

        parsed = None
        try:
            start = raw.find('{')
            if start >= 0:
                parsed = json.loads(raw[start:])
        except Exception:
            parsed = None


        if parsed is not None:
            self.finished.emit(parsed)
            self.proc = None
            self._buf = ''
            self._mode = 'python'
            self._file_path = ''
            return


        looks_bad = (code != 0) or ('Traceback' in raw) or ('No module named antlr4' in raw)
        if self._mode == 'python' and looks_bad and _docker_available():
            self.output.emit(f'[IDE] python falló (exit={code}); intentando Docker…\n')
            self._mode = 'docker'
            self._buf = ''
            self._run_docker(self._file_path)
            return


        data = {'ok': False, 'errors': [{'message': f'No JSON en salida (exit={code})'}], 'raw': raw}
        self.finished.emit(data)
        self.proc = None
        self._buf = ''
        self._mode = 'python'
        self._file_path = ''