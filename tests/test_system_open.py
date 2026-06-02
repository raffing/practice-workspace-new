"""Test per utility filesystem usate dall'apertura file."""
import tempfile
from pathlib import Path

from app.system_open import find_named_path


def test_find_named_path_direct_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "file.pdf"
        target.touch()
        assert find_named_path(root, "file.pdf") == target


def test_find_named_path_nested_folder():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "sub" / "materiale (Russo)"
        target.mkdir(parents=True)
        assert find_named_path(root, "materiale (Russo)") == target


def test_find_named_path_missing():
    with tempfile.TemporaryDirectory() as tmp:
        assert find_named_path(Path(tmp), "missing.pdf") is None
