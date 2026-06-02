"""Test per path pratiche, link file e roundtrip raw/editor."""
import tempfile
from pathlib import Path

from app.agenda_markup import (
    editor_to_raw_text,
    parse_practice_paths,
    raw_to_editor_text,
    resolve_file_links,
)


def test_extract_practice_paths_with_parentheses():
    raw = "# [Anna (Colucci)](ABC/Anna (Colucci))\n# [Test](DEF/Test)\n# No Path"
    assert parse_practice_paths(raw) == {
        "Anna (Colucci)": "ABC/Anna (Colucci)",
        "Test": "DEF/Test",
    }


def test_clean_content_for_editor():
    raw = "# [Anna (Colucci)](ABC/Anna (Colucci))\n- Task @[file.pdf](ABC/file.pdf)"
    assert raw_to_editor_text(raw) == "# Anna (Colucci)\n- Task @file.pdf"


def test_roundtrip_file_with_spaces():
    raw = "- task @['materiale (Russo)'](pratica/materiale (Russo))"
    clean = raw_to_editor_text(raw)
    assert "@'materiale (Russo)'" in clean


def test_roundtrip_file_no_spaces():
    raw = "- task @[file.pdf](pratica/file.pdf)"
    clean = raw_to_editor_text(raw)
    assert clean == "- task @file.pdf"


def test_resolve_file_links():
    line = "- task @'file.pdf' @altro.docx"
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        practice_dir = workspace / "ABC/Test"
        practice_dir.mkdir(parents=True)
        (practice_dir / "file.pdf").touch()
        (practice_dir / "altro.docx").touch()

        result = resolve_file_links(line, workspace, practice_dir)
        assert "@[file.pdf](ABC/Test/file.pdf)" in result
        assert "@[altro.docx](ABC/Test/altro.docx)" in result


def test_file_not_found_still_gets_path():
    workspace = Path("/tmp/test_workspace")
    practice_dir = workspace / "ABC/Test"
    result = resolve_file_links("- task @'file_inesistente.pdf'", workspace, practice_dir)
    assert "@[file_inesistente.pdf](ABC/Test/file_inesistente.pdf)" in result


def test_file_with_spaces_and_parentheses():
    workspace = Path("/tmp/test_workspace")
    practice_dir = workspace / "Test"
    result = resolve_file_links(
        "- task @'materiale per Raffaele (Russo)'",
        workspace,
        practice_dir,
    )
    assert "@['materiale per Raffaele (Russo)'](Test/materiale per Raffaele (Russo))" in result


def test_editor_to_raw_text_roundtrip():
    raw = "# [Anna (Colucci)](ABC/Anna (Colucci))\n- Task @'file uno.pdf'"
    clean = raw_to_editor_text(raw)
    result = editor_to_raw_text(
        clean,
        Path("/tmp/ws"),
        {"Anna (Colucci)": "ABC/Anna (Colucci)"},
    )
    assert result == "# [Anna (Colucci)](ABC/Anna (Colucci))\n- Task @['file uno.pdf'](ABC/Anna (Colucci)/file uno.pdf)"
