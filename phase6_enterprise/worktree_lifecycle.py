"""
Phase 6 — Pattern 23: Advanced Worktree Lifecycle Management
Creates, tracks, conflict-checks, merges, and prunes Git worktrees
automatically. Keeps the repository clean at scale.
"""
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

REGISTRY_FILE = Path(".worktree_registry.json")
WORKTREE_BASE = Path(".worktrees")
WORKTREE_BASE.mkdir(exist_ok=True)


class WorktreeStatus(str, Enum):
    ACTIVE    = "active"
    IDLE      = "idle"        # task done, not yet merged
    MERGED    = "merged"
    ABANDONED = "abandoned"   # idle too long → auto-pruned
    CONFLICT  = "conflict"    # dry-run merge detected conflicts


def _load() -> dict:
    return json.loads(REGISTRY_FILE.read_text()) if REGISTRY_FILE.exists() else {}

def _save(registry: dict) -> None:
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))

def _git(*args, cwd=None, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd,
        capture_output=True, text=True, check=check,
    )


class WorktreeLifecycleManager:

    def create(
        self,
        task_id: str,
        base_branch: str = "main",
        agent_name: str = "agent",
    ) -> Path:
        """Create a worktree and register it in the lifecycle registry."""
        path        = WORKTREE_BASE / task_id
        branch_name = f"agent/{task_id}"

        result = _git("worktree", "add", "-b", branch_name, str(path), base_branch, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr.strip()}")

        registry = _load()
        registry[task_id] = {
            "task_id":     task_id,
            "branch":      branch_name,
            "path":        str(path),
            "base_branch": base_branch,
            "agent":       agent_name,
            "status":      WorktreeStatus.ACTIVE,
            "created_at":  datetime.now(timezone.utc).isoformat(),
            "updated_at":  datetime.now(timezone.utc).isoformat(),
        }
        _save(registry)
        print(f"[Lifecycle] Created worktree: {path} (branch: {branch_name})")
        return path

    def mark_idle(self, task_id: str) -> None:
        """Signal that the agent finished work; worktree awaits merge review."""
        registry = _load()
        if task_id not in registry:
            return
        registry[task_id].update(
            status=WorktreeStatus.IDLE,
            idle_since=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        _save(registry)

    def check_conflicts(self, task_id: str) -> bool:
        """
        Dry-run the merge to detect conflicts before committing.
        Returns True if the merge would be clean.
        """
        registry = _load()
        entry = registry.get(task_id)
        if not entry:
            return False

        branch      = entry["branch"]
        base_branch = entry["base_branch"]

        # Attempt a no-commit merge
        merge = _git("merge", "--no-commit", "--no-ff", branch, check=False)
        # Always abort regardless of outcome
        _git("merge", "--abort", check=False)

        has_conflicts = merge.returncode != 0
        if has_conflicts:
            registry[task_id]["status"] = WorktreeStatus.CONFLICT
            registry[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save(registry)
            print(f"[Lifecycle] CONFLICT detected in {task_id}")
        return not has_conflicts

    def merge_and_cleanup(self, task_id: str) -> bool:
        """
        Merge the task branch into its base, remove the worktree and branch.
        Returns True on success.
        """
        registry = _load()
        entry = registry.get(task_id)
        if not entry:
            print(f"[Lifecycle] Unknown task: {task_id}")
            return False

        if not self.check_conflicts(task_id):
            print(f"[Lifecycle] Aborting merge for {task_id} — conflicts exist")
            return False

        branch      = entry["branch"]
        path        = Path(entry["path"])

        # Fast-forward merge
        merge = _git("merge", "--ff-only", branch, check=False)
        if merge.returncode != 0:
            print(f"[Lifecycle] Merge failed: {merge.stderr.strip()}")
            return False

        # Remove worktree + branch
        _git("worktree", "remove", str(path), "--force", check=False)
        _git("branch", "-D", branch, check=False)

        registry[task_id].update(
            status=WorktreeStatus.MERGED,
            merged_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        _save(registry)
        print(f"[Lifecycle] Merged and cleaned up: {task_id}")
        return True

    def prune_abandoned(self, max_idle_hours: int = 24) -> list[str]:
        """
        Force-remove worktrees that have been idle longer than max_idle_hours.
        Returns list of pruned task IDs.
        """
        registry = _load()
        cutoff   = datetime.now(timezone.utc) - timedelta(hours=max_idle_hours)
        pruned   = []

        for task_id, entry in list(registry.items()):
            if entry["status"] not in (WorktreeStatus.IDLE, WorktreeStatus.CONFLICT):
                continue
            idle_since = entry.get("idle_since") or entry["created_at"]
            if datetime.fromisoformat(idle_since) > cutoff:
                continue

            path   = Path(entry["path"])
            branch = entry["branch"]
            _git("worktree", "remove", str(path), "--force", check=False)
            _git("branch", "-D", branch, check=False)
            registry[task_id]["status"]     = WorktreeStatus.ABANDONED
            registry[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            pruned.append(task_id)
            print(f"[Lifecycle] Pruned abandoned worktree: {task_id}")

        _save(registry)
        return pruned

    def status_report(self) -> str:
        registry = _load()
        if not registry:
            return "No worktrees registered."
        lines = ["Worktree Registry:"]
        for task_id, entry in sorted(registry.items()):
            lines.append(
                f"  [{entry['status'].upper():<12}] {task_id:<24} "
                f"branch={entry['branch']}  agent={entry['agent']}"
            )
        return "\n".join(lines)


# ── Example ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if not Path(".git").exists():
        print("Run from the root of a git repository.")
        sys.exit(1)

    mgr = WorktreeLifecycleManager()

    # Simulate two parallel tasks
    for tid in ["task-auth", "task-payments"]:
        try:
            mgr.create(tid, base_branch="main", agent_name="agent-1")
            # Simulate agent writing a file in the worktree
            wt_path = Path(f".worktrees/{tid}")
            (wt_path / f"{tid}_output.txt").write_text(f"Work from {tid}\n")
            subprocess.run(["git", "add", "-A"], cwd=wt_path)
            subprocess.run(["git", "commit", "-m", f"feat: {tid}"], cwd=wt_path)
            mgr.mark_idle(tid)
        except Exception as e:
            print(f"Skipped {tid}: {e}")

    print(mgr.status_report())
    pruned = mgr.prune_abandoned(max_idle_hours=0)   # prune immediately for demo
    print(f"\nPruned: {pruned}")
    print(mgr.status_report())
