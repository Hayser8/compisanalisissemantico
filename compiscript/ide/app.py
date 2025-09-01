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

        # Toolbar
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)
        actOpenFolder = QAction("Open Folder", self)
        actNew = QAction("New", self)
        actSave = QAction("Save", self)
        actSaveAs = QAction("Save As", self)
        actRun = QAction("▶ Run", self)
        actTheme = QAction("🌓 Theme", self)
        for a in (actOpenFolder, actNew, actSave, actSaveAs, actRun, actTheme):
            tb.addAction(a)
        actOpenFolder.triggered.connect(self.on_open_folder)
        actNew.triggered.connect(self.on_new_file)
        actSave.triggered.connect(self.on_save)
        actSaveAs.triggered.connect(self.on_save_as)
        actRun.triggered.connect(self.on_run)
        actTheme.triggered.connect(self.on_toggle_theme)

        # Layout: tree | editors | outline
        splitter = QSplitter(self)
        self.setCentralWidget(splitter)

        self.fsModel = QFileSystemModel(self)
        self.fsModel.setNameFilters(["*.cps", "*"])
        self.fsModel.setNameFilterDisables(False)

        self.tree = QTreeView(self)
        self.tree.setModel(self.fsModel)
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self.on_tree_double)
        splitter.addWidget(self.tree)

        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.on_close_tab)
        splitter.addWidget(self.tabs)

        self.outline = QTreeWidget(self)
        self.outline.setHeaderLabels(["Outline"])
        self.outline.itemActivated.connect(self.on_outline_jump)
        splitter.addWidget(self.outline)
        splitter.setSizes([250, 700, 250])

        # Bottom dock: Problems / Output / Report / Tree
        self.problems = QTreeWidget(self)
        self.problems.setHeaderLabels(["Code", "Line", "Col", "Message"])
        self.problems.itemActivated.connect(self.on_problem_jump)

        self.output = QPlainTextEdit(self)
        self.output.setReadOnly(True)

        self.pretty = QPlainTextEdit(self)   # reporte legible
        self.pretty.setReadOnly(True)

        # --- NUEVA pestaña: Tree (Imagen del AST) ---
        self.astLabel = QLabel("AST image will appear here")
        self.astLabel.setAlignment(Qt.AlignCenter)
        self.astScroll = QScrollArea(self)
        self.astScroll.setWidgetResizable(True)
        self.astScroll.setWidget(self.astLabel)

        bottom = QTabWidget(self)
        bottom.addTab(self.problems, "Problems")
        bottom.addTab(self.output, "Output")
        bottom.addTab(self.pretty, "Report")
        bottom.addTab(self.astScroll, "Tree")

        from PySide6.QtWidgets import QDockWidget
        dock = QDockWidget("Problems / Output / Report / Tree", self)
        dock.setWidget(bottom)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)

        # Runner (para análisis)
        self.runner = CliRunner(self)
        self.runner.output.connect(self.append_output)
        self.runner.finished.connect(self.on_run_finished)

        # Theme + initial workspace
        apply_theme(QApplication.instance(), self.theme)
        if self.program_dir and os.path.isdir(self.program_dir):
            self._set_root(self.program_dir)

        self.status = QStatusBar(self)
        self.setStatusBar(self.status)

        # Logs iniciales
        defs = find_defaults()
        self.append_output(f"[IDE] defaults: cli={defs.get('cli_path')}\n")
        self.append_output(f"[IDE] defaults: program_dir={defs.get('program_dir')}\n")
        self.append_output(f"[IDE] defaults: python={defs.get('python_path')}\n")

        # QProcess para AST (cadena: ast_dump -> dot)
        self._proc_ast_dump: QProcess | None = None
        self._proc_dot: QProcess | None = None
        self._last_dot: str = ""

    # ---- File ops ----
    def _current_editor(self) -> CodeEditor | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def _current_path(self) -> str | None:
        ed = self._current_editor()
        return getattr(ed, "file_path", None) if ed else None

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

    # ---- Run ----
    def on_run(self):
        try:
            ed = self._current_editor()
            path = self._current_path()
            if not ed or not path:
                self.append_output("[IDE] No active editor or file path is empty\n")
                QMessageBox.warning(self, "Run", "Open and save a .cps file first.")
                return
            # Save & clear
            self.on_save()
            self.output.clear()
            self.problems.clear()
            self.outline.clear()
            self.pretty.clear()
            self.astLabel.setText("Generating AST…")

            abs_path = os.path.abspath(path)
            self.append_output("[IDE] Run clicked\n")
            self.append_output(f"[IDE] Running on {abs_path}\n")
            self.runner.run_file(abs_path)

            # En paralelo (o después) generamos el AST visual
            self.generate_ast_image(abs_path)
        except Exception as e:
            self.append_output(f"[IDE] on_run exception: {e!r}\n")

    def append_output(self, text: str):
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(text)
        self.output.moveCursor(QTextCursor.End)

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

        self.status.showMessage("Run finished", 3000)

    # ---- Reporte bonito ----
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

    # ---- AST visual (DOT -> PNG) ----
    def generate_ast_image(self, cps_path: str):
        """Lanza dos procesos: (1) python -m src.tools.ast_dump <file.cps>  (2) dot -Tpng"""
        # Limpia procesos previos
        if self._proc_ast_dump:
            self._proc_ast_dump.kill()
        if self._proc_dot:
            self._proc_dot.kill()
        self._last_dot = ""

        py = self.defaults.get("python_path")
        workdir = self.program_dir or os.path.dirname(cps_path)

        # 1) Obtener DOT
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
            on_ast_ready()  # drenar
            dot_txt = (self._last_dot or "").strip()
            if not dot_txt or "digraph" not in dot_txt:
                self.astLabel.setText("No se pudo generar DOT del AST.\n¿Está correcto el archivo?\n\nSalida:\n" + (self._last_dot or "(vacía)"))
                return
            # 2) Render con Graphviz (dot -Tpng)
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
        self._proc_dot.setProgram("dot")           # requiere Graphviz instalado
        self._proc_dot.setArguments(["-Tpng"])
        self._proc_dot.setProcessChannelMode(QProcess.MergedChannels)

        png_chunks: list[bytes] = []

        def on_dot_out():
            data = bytes(self._proc_dot.readAllStandardOutput())
            if data:
                png_chunks.append(data)
            err = bytes(self._proc_dot.readAllStandardError())
            if err:
                # también agregamos a output IDE
                self.append_output(err.decode("utf-8", errors="replace"))

        def on_dot_finished(_code, _status):
            on_dot_out()
            if not png_chunks:
                # Fallback: mostrar DOT como texto y sugerir instalar Graphviz
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

        # Enviar DOT por stdin
        self._proc_dot.start()
        if not self._proc_dot.waitForStarted(5000):
            self.astLabel.setText("No se pudo iniciar 'dot'. ¿Está Graphviz instalado?")
            return
        self._proc_dot.write(dot_text.encode("utf-8"))
        self._proc_dot.closeWriteChannel()

    # ---- Outline ----
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

    # ---- Theme ----
    def on_toggle_theme(self):
        self.theme = "light" if (self.theme or "dark") == "dark" else "dark"
        apply_theme(QApplication.instance(), self.theme)
