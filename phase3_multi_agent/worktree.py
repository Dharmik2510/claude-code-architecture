"""
Phase 3 — Pattern 12: Git Worktree Task Isolation
Each parallel agent gets its own checkout of the repo on a dedicated branch.
No file conflicts. No test interference. Clean PR per task.
"""
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

WORKTREE_BASE = Path(".worktrees")
WORKTREE_BASE.mkdir(exist_ok=True)


def create_worktree(task_id: str, base_branch: str = "main") -> Path:
    """
    Create an isolated Git worktree for a task.
    Returns the path to the new worktree directory.
    """
    worktree_path = WORKTREE_BASE / task_id
    branch_name   = f"agent/{task_id}"

    result = subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_branch],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git worktree add failed: {result.stderr.strip()}")

    print(f"[Worktree] Created: {worktree_path}  (branch: {branch_name})")
    return worktree_path


def commit_worktree(task_id: str, message: str) -> str:
    """Stage and commit all changes in a task's worktree."""
    worktree_path = WORKTREE_BASE / task_id
    subprocess.run(["git", "add", "-A"], cwd=worktree_path, check=True)
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=worktree_path, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return f"Nothing to commit: {result.stderr.strip()}"
    return result.stdout.strip()


def get_diff(task_id: str) -> str:
    """Return the diff of all changes in the worktree vs its base branch."""
    worktree_path = WORKTREE_BASE / task_id
    result = subprocess.run(
        ["git", "diff", "HEAD"],
        cwd=worktree_path, capture_output=True, text=True,
    )
    return result.stdout[:4000] if result.stdout else "(no uncommitted changes)"


def cleanup_worktree(task_id: str, force: bool = False) -> None:
    """Remove the worktree directory and delete its branch."""
    worktree_path = WORKTREE_BASE / task_id
    branch_name   = f"agent/{task_id}"

    cmd = ["git", "worktree", "remove", str(worktree_path)]
    if force:
        cmd.append("--force")
    subprocess.run(cmd, capture_output=True)
    subprocess.run(["git", "branch", "-D", branch_name], capture_output=True)
    print(f"[Worktree] Cleaned up: {task_id}")


def list_active_worktrees() -> str:
    """List all currently registered git worktrees."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True, text=True,
    )
    return result.stdout if result.stdout else "No worktrees found."


# ── Example usage ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os, sys

    # Ensure we're in a git repo
    if not Path(".git").exists():
        print("Run this from the root of a git repository.")
        sys.exit(1)

    task_id = "demo-task-001"

    # Create isolated workspace
    wt_path = create_worktree(task_id)
    print(f"Working in: {wt_path}")

    # Simulate agent writing a file
    (wt_path / "agent_output.txt").write_text(
        f"Agent completed task {task_id} at {datetime.now(timezone.utc).isoformat()}\n"
    )

    # Commit the work
    log = commit_worktree(task_id, f"feat: complete {task_id}")
    print(f"Committed: {log}")

    print("\nActive worktrees:")
    print(list_active_worktrees())

    # Clean up
    cleanup_worktree(task_id, force=True)
    print("Done.")
