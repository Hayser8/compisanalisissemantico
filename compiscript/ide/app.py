from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QTextCursor 
from PySide6.QtWidgets import (QMainWindow, QFileDialog, QTabWidget, QTreeView, QToolBar, QMessageBox, QTreeWidget, QTreeWidgetItem, QStatusBar, QSplitter, QPlainTextEdit, QFileSystemModel, QApplication)
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
        tb = QToolBar("Main"); tb.setMovable(False); self.addToolBar(tb)
        actOpenFolder = QAction("Open Folder", self)
        actNew = QAction("New", self)
        actSave = QAction("Save", self)
        actSaveAs = QAction("Save As", self)
        actRun = QAction("▶ Run", self)
        actTheme = QAction("🌓 Theme", self)
        for a in (actOpenFolder, actNew, actSave, actSaveAs, actRun, actTheme): tb.addAction(a)
        actOpenFolder.triggered.connect(self.on_open_folder)
        actNew.triggered.connect(self.on_new_file)
        actSave.triggered.connect(self.on_save)
        actSaveAs.triggered.connect(self.on_save_as)
        actRun.triggered.connect(self.on_run)
        actTheme.triggered.connect(self.on_toggle_theme)

        # Layout: tree | editors | outline
        splitter = QSplitter(self); self.setCentralWidget(splitter)
        self.fsModel = QFileSystemModel(self); self.fsModel.setNameFilters(["*.cps","*"]); self.fsModel.setNameFilterDisables(False)
        self.tree = QTreeView(self); self.tree.setModel(self.fsModel); self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self.on_tree_double)
        splitter.addWidget(self.tree)
        self.tabs = QTabWidget(self); splitter.addWidget(self.tabs)
        self.outline = QTreeWidget(self); self.outline.setHeaderLabels(["Outline"]); self.outline.itemActivated.connect(self.on_outline_jump)
        splitter.addWidget(self.outline); splitter.setSizes([250, 700, 250])

        # Bottom dock: Problems / Output
        self.problems = QTreeWidget(self); self.problems.setHeaderLabels(["Code","Line","Col","Message"]); self.problems.itemActivated.connect(self.on_problem_jump)
        self.output = QPlainTextEdit(self); self.output.setReadOnly(True)
        bottom = QTabWidget(self); bottom.addTab(self.problems, "Problems"); bottom.addTab(self.output, "Output")
        from PySide6.QtWidgets import QDockWidget
        dock = QDockWidget("Problems / Output", self); dock.setWidget(bottom); self.addDockWidget(Qt.BottomDockWidgetArea, dock)

        # Runner
        self.runner = CliRunner(self)
        self.runner.output.connect(self.append_output)
        self.runner.finished.connect(self.on_run_finished)

        # Theme + initial workspace
        apply_theme(QApplication.instance(), self.theme)
        if self.program_dir and os.path.isdir(self.program_dir):
            self._set_root(self.program_dir)

        self.status = QStatusBar(self); self.setStatusBar(self.status)

    # ---- File ops ----
    def _current_editor(self) -> CodeEditor | None:
        w = self.tabs.currentWidget(); return w if isinstance(w, CodeEditor) else None

    def _current_path(self) -> str | None:
        ed = self._current_editor(); return getattr(ed, "file_path", None) if ed else None

    def on_open_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Open Folder", self.program_dir or os.getcwd())
        if d:
            self._set_root(d)
            self.program_dir = d

    def _set_root(self, folder: str):
        idx = self.fsModel.setRootPath(folder); self.tree.setRootIndex(idx)

    def on_tree_double(self, index):
        path = self.fsModel.filePath(index)
        if os.path.isdir(path): return
        self.open_file(path)

    def open_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f: text = f.read()
        ed = CodeEditor(self); ed.file_path = path; CompiscriptHighlighter(ed.document()); ed.setPlainText(text)
        self.tabs.addTab(ed, os.path.basename(path)); self.tabs.setCurrentWidget(ed)
        self.status.showMessage(f"Opened {path}", 3000)

    def on_new_file(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New File", "Name (e.g. main.cps)")
        if ok and name:
            base = self.program_dir or os.getcwd(); full = os.path.join(base, name)
            with open(full, "w", encoding="utf-8") as f: f.write("// new file")
            self._set_root(base); self.open_file(full)

    def on_save(self):
        ed = self._current_editor();
        if not ed: return
        path = getattr(ed, "file_path", None)
        if not path: return self.on_save_as()
        with open(path, "w", encoding="utf-8") as f: f.write(ed.toPlainText())
        self.status.showMessage(f"Saved {path}", 2000)

    def on_save_as(self):
        ed = self._current_editor();
        if not ed: return
        path, _ = QFileDialog.getSaveFileName(self, "Save As", self.program_dir or os.getcwd(), "CPS (*.cps);;All (*.*)")
        if path:
            ed.file_path = path; self.on_save(); i = self.tabs.currentIndex(); self.tabs.setTabText(i, os.path.basename(path))

    # ---- Run ----
    def on_run(self):
        path = self._current_path(); ed = self._current_editor()
        if not path or not ed:
            QMessageBox.warning(self, "Run", "Open and save a .cps file first."); return
        self.on_save(); self.output.clear(); self.problems.clear(); self.outline.clear()
        self.append_output(f"[IDE] Running on {path}\n")


    def append_output(self, text: str):
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(text)
        self.output.moveCursor(QTextCursor.End)

    def on_run_finished(self, data: dict):
        errs = data.get("errors", []) if isinstance(data, dict) else []
        for e in errs:
            code = str(e.get("code","")); line = str(e.get("line","")); col = str(e.get("column","")); msg = e.get("message","")
            self.problems.addTopLevelItem(QTreeWidgetItem([code, line, col, msg]))
        syms = data.get("symbols", {}) if isinstance(data, dict) else {}
        self.populate_outline(syms); self.status.showMessage("Run finished", 3000)

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
        if not (name and ed): return
        text = ed.toPlainText(); idx = text.find(name)
        if idx >= 0:
            cur = ed.textCursor(); cur.setPosition(idx); ed.setTextCursor(cur); ed.setFocus()

    def on_problem_jump(self, item: QTreeWidgetItem, _col: int):
        ed = self._current_editor();
        if not ed: return
        try:
            line = int(item.text(1)) - 1; col = max(0, int(item.text(2)) - 1)
        except Exception: return
        doc = ed.document(); blk = doc.findBlockByLineNumber(line); pos = blk.position() + col
        cur = ed.textCursor(); cur.setPosition(pos); ed.setTextCursor(cur); ed.setFocus()

    # ---- Theme ----
    def on_toggle_theme(self):
        self.theme = "light" if (self.theme or "dark") == "dark" else "dark"
        apply_theme(QApplication.instance(), self.theme)
