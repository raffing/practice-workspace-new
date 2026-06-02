"""Test per il parser del documento."""
from app.parser import DocumentParser


parser = DocumentParser()


def test_parse_simple_practice():
    text = "# Test Pratica\n- Task 1\n  - Subtask"
    nodes = parser.parse_document(text)
    assert len(nodes) == 1
    assert nodes[0].text == "Test Pratica"
    assert nodes[0].is_task is False
    assert len(nodes[0].children) == 1
    assert nodes[0].children[0].text == "Task 1"
    assert nodes[0].children[0].is_task is True


def test_parse_raw_practice_with_path_and_parentheses():
    text = "# [Anna Ventrella (Colucci)](ABC/Anna Ventrella (Colucci))\n- Task"
    nodes = parser.parse_document(text)
    assert nodes[0].text == "Anna Ventrella (Colucci)"


def test_parse_completed_task():
    text = "# Test\n- [x] Task completata"
    nodes = parser.parse_document(text)
    task = nodes[0].children[0]
    assert task.task_data["status"] == "done"


def test_parse_tags():
    text = "# Test\n- Task #urgente #casa"
    nodes = parser.parse_document(text)
    task = nodes[0].children[0]
    assert "urgente" in task.task_data["tags"]
    assert "casa" in task.task_data["tags"]


def test_parse_people_are_not_files():
    text = "# Test\n- Task @Marco @Anna"
    nodes = parser.parse_document(text)
    task = nodes[0].children[0]
    assert "Marco" in task.task_data["people"]
    assert "Anna" in task.task_data["people"]
    assert task.task_data["files"] == []


def test_parse_file_references():
    text = "# Test\n- Task @'file name.pdf' @doc.docx"
    nodes = parser.parse_document(text)
    task = nodes[0].children[0]
    files = task.task_data["files"]
    assert "file name.pdf" in files
    assert "doc.docx" in files


def test_parse_file_with_spaces_and_parentheses():
    text = "# Test\n- Task @'materiale per Raffaele (Russo)'"
    nodes = parser.parse_document(text)
    task = nodes[0].children[0]
    files = task.task_data["files"]
    assert "materiale per Raffaele (Russo)" in files


def test_parse_raw_file_link_with_parentheses():
    text = "# Test\n- Task @['materiale (Russo)'](pratica/materiale (Russo))"
    nodes = parser.parse_document(text)
    task = nodes[0].children[0]
    assert "materiale (Russo)" in task.task_data["files"]


def test_clean_task_text():
    text = "Verificare computo @computo.xlsx e @'altro file.pdf' con @Marco"
    cleaned = DocumentParser.clean_task_text(text)
    assert "@computo" not in cleaned
    assert "altro file.pdf" not in cleaned
    assert "@Marco" in cleaned
    assert "Verificare computo" in cleaned


def test_toggle_task_status():
    assert DocumentParser.toggle_task_status("- Task") == "- [x] Task"
    assert DocumentParser.toggle_task_status("- [x] Task") == "- Task"
    assert DocumentParser.toggle_task_status("  - Task") == "  - [x] Task"
    assert DocumentParser.toggle_task_status("# Not a task") == "# Not a task"


def test_parse_empty_document():
    nodes = parser.parse_document("")
    assert len(nodes) == 0


def test_parse_multiple_practices():
    text = "# Pratica 1\n- Task A\n\n# Pratica 2\n- Task B"
    nodes = parser.parse_document(text)
    assert len(nodes) == 2
    assert nodes[0].text == "Pratica 1"
    assert nodes[1].text == "Pratica 2"
