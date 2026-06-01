"""Gestione cronologia modifiche con diff."""
import difflib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class DocumentHistory:
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.history_file = workspace_path / "Agenda.md.history.yaml"
        self._entries: List[Dict] = []
        self._load()

    def _load(self):
        if self.history_file.exists():
            self._entries = yaml.safe_load(self.history_file.read_text(encoding='utf-8')) or []

    def _save(self):
        self.history_file.write_text(
            yaml.dump(self._entries, allow_unicode=True),
            encoding='utf-8',
        )

    def add_entry(self, old_content: str, new_content: str, username: str = ""):
        """Aggiunge una voce alla cronologia con il diff."""
        diff = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile='prima',
            tofile='dopo',
        ))

        entry = {
            'timestamp': datetime.now().isoformat(),
            'user': username or os.environ.get('USERNAME', 'unknown'),
            'hostname': os.environ.get('COMPUTERNAME', 'unknown'),
            'diff': ''.join(diff),
            'summary': self._summarize(diff),
        }
        self._entries.append(entry)

        if len(self._entries) > 50:
            self._entries = self._entries[-50:]

        self._save()

    def _summarize(self, diff_lines: List[str]) -> str:
        """Crea un riepilogo leggibile delle modifiche."""
        added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        return f"+{added} -{removed}"

    def get_entries(self, limit: int = 20) -> List[Dict]:
        return self._entries[-limit:]

    def count(self) -> int:
        return len(self._entries)

    def get_entry(self, index: int) -> Optional[Dict]:
        if 0 <= index < len(self._entries):
            return self._entries[index]
        return None
