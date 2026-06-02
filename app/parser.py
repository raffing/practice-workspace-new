import re
from datetime import datetime, timedelta
from typing import List, Dict
from .agenda_markup import extract_file_mentions, parse_practice_heading, remove_file_mentions
from .models import DocumentNode, TaskStatus
from .constants import WEEKDAYS, MONTHS

class DocumentParser:
    _task_pattern = re.compile(r'^(\s*)-\s+(?:\[([ x])\]\s+)?(.+)$')
    _tag_pattern = re.compile(r'#([\wÀ-ÿ-]+)')
    _person_pattern = re.compile(r'@([A-Za-zÀ-ÿ]+(?:\s[A-Za-zÀ-ÿ]+)*)')
    _today_pattern = re.compile(r'\boggi\b', re.IGNORECASE)
    _tomorrow_pattern = re.compile(r'\bdomani\b', re.IGNORECASE)
    _date_pattern = re.compile(
        r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)',
        re.IGNORECASE
    )
    _multi_space_pattern = re.compile(r'\s+')
    
    def parse_document(self, text: str) -> List[DocumentNode]:
        nodes = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            practice = parse_practice_heading(line)
            if practice:
                nodes.append(DocumentNode(
                    text=practice[0],
                    level=0, line_number=i, is_task=False
                ))
                continue
            
            task_match = self._task_pattern.match(line)
            if task_match:
                indent = len(task_match.group(1))
                level = (indent // 2) + 1
                task_text = task_match.group(3).strip()
                task_data = self._parse_task_metadata(task_text)
                
                if task_match.group(2) == 'x':
                    task_data['status'] = TaskStatus.DONE.value
                
                nodes.append(DocumentNode(
                    text=task_text, level=level, line_number=i,
                    is_task=True, task_data=task_data
                ))
        
        return self._build_tree(nodes)
    
    def _build_tree(self, flat_nodes: List[DocumentNode]) -> List[DocumentNode]:
        if not flat_nodes:
            return []
        
        root = DocumentNode(text="Root", level=-1, line_number=-1)
        stack = [root]
        
        for node in flat_nodes:
            while stack[-1].level >= node.level:
                stack.pop()
            node.parent = stack[-1]
            stack[-1].children.append(node)
            stack.append(node)
        
        return root.children
    
    def _parse_task_metadata(self, text: str) -> Dict:
        metadata = {
            'tags': self._tag_pattern.findall(text),
            'people': self._person_pattern.findall(text),
            'dates': [], 'files': [],
            'status': TaskStatus.OPEN.value
        }
        metadata['files'] = extract_file_mentions(text)
        
        today = datetime.now()
        if self._today_pattern.search(text):
            metadata['dates'].append(today.strftime("%Y-%m-%d"))
        if self._tomorrow_pattern.search(text):
            metadata['dates'].append((today + timedelta(days=1)).strftime("%Y-%m-%d"))
        
        text_lower = text.lower()
        for day, day_num in WEEKDAYS.items():
            if day in text_lower:
                days_ahead = (day_num - today.weekday()) % 7 or 7
                target_date = today + timedelta(days=days_ahead)
                metadata['dates'].append(target_date.strftime("%Y-%m-%d"))
        
        date_match = self._date_pattern.search(text)
        if date_match:
            day = int(date_match.group(1))
            month = MONTHS[date_match.group(2).lower()]
            try:
                date_obj = datetime(today.year, month, day)
                metadata['dates'].append(date_obj.strftime("%Y-%m-%d"))
            except ValueError:
                pass
        
        return metadata
    
    @classmethod
    def clean_task_text(cls, text: str) -> str:
        cleaned = remove_file_mentions(text)
        return cls._multi_space_pattern.sub(' ', cleaned).strip()
    
    @classmethod
    def toggle_task_status(cls, line: str) -> str:
        match = re.match(r'^(\s*-\s+)(?:\[x\]\s+)?(.+)$', line)
        if not match:
            return line
        
        indent = match.group(1)
        text = match.group(2)
        
        if line.startswith(f"{indent}[x] "):
            return f"{indent}{text}"
        else:
            return f"{indent}[x] {text}"
