"""Test per la presenza nel workspace."""
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from app.presence import WorkspacePresence


def test_touch_active_creates_session():
    with tempfile.TemporaryDirectory() as tmp:
        presence = WorkspacePresence(Path(tmp), session_id="me")
        presence.touch_active()

        data = yaml.safe_load((Path(tmp) / "Agenda.md.sessions.yaml").read_text(encoding="utf-8"))
        assert data["me"]["status"] == "active"


def test_active_peers_excludes_current_session():
    with tempfile.TemporaryDirectory() as tmp:
        sessions_file = Path(tmp) / "Agenda.md.sessions.yaml"
        sessions_file.write_text(
            yaml.dump(
                {
                    "me": {"username": "me", "status": "active"},
                    "other": {"username": "Raffaele", "status": "active"},
                    "away": {"username": "Away", "status": "away"},
                }
            ),
            encoding="utf-8",
        )

        presence = WorkspacePresence(Path(tmp), session_id="me")
        assert presence.active_peers() == ["Raffaele (other)"]


def test_touch_active_marks_stale_peer_away():
    with tempfile.TemporaryDirectory() as tmp:
        sessions_file = Path(tmp) / "Agenda.md.sessions.yaml"
        stale = (datetime.now() - timedelta(minutes=10)).isoformat()
        sessions_file.write_text(
            yaml.dump({"old": {"username": "old", "status": "active", "last_seen": stale}}),
            encoding="utf-8",
        )

        presence = WorkspacePresence(Path(tmp), session_id="me")
        presence.touch_active()

        data = yaml.safe_load(sessions_file.read_text(encoding="utf-8"))
        assert data["old"]["status"] == "away"


def test_mark_closed():
    with tempfile.TemporaryDirectory() as tmp:
        presence = WorkspacePresence(Path(tmp), session_id="me")
        presence.touch_active()
        presence.mark_closed()

        data = yaml.safe_load((Path(tmp) / "Agenda.md.sessions.yaml").read_text(encoding="utf-8"))
        assert data["me"]["status"] == "closed"
