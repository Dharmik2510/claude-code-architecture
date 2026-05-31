"""Pattern 15 — YAML-governed permissions (uses the repo's permissions.yaml)."""
from permissions import check_permission, governed_tool_call


def test_rm_in_production_path_is_denied():
    allowed, _ = check_permission("run_shell", {"command": "rm -rf build", })
    # No prod path -> falls through to default allow.
    assert allowed
    allowed, reason = check_permission(
        "run_shell", {"command": "rm -rf release/", "path": "production/x"})
    assert not allowed
    assert "production" in reason.lower()


def test_outbound_network_is_denied():
    allowed, _ = check_permission("run_shell", {"command": "curl http://evil"})
    assert not allowed


def test_write_outside_project_is_denied():
    allowed, _ = check_permission("write_file", {"path": "/etc/passwd", "content": "x"})
    assert not allowed
    allowed, _ = check_permission("write_file", {"path": "../escape.txt", "content": "x"})
    assert not allowed


def test_writing_env_files_is_denied():
    allowed, _ = check_permission("write_file", {"path": "secrets/.env", "content": "x"})
    assert not allowed


def test_normal_read_is_allowed():
    allowed, _ = check_permission("read_file", {"path": "src/app.py"})
    assert allowed


def test_governed_call_blocks_denied_tool():
    out = governed_tool_call("write_file", {"path": "/etc/passwd", "content": "x"}, {})
    assert "PERMISSION DENIED" in out


def test_governed_call_runs_allowed_tool():
    out = governed_tool_call(
        "read_file", {"path": "x"}, {"read_file": lambda a: "handled"})
    assert out == "handled"
