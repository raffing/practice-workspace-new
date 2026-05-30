import re
from typing import Dict
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from .theme import Theme

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, theme: Dict = None):
        super().__init__(parent)
        self.theme = theme or Theme.get_theme()
        self._rules = self._create_rules()
    
    def _create_rules(self):
        rules = []
        t = self.theme
        
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setFontPointSize(14)
        fmt.setForeground(QColor(t['success']))
        rules.append((re.compile(r'^# .+$'), fmt))
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(t['text_disabled']))
        fmt.setFontStrikeOut(True)
        rules.append((re.compile(r'^\s*-\s+\[x\].+$'), fmt))
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(t['tree_task']))
        fmt.setFontWeight(QFont.Bold)
        rules.append((re.compile(r'^\s*-\s+(?!\[x\]).+$'), fmt))
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(t['warning']))
        rules.append((re.compile(r'#\w+'), fmt))
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(t['purple']))
        rules.append((re.compile(r'@[A-Za-zÀ-ÿ]+'), fmt))
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(t['info']))
        fmt.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        rules.append((re.compile(r"""@['"][^'"]+\.\w+['"]"""), fmt))
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(t['info']))
        fmt.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        rules.append((re.compile(r'@\S+\.\w+'), fmt))
        
        return rules
    
    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)
    
    def update_theme(self, theme: Dict):
        self.theme = theme
        self._rules = self._create_rules()
        self.rehighlight()