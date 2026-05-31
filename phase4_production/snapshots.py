"""
Phase 4 — Pattern 14: File Snapshots (Reversible Writes)
Every file write is automatically backed up. Any write can be undone.
"""
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

SNAPSHOT_DIR = Path(".file_snapshots")
SNAPSHOT_DIR.mkdir(exist_ok=True)


def _safe_name(filepath: str) -> str:
    return filepath.replace("/", "_").replace("\\", "_").lstrip("._")


def snapshot_before_write(filepath: str) -> Optional[str]:
    """Snapshot an existing file before overwriting. Returns snapshot path or None."""
    path = Path(filepath)
    if not path.exists():
        return None
    ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    snapshot = SNAPSHOT_DIR / f"{_safe_name(filepath)}__{ts}"
    shutil.copy2(path, snapshot)
    return str(snapshot)


def revert_file(filepath: str) -> str:
    """Restore a file from its most recent snapshot."""
    pattern   = f"{_safe_name(filepath)}__*"
    snapshots = sorted(SNAPSHOT_DIR.glob(pattern), reverse=True)
    if not snapshots:
        return f"No snapshots found for {filepath}."
    shutil.copy2(snapshots[0], filepath)
    return f"Reverted {filepath} to {snapshots[0].name}"


def list_snapshots(filepath: str) -> str:
    pattern   = f"{_safe_name(filepath)}__*"
    snapshots = sorted(SNAPSHOT_DIR.glob(pattern), reverse=True)
    if not snapshots:
        return f"No snapshots for {filepath}."
    return "\n".join(s.name for s in snapshots)


def tool_safe_write(args: dict) -> str:
    """Drop-in replacement for write_file that auto-snapshots first."""
    filepath = args["path"]
    content  = args["content"]
    snapshot = snapshot_before_write(filepath)
    path     = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    note = f" Previous version saved." if snapshot else ""
    return f"Written {len(content)} bytes to {filepath}.{note}"
