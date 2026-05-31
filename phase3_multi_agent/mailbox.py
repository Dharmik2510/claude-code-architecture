"""
Phase 3 — Pattern 9: Persistent Agent Mailboxes (JSONL)
Each agent has an inbox file. Messages survive process restarts.
"""
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

MAILBOX_DIR = Path(".agent_mailboxes")
MAILBOX_DIR.mkdir(exist_ok=True)


def send_message(
    to_agent: str,
    from_agent: str,
    message: dict,
) -> str:
    """
    Drop a message into an agent's inbox.
    Returns the message ID.
    """
    inbox = MAILBOX_DIR / f"{to_agent}.jsonl"
    envelope = {
        "id":        str(uuid.uuid4()),
        "from":      from_agent,
        "to":        to_agent,
        "timestamp": datetime.utcnow().isoformat(),
        "read":      False,
        **message,
    }
    with inbox.open("a") as f:
        f.write(json.dumps(envelope) + "\n")
    return envelope["id"]


def read_unread_messages(agent_name: str) -> list[dict]:
    """
    Return all unread messages for this agent and mark them read.
    """
    inbox = MAILBOX_DIR / f"{agent_name}.jsonl"
    if not inbox.exists():
        return []

    unread = []
    updated_lines = []

    for line in inbox.read_text().strip().splitlines():
        if not line.strip():
            continue
        msg = json.loads(line)
        if not msg.get("read"):
            unread.append(msg)
            msg["read"] = True
        updated_lines.append(json.dumps(msg))

    inbox.write_text("\n".join(updated_lines) + "\n")
    return unread


def reply_to_message(
    original: dict,
    from_agent: str,
    reply_body: dict,
) -> str:
    """Reply to a message, preserving the thread ID."""
    return send_message(
        to_agent=original["from"],
        from_agent=from_agent,
        message={
            **reply_body,
            "reply_to":  original["id"],
            "thread_id": original.get("thread_id", original["id"]),
        },
    )


def peek_inbox(agent_name: str) -> str:
    """Return a summary of an agent's inbox (for debugging)."""
    inbox = MAILBOX_DIR / f"{agent_name}.jsonl"
    if not inbox.exists():
        return f"No inbox for '{agent_name}'"
    msgs = [json.loads(l) for l in inbox.read_text().strip().splitlines() if l.strip()]
    unread = sum(1 for m in msgs if not m.get("read"))
    return f"Inbox '{agent_name}': {len(msgs)} total, {unread} unread"


# ── Example usage ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Coordinator sends work to the reviewer
    msg_id = send_message(
        to_agent="reviewer",
        from_agent="coordinator",
        message={"type": "review_request", "file": "src/auth.py", "focus": "security"},
    )
    print(f"Sent message {msg_id}")

    # Reviewer reads its inbox
    unread = read_unread_messages("reviewer")
    for msg in unread:
        print(f"Reviewer received: {msg['type']} for {msg['file']}")

        # Reviewer replies
        reply_to_message(msg, "reviewer", {
            "type":     "review_complete",
            "findings": "No critical issues. One medium: missing rate limiting on /login.",
        })

    # Coordinator reads the reply
    replies = read_unread_messages("coordinator")
    for r in replies:
        print(f"Coordinator received reply: {r['findings']}")
