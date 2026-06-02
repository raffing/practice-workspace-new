"""Conversioni pure tra Agenda.md salvata ed editor.

Il file su disco conserva path deterministici; l'editor mostra testo leggibile.
Tenere queste regole qui evita regex diverse sparse nella UI.
"""
from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional, Tuple


_SIMPLE_MENTION_PATTERN = re.compile(r"""@(?:'([^']+)'|"(.+)"|([^\s#@]+))""")


def parse_practice_heading(line: str) -> Optional[Tuple[str, Optional[str]]]:
    """Ritorna nome e path da una riga pratica, anche se il path contiene parentesi."""
    if line.startswith("# [") and line.endswith(")"):
        close_label = line.find("](")
        if close_label > 3:
            name = line[3:close_label]
            path = line[close_label + 2:-1]
            return name.strip(), path.strip()
    if line.startswith("# "):
        return line[2:].strip(), None
    return None


def parse_practice_paths(text: str) -> Dict[str, str]:
    paths: Dict[str, str] = {}
    for line in text.splitlines():
        parsed = parse_practice_heading(line)
        if parsed and parsed[1]:
            paths[parsed[0]] = parsed[1]
    return paths


def editor_file_token(label: str) -> str:
    label = label.strip()
    if (label.startswith("'") and label.endswith("'")) or (
        label.startswith('"') and label.endswith('"')
    ):
        return f"@{label}"
    if any(ch.isspace() for ch in label) or "(" in label or ")" in label:
        return f"@'{label}'"
    return f"@{label}"


def _find_markdown_file_link_end(line: str, start: int) -> int:
    """Trova la parentesi finale di @[label](path) tollerando parentesi nel path."""
    for index in range(start, len(line)):
        if line[index] == ")" and (index + 1 == len(line) or line[index + 1].isspace()):
            return index
    return -1


def strip_file_links_for_editor(line: str) -> str:
    """Converte @[file](path) e @['file complesso'](path) in token editabili."""
    result: List[str] = []
    pos = 0
    while True:
        start = line.find("@[", pos)
        if start == -1:
            result.append(line[pos:])
            break
        close_label = line.find("](", start + 2)
        if close_label == -1:
            result.append(line[pos:])
            break
        close_link = _find_markdown_file_link_end(line, close_label + 2)
        if close_link == -1:
            result.append(line[pos:])
            break
        result.append(line[pos:start])
        result.append(editor_file_token(line[start + 2:close_label]))
        pos = close_link + 1
    return "".join(result)


def raw_to_editor_text(raw_content: str) -> str:
    lines: List[str] = []
    for line in raw_content.split("\n"):
        parsed = parse_practice_heading(line)
        if parsed:
            lines.append(f"# {parsed[0]}")
        else:
            lines.append(strip_file_links_for_editor(line))
    return "\n".join(lines)


def extract_file_mentions(text: str) -> List[str]:
    """Estrae solo riferimenti file/cartelle, non persone come @Marco."""
    files: List[str] = []
    for match in _SIMPLE_MENTION_PATTERN.finditer(strip_file_links_for_editor(text)):
        filename = match.group(1) or match.group(2) or match.group(3)
        if not filename:
            continue
        if match.group(3) and not _looks_like_file_reference(filename):
            continue
        files.append(filename)
    return files


def remove_file_mentions(text: str) -> str:
    def replace(match: re.Match) -> str:
        filename = match.group(1) or match.group(2) or match.group(3)
        if match.group(3) and not _looks_like_file_reference(filename):
            return match.group(0)
        return ""

    return _SIMPLE_MENTION_PATTERN.sub(replace, strip_file_links_for_editor(text))


def _looks_like_file_reference(value: str) -> bool:
    return "." in value or "/" in value or "\\" in value


def _quote_link_label(filename: str) -> str:
    if any(ch.isspace() for ch in filename) or "(" in filename or ")" in filename:
        return f"'{filename}'"
    return filename


def resolve_file_links(line: str, workspace_path: Path, practice_dir: Path) -> str:
    """Sostituisce token @file con link deterministici relativi al workspace."""
    clean_line = strip_file_links_for_editor(line)

    def replace(match: re.Match) -> str:
        filename = match.group(1) or match.group(2) or match.group(3)
        if not filename:
            return match.group(0)
        if match.group(3) and not _looks_like_file_reference(filename):
            return match.group(0)

        target = practice_dir / filename
        try:
            rel = target.relative_to(workspace_path)
        except ValueError:
            return editor_file_token(filename)

        rel_str = str(rel).replace("\\", "/")
        return f"@[{_quote_link_label(filename)}]({rel_str})"

    return _SIMPLE_MENTION_PATTERN.sub(replace, clean_line)


def editor_to_raw_text(
    editor_text: str,
    workspace_path: Path,
    practice_paths: Dict[str, str],
    resolve_links: bool = True,
) -> str:
    lines: List[str] = []
    current_practice_path = "."
    for line in editor_text.split("\n"):
        parsed = parse_practice_heading(line)
        if parsed:
            name = parsed[0]
            current_practice_path = practice_paths.get(name, ".")
            if name in practice_paths:
                lines.append(f"# [{name}]({current_practice_path})")
            else:
                lines.append(f"# {name}")
            continue

        if resolve_links and current_practice_path:
            line = resolve_file_links(line, workspace_path, workspace_path / current_practice_path)
        lines.append(line)
    return "\n".join(lines)
