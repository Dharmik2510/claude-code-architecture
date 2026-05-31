"""
Example: Parallel Refactor with Git Worktrees
==============================================
Demonstrates Phase 3 Patterns 11–12:
- Two agents claim independent tasks from a shared graph
- Each agent works in an isolated Git worktree (no file conflicts)

Usage:
    python examples/run_refactor.py
"""
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase2_context_management.task_graph import init, get_ready, mark_done, status_report
from phase3_multi_agent.self_assignment import claim_next_task
from phase3_multi_agent.worktree import create_worktree, cleanup_worktree


REFACTOR_TASKS = [
    {
        "id": "rename-utils",
        "description": "In the worktree, find any function named 'helper' in Python files and rename it to 'util_fn' in comments only (do not change code logic). Report what you found.",
        "depends_on": [],
        "requires_capability": "refactor",
    },
    {
        "id": "add-type-hints",
        "description": "In the worktree, read phase1_core_loop/tools.py and list which functions already have type hints. Write findings to TYPE_HINTS.md in the worktree root.",
        "depends_on": [],
        "requires_capability": "refactor",
    },
]


def run_claimed_task(agent_id: str, task: dict, worktree_path: Path) -> str:
    """Simulate agent work inside an isolated worktree (no API call required for demo)."""
    report = worktree_path / f"{task['id']}-report.txt"
    report.write_text(
        f"Agent {agent_id} completed {task['id']} in {worktree_path}\n"
        f"Description: {task['description']}\n"
    )
    return report.read_text()


def agent_worker(agent_id: str, capabilities: list[str]):
    while True:
        task = claim_next_task(agent_id, capabilities)
        if task is None:
            graph_path = Path(".task_graph.json")
            if graph_path.exists():
                import json
                graph = json.loads(graph_path.read_text())
                if all(t["status"] in ("done", "failed") for t in graph.values()):
                    return
            time.sleep(0.5)
            continue

        wt = create_worktree(task["id"])
        print(f"[{agent_id}] Claimed '{task['id']}' → worktree {wt}")
        try:
            result = run_claimed_task(agent_id, task, wt)
            mark_done(task["id"], result)
        finally:
            cleanup_worktree(task["id"], force=True)


if __name__ == "__main__":
    init(REFACTOR_TASKS)
    agents = [
        threading.Thread(
            target=agent_worker,
            args=(f"refactor-{i}", ["refactor"]),
            daemon=True,
        )
        for i in range(2)
    ]
    for a in agents:
        a.start()
    for a in agents:
        a.join(timeout=60)

    print(status_report())
