"""
Phase 4 — Pattern 17: Session Persistence, Resume, and Fork
Agent state (message history) is saved after every turn.
Resuming restores exact context. Forking branches from any saved point.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

SESSIONS_DIR = Path(".sessions")
SESSIONS_DIR.mkdir(exist_ok=True)


def save_session(
    session_id: str,
    messages: list[dict],
    metadata: Optional[dict] = None,
) -> str:
    """Persist session state. Overwrites 'latest' and keeps timestamped backup."""
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    state = {
        "session_id":    session_id,
        "saved_at":      datetime.utcnow().isoformat(),
        "message_count": len(messages),
        "messages":      messages,
        "metadata":      metadata or {},
    }
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    (session_dir / f"state_{ts}.json").write_text(json.dumps(state, indent=2))
    (session_dir / "latest.json").write_text(json.dumps(state, indent=2))
    return str(session_dir / "latest.json")


def load_session(session_id: str) -> Optional[dict]:
    """Load the most recent state for a session."""
    latest = SESSIONS_DIR / session_id / "latest.json"
    if not latest.exists():
        return None
    return json.loads(latest.read_text())


def fork_session(source_id: str, fork_id: str) -> Optional[dict]:
    """Create a new session starting from the same message history as source."""
    source = load_session(source_id)
    if not source:
        return None
    fork = {
        **source,
        "session_id":  fork_id,
        "forked_from": source_id,
        "forked_at":   datetime.utcnow().isoformat(),
    }
    save_session(fork_id, fork["messages"], fork.get("metadata", {}))
    return fork


def list_sessions() -> str:
    if not SESSIONS_DIR.exists():
        return "No sessions."
    lines = ["Saved sessions:"]
    for d in sorted(SESSIONS_DIR.iterdir()):
        latest = d / "latest.json"
        if latest.exists():
            s = json.loads(latest.read_text())
            lines.append(
                f"  {d.name}: {s['message_count']} messages, "
                f"saved {s['saved_at'][:19]}"
            )
    return "\n".join(lines) if len(lines) > 1 else "No sessions."
