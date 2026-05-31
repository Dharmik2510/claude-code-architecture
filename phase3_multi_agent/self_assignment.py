"""
Phase 3 — Pattern 11: Autonomous Task Self-Assignment
Agents pull work from the shared task graph instead of waiting
for a coordinator to push it. File locking prevents double-claiming.
"""
import json
import fcntl
import os
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from phase2_context_management.task_graph import GRAPH_FILE, mark_done, mark_failed


def claim_next_task(
    agent_name: str,
    capabilities: list[str],
    graph_file: Path = GRAPH_FILE,
) -> Optional[dict]:
    """
    Atomically claim the next available task matching this agent's capabilities.
    Uses an exclusive file lock so two agents never claim the same task.
    Returns the claimed task dict, or None if nothing is available.
    """
    if not graph_file.exists():
        return None

    with open(graph_file, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            graph = json.load(f)
            done_ids = {tid for tid, t in graph.items() if t["status"] == "done"}

            for tid, task in graph.items():
                if task["status"] != "pending":
                    continue
                # All dependencies must be done
                if not all(d in done_ids for d in task.get("depends_on", [])):
                    continue
                # Capability match
                req = task.get("requires_capability")
                if req and req not in capabilities:
                    continue

                # Claim it
                graph[tid]["status"]      = "running"
                graph[tid]["assigned_to"] = agent_name
                graph[tid]["claimed_at"]  = datetime.utcnow().isoformat()

                f.seek(0)
                json.dump(graph, f, indent=2)
                f.truncate()
                return task
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    return None


def agent_worker(
    agent_name: str,
    capabilities: list[str],
    work_fn,                      # callable(task_description: str) → str
    poll_interval: float = 2.0,
    graph_file: Path = GRAPH_FILE,
) -> None:
    """
    Continuously poll the task graph and execute available tasks.
    Stops when no tasks remain.
    """
    print(f"[{agent_name}] Started. Capabilities: {capabilities}")

    while True:
        task = claim_next_task(agent_name, capabilities, graph_file)

        if task is None:
            # Check if all tasks are finished
            if graph_file.exists():
                graph = json.loads(graph_file.read_text())
                active = [t for t in graph.values() if t["status"] in ("pending", "running")]
                if not active:
                    print(f"[{agent_name}] No more tasks. Exiting.")
                    return
            time.sleep(poll_interval)
            continue

        print(f"[{agent_name}] Claimed task: {task['id']}")
        try:
            result = work_fn(task["description"])
            mark_done(task["id"], result, graph_file)
            print(f"[{agent_name}] Completed: {task['id']}")
        except Exception as e:
            mark_failed(task["id"], str(e), graph_file)
            print(f"[{agent_name}] Failed: {task['id']} — {e}")


# ── Example: multiple agents competing for tasks ──────────────────────────────
if __name__ == "__main__":
    from phase2_context_management.task_graph import init

    init([
        {"id": "lint",     "description": "Run pylint on src/",           "depends_on": [], "requires_capability": "shell"},
        {"id": "test",     "description": "Run pytest tests/",            "depends_on": [], "requires_capability": "shell"},
        {"id": "typecheck","description": "Run mypy on src/",             "depends_on": [], "requires_capability": "shell"},
        {"id": "report",   "description": "Summarise lint/test/typecheck","depends_on": ["lint","test","typecheck"], "requires_capability": "writing"},
    ])

    def fake_work(description: str) -> str:
        time.sleep(0.5)   # simulate work
        return f"Done: {description[:50]}"

    agents = [
        ("agent-shell-1", ["shell"]),
        ("agent-shell-2", ["shell"]),
        ("agent-writer",  ["writing"]),
    ]

    threads = [
        threading.Thread(
            target=agent_worker,
            args=(name, caps, fake_work),
            daemon=True,
        )
        for name, caps in agents
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    print("\nFinal graph:")
    graph = json.loads(GRAPH_FILE.read_text())
    for tid, t in graph.items():
        print(f"  [{t['status']:<10}] {tid} (assigned to: {t.get('assigned_to','—')})")
