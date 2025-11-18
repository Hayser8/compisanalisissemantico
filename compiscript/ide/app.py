# compiscript/ide/app.py
from __future__ import annotations
from PySide6.QtCore import Qt, QIODevice, QByteArray
from PySide6.QtGui import QAction, QTextCursor, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QTabWidget, QTreeView,
    QToolBar, QMessageBox, QTreeWidget, QTreeWidgetItem, QStatusBar,
    QSplitter, QPlainTextEdit, QFileSystemModel, QApplication,
    QLabel, QScrollArea
)
from PySide6.QtCore import QProcess
import os
import sys  # <-- para fallback de python si hace falta

from editor import CodeEditor, CompiscriptHighlighter
from runner import CliRunner, find_defaults
from theming import apply_theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compiscript IDE")
        self.resize(1200, 800)
        self.theme = "dark"
        self.defaults = find_defaults()
        self.program_dir = self.defaults.get("program_dir", os.getcwd())
        self.last_run_path: str | None = None      # último archivo ejecutado
        self._mips_proc: QProcess | None = None    # proceso para --emit-mips
        self._mars_proc: QProcess | None = None    # proceso para --run-mars (MIPS op)

        # ------------------------------------------------------------------ #
        # Toolbar
        # ------------------------------------------------------------------ #
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)
        actOpenFolder = QAction("Open Folder", self)
        actNew = QAction("New", self)
        actSave = QAction("Save", self)
        actSaveAs = QAction("Save As", self)
        actRun = QAction("▶ Run", self)
        actTheme = QAction("Theme", self)
        for a in (actOpenFolder, actNew, actSave, actSaveAs, actRun, actTheme):
            tb.addAction(a)

        actOpenFolder.triggered.connect(self.on_open_folder)
        actNew.triggered.connect(self.on_new_file)
        actSave.triggered.connect(self.on_save)
        actSaveAs.triggered.connect(self.on_save_as)
        actRun.triggered.connect(self.on_run)
        actTheme.triggered.connect(self.on_toggle_theme)

        # ------------------------------------------------------------------ #
        # Layout central: árbol de archivos + editor + outline
        # ------------------------------------------------------------------ #
        splitter = QSplitter(self)
        self.setCentralWidget(splitter)

        # Árbol de archivos con filtro *.cps
        self.fsModel = QFileSystemModel(self)
        self.fsModel.setNameFilters(["*.cps", "*"])
        self.fsModel.setNameFilterDisables(False)

        self.tree = QTreeView(self)
        self.tree.setModel(self.fsModel)
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self.on_tree_double)
        splitter.addWidget(self.tree)

        # Pestañas de editores
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.on_close_tab)
        splitter.addWidget(self.tabs)

        # Outline
        self.outline = QTreeWidget(self)
        self.outline.setHeaderLabels(["Outline"])
        self.outline.itemActivated.connect(self.on_outline_jump)
        splitter.addWidget(self.outline)
        splitter.setSizes([250, 700, 250])

        # ------------------------------------------------------------------ #
        # Panel inferior: Problems / Output / Report / TAC / ASM / Tree / MIPS op
        # ------------------------------------------------------------------ #
        self.problems = QTreeWidget(self)
        self.problems.setHeaderLabels(["Code", "Line", "Col", "Message"])
        self.problems.itemActivated.connect(self.on_problem_jump)

        self.output = QPlainTextEdit(self)
        self.output.setReadOnly(True)

        self.pretty = QPlainTextEdit(self)
        self.pretty.setReadOnly(True)

        # TAC / IR
        self.tac = QPlainTextEdit(self)
        self.tac.setReadOnly(True)

        # ASM (MIPS generado por --emit-mips)
        self.asmView = QPlainTextEdit(self)
        self.asmView.setReadOnly(True)

        # MIPS op (salida del programa corriendo en MARS con --run-mars)
        self.mipsOp = QPlainTextEdit(self)
        self.mipsOp.setReadOnly(True)

        # Visor de imagen para el AST (Graphviz)
        self.astLabel = QLabel("AST image will appear here")
        self.astLabel.setAlignment(Qt.AlignCenter)
        self.astScroll = QScrollArea(self)
        self.astScroll.setWidgetResizable(True)
        self.astScroll.setWidget(self.astLabel)

        bottom = QTabWidget(self)
        bottom.addTab(self.problems, "Problems")
        bottom.addTab(self.output, "Output")
        bottom.addTab(self.pretty, "Report")
        bottom.addTab(self.tac, "TAC")
        bottom.addTab(self.asmView, "ASM")
        bottom.addTab(self.astScroll, "Tree")
        bottom.addTab(self.mipsOp, "MIPS op")

        from PySide6.QtWidgets import QDockWidget
        dock = QDockWidget("Problems / Output / Report / TAC / ASM / Tree / MIPS op", self)
        dock.setWidget(bottom)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)

        # ------------------------------------------------------------------ #
        # Runner CLI + tema + estado
        # ------------------------------------------------------------------ #
        self.runner = CliRunner(self)
        self.runner.output.connect(self.append_output)
        self.runner.finished.connect(self.on_run_finished)

        apply_theme(QApplication.instance(), self.theme)
        if self.program_dir and os.path.isdir(self.program_dir):
            self._set_root(self.program_dir)

        self.status = QStatusBar(self)
        self.setStatusBar(self.status)

        defs = find_defaults()
        self.append_output(f"[IDE] defaults: cli={defs.get('cli_path')}\n")
        self.append_output(f"[IDE] defaults: program_dir={defs.get('program_dir')}\n")
        self.append_output(f"[IDE] defaults: python={defs.get('python_path')}\n")

        # Procesos para la generación del AST (DOT -> PNG)
        self._proc_ast_dump: QProcess | None = None
        self._proc_dot: QProcess | None = None
        self._last_dot: str = ""

    # ====================================================================== #
    # Helpers
    # ====================================================================== #
    def _current_editor(self) -> CodeEditor | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def _current_path(self) -> str | None:
        ed = self._current_editor()
        return getattr(ed, "file_path", None) if ed else None

    # ====================================================================== #
    # Abrir carpeta / archivos
    # ====================================================================== #
    def on_open_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Open Folder", self.program_dir or os.getcwd())
        if d:
            self._set_root(d)
            self.program_dir = d

    def _set_root(self, folder: str):
        idx = self.fsModel.setRootPath(folder)
        self.tree.setRootIndex(idx)

    def on_tree_double(self, index):
        path = self.fsModel.filePath(index)
        if os.path.isdir(path):
            return
        self.open_file(path)

    def open_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        ed = CodeEditor(self)
        ed.file_path = path
        CompiscriptHighlighter(ed.document())
        ed.setPlainText(text)
        self.tabs.addTab(ed, os.path.basename(path))
        self.tabs.setCurrentWidget(ed)
        self.status.showMessage(f"Opened {path}", 3000)

    # ====================================================================== #
    # Nuevo / Guardar
    # ====================================================================== #
    def on_new_file(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New File", "Name (e.g. main.cps)")
        if ok and name:
            base = self.program_dir or os.getcwd()
            full = os.path.join(base, name)
            with open(full, "w", encoding="utf-8") as f:
                f.write("// new file\n")
            self._set_root(base)
            self.open_file(full)

    def on_save(self):
        ed = self._current_editor()
        if not ed:
            return
        path = getattr(ed, "file_path", None)
        if not path:
            return self.on_save_as()
        with open(path, "w", encoding="utf-8") as f:
            f.write(ed.toPlainText())
        self.status.showMessage(f"Saved {path}", 2000)

    def on_save_as(self):
        ed = self._current_editor()
        if not ed:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", self.program_dir or os.getcwd(), "CPS (*.cps);;All (*.*)"
        )
        if path:
            ed.file_path = path
            self.on_save()
            i = self.tabs.currentIndex()
            self.tabs.setTabText(i, os.path.basename(path))

    # ====================================================================== #
    # Run: CLI (JSON) + AST + MIPS (emit-mips y run-mars)
    # ====================================================================== #
    def on_run(self):
        try:
            ed = self._current_editor()
            path = self._current_path()
            if not ed or not path:
                self.append_output("[IDE] No active editor or file path is empty\n")
                QMessageBox.warning(self, "Run", "Open and save a .cps file first.")
                return

            # Guardar y limpiar paneles
            self.on_save()
            self.output.clear()
            self.problems.clear()
            self.outline.clear()
            self.pretty.clear()
            self.tac.clear()
            self.asmView.clear()
            self.mipsOp.clear()
            self.astLabel.setText("Generating AST…")

            # Cancelar procesos previos de MIPS / MARS si seguían vivos
            if self._mips_proc:
                try:
                    self._mips_proc.kill()
                except Exception:
                    pass
                self._mips_proc = None

            if self._mars_proc:
                try:
                    self._mars_proc.kill()
                except Exception:
                    pass
                self._mars_proc = None

            abs_path = os.path.abspath(path)
            self.last_run_path = abs_path
            self.append_output("[IDE] Run clicked\n")
            self.append_output(f"[IDE] Running on {abs_path}\n")

            # 1) Corre el checker CLI (modo JSON)
            self.runner.run_file(abs_path)
            # 2) Genera AST (DOT -> PNG)
            self.generate_ast_image(abs_path)
        except Exception as e:
            self.append_output(f"[IDE] on_run exception: {e!r}\n")

    # ====================================================================== #
    # Output helpers
    # ====================================================================== #
    def append_output(self, text: str):
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(text)
        self.output.moveCursor(QTextCursor.End)

    # ====================================================================== #
    # CLI terminado (JSON)
    # ====================================================================== #
    def on_run_finished(self, data: dict):
        self.append_output(f"[IDE] finished; ok={data.get('ok', False)}\n")

        errs = data.get("errors", []) if isinstance(data, dict) else []
        for e in errs:
            code = str(e.get("code", ""))
            line = str(e.get("line", ""))
            cval = e.get("col") if e.get("col") is not None else e.get("column", "")
            msg = e.get("message", "")
            self.problems.addTopLevelItem(QTreeWidgetItem([code, line, str(cval), msg]))

        syms = data.get("symbols", {}) if isinstance(data, dict) else {}
        self.populate_outline(syms)
        self.update_pretty_report(data)

        # TAC / IR (si lo manda el CLI)
        ir_txt = data.get("ir") if isinstance(data, dict) else None
        if isinstance(ir_txt, str) and ir_txt.strip():
            self.tac.setPlainText(ir_txt)
        elif data.get("ok") is False:
            self.tac.setPlainText("(Sin IR: hay errores en el código)")

        # Si todo está OK, lanzamos:
        #   - generación de ASM (--emit-mips) → pestaña ASM
        #   - ejecución en MARS (--run-mars)  → pestaña MIPS op
        if data.get("ok"):
            try:
                self.run_emit_mips()
            except Exception as e:
                self.append_output(f"[IDE] run_emit_mips exception: {e!r}\n")
            try:
                self.run_mips_op()
            except Exception as e:
                self.append_output(f"[IDE] run_mips_op exception: {e!r}\n")

        self.status.showMessage("Run finished", 3000)

    # ====================================================================== #
    # MIPS: --emit-mips (ASM tab)
    # ====================================================================== #
    def run_emit_mips(self) -> None:
        """
        Ejecuta:
            python cli.py --emit-mips <file.cps>
        usando QProcess y vuelca la salida textual en la pestaña ASM.
        """
        path = self.last_run_path or self._current_path()
        if not path:
            return

        cli = self.defaults.get("cli_path")
        if not cli or not os.path.isfile(cli):
            self.append_output("[IDE] cli_path no encontrado; no se puede generar MIPS.\n")
            return

        py = self.defaults.get("python_path") or (sys.executable or "python3")
        workdir = os.path.dirname(cli) or os.getcwd()

        # Si ya había un proceso MIPS corriendo, lo matamos
        if self._mips_proc:
            try:
                self._mips_proc.kill()
            except Exception:
                pass
            self._mips_proc = None

        self.asmView.clear()
        self.append_output(
            f'[IDE] exec(py emit-mips): "{py}" "{cli}" --emit-mips "{path}"\n'
            f"[IDE] cwd(mips): {workdir}\n"
        )

        proc = QProcess(self)
        self._mips_proc = proc
        proc.setWorkingDirectory(workdir)
        proc.setProgram(py)
        proc.setArguments([cli, "--emit-mips", path])
        proc.setProcessChannelMode(QProcess.MergedChannels)

        def on_ready():
            if not self._mips_proc:
                return
            out = bytes(self._mips_proc.readAllStandardOutput()).decode("utf-8", errors="replace")
            err = bytes(self._mips_proc.readAllStandardError()).decode("utf-8", errors="replace")
            text = (out or "") + (err or "")
            if text:
                self.asmView.moveCursor(QTextCursor.End)
                self.asmView.insertPlainText(text)
                self.asmView.moveCursor(QTextCursor.End)

        def on_finished(code, _status):
            on_ready()  # leer lo último que quede
            self.append_output(f"[IDE] emit-mips finished (exit={code})\n")
            self._mips_proc = None

        proc.readyReadStandardOutput.connect(on_ready)
        proc.readyReadStandardError.connect(on_ready)
        proc.finished.connect(on_finished)
        proc.start()

    # ====================================================================== #
    # MIPS: --run-mars (MIPS op tab)
    # ====================================================================== #
    def run_mips_op(self) -> None:
        """
        Ejecuta:
            python cli.py --run-mars <file.cps>
        usando QProcess y vuelca la salida del programa (MARS) en la pestaña MIPS op.
        Se asume que cli.py internamente compila a MIPS y lanza MARS.
        """
        path = self.last_run_path or self._current_path()
        if not path:
            return

        cli = self.defaults.get("cli_path")
        if not cli or not os.path.isfile(cli):
            self.append_output("[IDE] cli_path no encontrado; no se puede ejecutar MARS.\n")
            return

        py = self.defaults.get("python_path") or (sys.executable or "python3")
        workdir = os.path.dirname(cli) or os.getcwd()

        # Si ya había un proceso MARS corriendo, lo matamos
        if self._mars_proc:
            try:
                self._mars_proc.kill()
            except Exception:
                pass
            self._mars_proc = None

        self.mipsOp.clear()
        self.append_output(
            f'[IDE] exec(py run-mars): "{py}" "{cli}" --run-mars "{path}"\n'
            f"[IDE] cwd(mars): {workdir}\n"
        )

        proc = QProcess(self)
        self._mars_proc = proc
        proc.setWorkingDirectory(workdir)
        proc.setProgram(py)
        proc.setArguments([cli, "--run-mars", path])
        proc.setProcessChannelMode(QProcess.MergedChannels)

        def on_ready_mars():
            if not self._mars_proc:
                return
            out = bytes(self._mars_proc.readAllStandardOutput()).decode("utf-8", errors="replace")
            err = bytes(self._mars_proc.readAllStandardError()).decode("utf-8", errors="replace")
            text = (out or "") + (err or "")
            if text:
                self.mipsOp.moveCursor(QTextCursor.End)
                self.mipsOp.insertPlainText(text)
                self.mipsOp.moveCursor(QTextCursor.End)

        def on_finished_mars(code, _status):
            on_ready_mars()  # leer lo último
            self.append_output(f"[IDE] run-mars finished (exit={code})\n")
            self._mars_proc = None

        proc.readyReadStandardOutput.connect(on_ready_mars)
        proc.readyReadStandardError.connect(on_ready_mars)
        proc.finished.connect(on_finished_mars)
        proc.start()

    # ====================================================================== #
    # Reporte bonito
    # ====================================================================== #
    def update_pretty_report(self, data: dict):
        lines = []
        if not isinstance(data, dict):
            self.pretty.setPlainText("— sin datos —")
            return

        ok = data.get("ok", False)
        errs = data.get("errors", []) or []
        syms = data.get("symbols", {}) or {}

        if ok:
            lines.append("OK ✅  (sin errores)\n")
        else:
            lines.append(f"Errores ({len(errs)}):")
            for e in errs:
                code = e.get("code", "?")
                line = e.get("line")
                cval = e.get("col") if e.get("col") is not None else e.get("column")
                pos = f"{line}:{cval}" if (line is not None) else "?"
                msg = e.get("message", "")
                lines.append(f"  {code} @ {pos} - {msg}")
            lines.append("")

        gl = syms.get("globals", [])
        classes = syms.get("classes", {})
        fns = syms.get("functions", {})

        lines.append("Resumen de símbolos:")
        lines.append(f"  globals: {len(gl)}   clases: {len(classes)}   funciones: {len(fns)}\n")

        if fns:
            lines.append("Funciones (hasta 20):")
            for name, f in list(fns.items())[:20]:
                params = ", ".join(f"{p.get('name')}:{p.get('type')}" for p in f.get("params", []))
                ret = f.get("return") or f.get("ret") or "void"
                lines.append(f"  {name}({params}) : {ret}")
            lines.append("")

        if classes:
            lines.append("Clases:")
            for cname, members in classes.items():
                lines.append(f"  {cname}  ({len(members)} miembros)")
            lines.append("")

        if gl:
            lines.append("Globals (hasta 20):")
            for g in gl[:20]:
                name = g.get("name", "?")
                kind = g.get("kind", "")
                ty = g.get("type") or g.get("ret") or ""
                suffix = f" : {ty}" if ty else ""
                lines.append(f"  {kind} {name}{suffix}")

        self.pretty.setPlainText("\n".join(lines))

    # ====================================================================== #
    # AST: DOT -> PNG
    # ====================================================================== #
    def generate_ast_image(self, cps_path: str):
        """Lanza dos procesos: (1) python -m src.tools.ast_dump <file.cps>  (2) dot -Tpng"""

        # Cancelar procesos previos
        if self._proc_ast_dump:
            self._proc_ast_dump.kill()
        if self._proc_dot:
            self._proc_dot.kill()
        self._last_dot = ""

        py = self.defaults.get("python_path")
        workdir = self.program_dir or os.path.dirname(cps_path)

        # Ejecuta el generador DOT del AST
        self._proc_ast_dump = QProcess(self)
        self._proc_ast_dump.setWorkingDirectory(workdir)
        self._proc_ast_dump.setProgram(py)
        self._proc_ast_dump.setArguments(["-m", "src.tools.ast_dump", cps_path])
        self._proc_ast_dump.setProcessChannelMode(QProcess.MergedChannels)

        def on_ast_ready():
            out = bytes(self._proc_ast_dump.readAllStandardOutput()).decode("utf-8", errors="replace")
            if out:
                self._last_dot += out

        def on_ast_finished(_code, _status):
            on_ast_ready()
            dot_txt = (self._last_dot or "").strip()
            if not dot_txt or "digraph" not in dot_txt:
                self.astLabel.setText(
                    "No se pudo generar DOT del AST.\n¿Está correcto el archivo?\n\nSalida:\n"
                    + (self._last_dot or "(vacía)")
                )
                return
            self.render_dot_to_png(dot_txt, workdir)

        self._proc_ast_dump.readyReadStandardOutput.connect(on_ast_ready)
        self._proc_ast_dump.readyReadStandardError.connect(on_ast_ready)
        self._proc_ast_dump.finished.connect(on_ast_finished)

        self.append_output(f"[IDE] exec(py ast_dump): \"{py}\" -m src.tools.ast_dump \"{cps_path}\"\n")
        self.append_output(f"[IDE] cwd(ast): {workdir}\n")
        self._proc_ast_dump.start()

    def render_dot_to_png(self, dot_text: str, workdir: str):
        self._proc_dot = QProcess(self)
        self._proc_dot.setWorkingDirectory(workdir)
        self._proc_dot.setProgram("dot")
        self._proc_dot.setArguments(["-Tpng"])
        self._proc_dot.setProcessChannelMode(QProcess.MergedChannels)

        png_chunks: list[bytes] = []

        def on_dot_out():
            data = bytes(self._proc_dot.readAllStandardOutput())
            if data:
                png_chunks.append(data)
            err = bytes(self._proc_dot.readAllStandardError())
            if err:
                self.append_output(err.decode("utf-8", errors="replace"))

        def on_dot_finished(_code, _status):
            on_dot_out()
            if not png_chunks:
                msg = (
                    "No se pudo renderizar con Graphviz (dot).\n"
                    "Instala Graphviz y asegúrate que 'dot' esté en PATH.\n\n"
                    "DOT generado:\n\n"
                )
                self.astLabel.setText(msg + dot_text)
                return
            png_data = b"".join(png_chunks)
            pix = QPixmap()
            ok = pix.loadFromData(png_data, "PNG")
            if not ok:
                self.astLabel.setText("No se pudo cargar PNG del AST.\n")
                return
            self.astLabel.setPixmap(pix)
            self.astLabel.adjustSize()

        self._proc_dot.readyReadStandardOutput.connect(on_dot_out)
        self._proc_dot.readyReadStandardError.connect(on_dot_out)
        self._proc_dot.finished.connect(on_dot_finished)

        self._proc_dot.start()
        if not self._proc_dot.waitForStarted(5000):
            self.astLabel.setText("No se pudo iniciar 'dot'. ¿Está Graphviz instalado?")
            return
        self._proc_dot.write(dot_text.encode("utf-8"))
        self._proc_dot.closeWriteChannel()

    # ====================================================================== #
    # Outline + navegación
    # ====================================================================== #
    def populate_outline(self, symbols: dict):
        self.outline.clear()
        root = self.outline.invisibleRootItem()

        def add(parent, label, name=None):
            it = QTreeWidgetItem([label])
            parent.addChild(it)
            it.setData(0, Qt.UserRole, name or label)
            return it

        # Globals
        gl = symbols.get("globals", [])
        if gl:
            gnode = add(root, "Globals")
            for g in gl:
                name = g.get("name", "?")
                kind = g.get("kind", "")
                ty = g.get("type") or g.get("ret") or ""
                suffix = f" : {ty}" if ty else ""
                add(gnode, f"{kind} {name}{suffix}", name)

        # Classes
        classes = symbols.get("classes", {})
        for cname, members in classes.items():
            c = add(root, f"class {cname}", cname)
            for m in members:
                mname = m.get("name", "?")
                mret = m.get("ret") or m.get("type") or ""
                mk = m.get("kind", "field")
                suffix = f" : {mret}" if mret else ""
                add(c, f"{mk} {mname}{suffix}", mname)

        # Functions
        fns = symbols.get("functions", {})
        if fns:
            fnode = add(root, "Functions")
            for fname, f in fns.items():
                params = ", ".join(f"{p.get('name')}:{p.get('type')}" for p in f.get("params", []))
                ret = f.get("return") or f.get("ret") or "void"
                add(fnode, f"{fname}({params}) : {ret}", fname.split("::")[-1])

        self.outline.expandAll()

    def on_outline_jump(self, item: QTreeWidgetItem, _col: int):
        name = item.data(0, Qt.UserRole)
        ed = self._current_editor()
        if not (name and ed):
            return
        text = ed.toPlainText()
        idx = text.find(name)
        if idx >= 0:
            cur = ed.textCursor()
            cur.setPosition(idx)
            ed.setTextCursor(cur)
            ed.setFocus()

    def on_problem_jump(self, item: QTreeWidgetItem, _col: int):
        ed = self._current_editor()
        if not ed:
            return
        try:
            line = int(item.text(1)) - 1
            col = max(0, int(item.text(2)) - 1)
        except Exception:
            return
        doc = ed.document()
        blk = doc.findBlockByLineNumber(line)
        pos = blk.position() + col
        cur = ed.textCursor()
        cur.setPosition(pos)
        ed.setTextCursor(cur)
        ed.setFocus()

    # ====================================================================== #
    # Tabs / Tema
    # ====================================================================== #
    def on_close_tab(self, index: int):
        w = self.tabs.widget(index)
        try:
            if hasattr(w, "document") and w.document().isModified():
                path = getattr(w, "file_path", None)
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(w.toPlainText())
        except Exception:
            pass
        self.tabs.removeTab(index)

    def on_toggle_theme(self):
        self.theme = "light" if (self.theme or "dark") == "dark" else "dark"
        apply_theme(QApplication.instance(), self.theme)
