"""Gestione sessioni/presenza per workspace condivisi."""
from datetime import datetime
from pathlib import Path
import os
from typing import Dict, List

import yaml


class WorkspacePresence:
    def __init__(self, workspace_path: Path, session_id: str | None = None):
        self.workspace_path = workspace_path
        self.session_id = session_id or os.environ.get("COMPUTERNAME", "unknown")
        self.sessions_file = workspace_path / "Agenda.md.sessions.yaml"

    def touch_active(self):
        sessions = self._read_sessions()
        sessions[self.session_id] = {
            "username": os.environ.get("USERNAME", "unknown"),
            "last_seen": datetime.now().isoformat(),
            "status": "active",
        }
        self._mark_stale_sessions_away(sessions)
        self._write_sessions(sessions)

    def active_peers(self) -> List[str]:
        sessions = self._read_sessions()
        return [
            f"{data.get('username', 'unknown')} ({session_id})"
            for session_id, data in sessions.items()
            if session_id != self.session_id and data.get("status") == "active"
        ]

    def mark_closed(self):
        sessions = self._read_sessions()
        if self.session_id in sessions:
            sessions[self.session_id]["status"] = "closed"
            sessions[self.session_id]["last_seen"] = datetime.now().isoformat()
            self._write_sessions(sessions)

    def _read_sessions(self) -> Dict:
        if self.sessions_file.exists():
            return yaml.safe_load(self.sessions_file.read_text(encoding="utf-8")) or {}
        return {}

    def _write_sessions(self, sessions: Dict):
        self.sessions_file.write_text(
            yaml.dump(sessions, allow_unicode=True),
            encoding="utf-8",
        )

    def _mark_stale_sessions_away(self, sessions: Dict):
        now = datetime.now()
        for session_id, data in list(sessions.items()):
            if session_id == self.session_id:
                continue
            last_seen = data.get("last_seen")
            if not last_seen:
                continue
            try:
                last = datetime.fromisoformat(last_seen)
            except ValueError:
                continue
            if (now - last).seconds > 300:
                data["status"] = "away"
