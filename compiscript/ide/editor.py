# compiscript/ide/editor.py
from __future__ import annotations
from PySide6.QtCore import QRect, Qt, QSize
from PySide6.QtGui import QColor, QPainter, QTextFormat, QSyntaxHighlighter, QTextCharFormat, QFont
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
import re

class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
        self.setFont(QFont("Consolas", 11))

    def lineNumberAreaWidth(self):
        digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance('9') * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self._lineNumberArea.scroll(0, dy)
        else:
            self._lineNumberArea.update(0, rect.y(), self._lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self._lineNumberArea)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 20))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor("#888"))
                painter.drawText(0, top, self._lineNumberArea.width()-4, self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(255, 255, 0, 25))
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extraSelections.append(sel)
        self.setExtraSelections(extraSelections)

class CompiscriptHighlighter(QSyntaxHighlighter):
    KEYWORDS = (
        'let','var','const','function','class','if','else','while','do','for','foreach','try','catch','switch','case','default','break','continue','return','new','this','print','in'
    )
    TYPES = ('boolean','integer','float','string','void','true','false','null')

    def __init__(self, doc):
        super().__init__(doc)
        self.rules = []
        kwfmt = QTextCharFormat(); kwfmt.setForeground(QColor('#c678dd')); kwfmt.setFontWeight(QFont.Bold)
        tyfmt = QTextCharFormat(); tyfmt.setForeground(QColor('#56b6c2'))
        numfmt = QTextCharFormat(); numfmt.setForeground(QColor('#d19a66'))
        strfmt = QTextCharFormat(); strfmt.setForeground(QColor('#98c379'))
        comfmt = QTextCharFormat(); comfmt.setForeground(QColor('#6a737d'))

        for kw in self.KEYWORDS:
            self.rules.append((re.compile(rf"\\b{kw}\\b"), kwfmt))
        for ty in self.TYPES:
            self.rules.append((re.compile(rf"\\b{ty}\\b"), tyfmt))
        self.rules.append((re.compile(r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"), numfmt))
        self.rules.append((re.compile(r'"[^"\\\n]*(?:\\.[^"\\\n]*)*' + r'"'), strfmt))
        self.comment_re = re.compile(r"//.*")

    def highlightBlock(self, text: str):
        for regex, fmt in self.rules:
            for m in regex.finditer(text):
                self.setFormat(m.start(), m.end()-m.start(), fmt)
        m = self.comment_re.search(text)
        if m:
            comfmt = QTextCharFormat(); comfmt.setForeground(QColor('#6a737d'))
            self.setFormat(m.start(), len(text)-m.start(), comfmt)
