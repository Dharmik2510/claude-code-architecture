"""Pattern 14 — reversible file writes via snapshots."""
import snapshots as s


def test_write_then_revert_restores_original(tmp_path, monkeypatch):
    monkeypatch.setattr(s, "SNAPSHOT_DIR", tmp_path / "snaps")
    s.SNAPSHOT_DIR.mkdir()

    target = tmp_path / "doc.txt"
    target.write_text("ORIGINAL")

    s.tool_safe_write({"path": str(target), "content": "MODIFIED"})
    assert target.read_text() == "MODIFIED"

    msg = s.revert_file(str(target))
    assert target.read_text() == "ORIGINAL"
    assert "Reverted" in msg


def test_revert_with_no_snapshot_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(s, "SNAPSHOT_DIR", tmp_path / "snaps")
    s.SNAPSHOT_DIR.mkdir()
    out = s.revert_file(str(tmp_path / "never.txt"))
    assert "No snapshots" in out


def test_first_write_to_new_file_has_no_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(s, "SNAPSHOT_DIR", tmp_path / "snaps")
    s.SNAPSHOT_DIR.mkdir()
    new = tmp_path / "fresh.txt"
    out = s.tool_safe_write({"path": str(new), "content": "hi"})
    assert new.read_text() == "hi"
    assert "Previous version" not in out  # nothing existed to snapshot
