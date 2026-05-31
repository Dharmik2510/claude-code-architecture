"""Pattern 9 — persistent JSONL agent mailboxes."""
import mailbox as mb


def test_send_and_read_marks_read(tmp_path, monkeypatch):
    monkeypatch.setattr(mb, "MAILBOX_DIR", tmp_path / "mb")
    mb.MAILBOX_DIR.mkdir()

    mid = mb.send_message("reviewer", "coord", {"type": "review", "file": "a.py"})
    assert mid

    unread = mb.read_unread_messages("reviewer")
    assert len(unread) == 1
    assert unread[0]["type"] == "review"

    # Second read returns nothing — messages were marked read.
    assert mb.read_unread_messages("reviewer") == []


def test_reply_preserves_thread(tmp_path, monkeypatch):
    monkeypatch.setattr(mb, "MAILBOX_DIR", tmp_path / "mb")
    mb.MAILBOX_DIR.mkdir()

    mb.send_message("reviewer", "coord", {"type": "review", "file": "a.py"})
    original = mb.read_unread_messages("reviewer")[0]

    mb.reply_to_message(original, "reviewer", {"type": "done", "findings": "ok"})
    reply = mb.read_unread_messages("coord")[0]
    assert reply["reply_to"] == original["id"]
    assert reply["thread_id"] == original["id"]


def test_read_empty_inbox_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(mb, "MAILBOX_DIR", tmp_path / "mb")
    mb.MAILBOX_DIR.mkdir()
    assert mb.read_unread_messages("nobody") == []
