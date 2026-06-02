"""Apertura portabile di file e cartelle."""
from pathlib import Path
import os
import subprocess
import sys


def open_path(path: Path) -> bool:
    path_str = str(path)
    try:
        if sys.platform == "win32":
            os.startfile(path_str)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path_str])
        else:
            subprocess.Popen(["xdg-open", path_str])
        return True
    except (OSError, AttributeError):
        if sys.platform != "win32":
            return False

    try:
        if path.is_dir():
            subprocess.Popen(["explorer.exe", path_str])
        else:
            subprocess.Popen(["notepad.exe", path_str])
        return True
    except OSError:
        return False


def find_named_path(folder: Path, name: str) -> Path | None:
    direct = folder / name
    if direct.exists():
        return direct

    for candidate in folder.rglob(name):
        if candidate.is_file() or candidate.is_dir():
            return candidate
    return None
