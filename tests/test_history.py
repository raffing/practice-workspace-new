"""Test per la cronologia delle modifiche."""
import tempfile
from pathlib import Path

from app.history import DocumentHistory


def test_add_entry():
    with tempfile.TemporaryDirectory() as tmp:
        history = DocumentHistory(Path(tmp))
        history.add_entry("prima riga\n", "prima riga\nseconda riga\n")
        entries = history.get_entries()
        assert len(entries) == 1
        assert "+seconda riga" in entries[0]["diff"]


def test_multiple_entries():
    with tempfile.TemporaryDirectory() as tmp:
        history = DocumentHistory(Path(tmp))
        history.add_entry("a\n", "a\nb\n")
        history.add_entry("a\nb\n", "a\nb\nc\n")
        entries = history.get_entries()
        assert len(entries) == 2


def test_max_entries():
    with tempfile.TemporaryDirectory() as tmp:
        history = DocumentHistory(Path(tmp))
        for _ in range(60):
            history.add_entry("old", "new")
        entries = history.get_entries(limit=100)
        assert len(entries) == 50
