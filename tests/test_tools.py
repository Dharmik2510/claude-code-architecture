"""Pattern 2 — tool dispatch handlers."""
import tools as t


def test_write_then_read_roundtrip(tmp_path):
    f = tmp_path / "note.txt"
    msg = t.tool_write_file({"path": str(f), "content": "hello\nworld"})
    assert "Written" in msg

    out = t.tool_read_file({"path": str(f)})
    assert "1: hello" in out
    assert "2: world" in out


def test_read_missing_file_returns_error():
    out = t.tool_read_file({"path": "/no/such/file.xyz"})
    assert "does not exist" in out


def test_write_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b" / "c.txt"
    t.tool_write_file({"path": str(nested), "content": "x"})
    assert nested.exists()


def test_list_directory(tmp_path):
    (tmp_path / "f1.py").write_text("x")
    (tmp_path / "sub").mkdir()
    out = t.tool_list_directory({"path": str(tmp_path)})
    assert "f1.py" in out
    assert "sub" in out


def test_run_shell_captures_output():
    out = t.tool_run_shell({"command": "echo hello-from-shell"})
    assert "hello-from-shell" in out


def test_dispatch_map_wires_all_tools():
    assert set(t.TOOL_HANDLERS) == {
        "run_shell", "read_file", "write_file", "list_directory"}
    assert {s["name"] for s in t.TOOL_SCHEMAS} == set(t.TOOL_HANDLERS)
