"""
Phase 2 — Pattern 7: File-Based Task Dependency Graph
Task state persisted to disk. Survives process restarts and context resets.
"""
import json
import fcntl
from pathlib import Path
from datetime import datetime
from typing import Optional


GRAPH_FILE = Path(".task_graph.json")


def init(tasks: list[dict], graph_file: Path = GRAPH_FILE) -> None:
    """
    Initialize the graph from a list of task definitions.
    Each task: {id, description, depends_on: [...], requires_capability: str|None}
    """
    graph = {}
    for task in tasks:
        graph[task["id"]] = {
            **task,
            "status":     "pending",
            "result":     None,
            "assigned_to": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    graph_file.write_text(json.dumps(graph, indent=2))


def get_ready(graph_file: Path = GRAPH_FILE) -> list[dict]:
    """Return all tasks whose dependencies are fully satisfied."""
    if not graph_file.exists():
        return []
    graph = json.loads(graph_file.read_text())
    done  = {tid for tid, t in graph.items() if t["status"] == "done"}
    return [
        t for tid, t in graph.items()
        if t["status"] == "pending"
        and all(d in done for d in t.get("depends_on", []))
    ]


def claim(
    agent_name: str,
    capabilities: list[str],
    graph_file: Path = GRAPH_FILE,
) -> Optional[dict]:
    """Atomically claim the next available task matching the agent's capabilities."""
    with open(graph_file, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            graph = json.load(f)
            done  = {tid for tid, t in graph.items() if t["status"] == "done"}

            for tid, task in graph.items():
                if task["status"] != "pending":
                    continue
                if not all(d in done for d in task.get("depends_on", [])):
                    continue
                req = task.get("requires_capability")
                if req and req not in capabilities:
                    continue

                graph[tid]["status"]      = "running"
                graph[tid]["assigned_to"] = agent_name
                graph[tid]["updated_at"]  = datetime.utcnow().isoformat()

                f.seek(0)
                json.dump(graph, f, indent=2)
                f.truncate()
                return task
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return None


def mark_done(task_id: str, result: str, graph_file: Path = GRAPH_FILE) -> None:
    graph = json.loads(graph_file.read_text())
    graph[task_id].update(status="done", result=result[:500],
                          updated_at=datetime.utcnow().isoformat())
    graph_file.write_text(json.dumps(graph, indent=2))


def mark_failed(task_id: str, error: str, graph_file: Path = GRAPH_FILE) -> None:
    graph = json.loads(graph_file.read_text())
    graph[task_id].update(status="failed", result=error[:500],
                          updated_at=datetime.utcnow().isoformat())
    graph_file.write_text(json.dumps(graph, indent=2))


def status_report(graph_file: Path = GRAPH_FILE) -> str:
    if not graph_file.exists():
        return "No task graph found."
    graph = json.loads(graph_file.read_text())
    lines = ["Task Graph Status:"]
    for tid, task in graph.items():
        deps = ", ".join(task.get("depends_on", [])) or "—"
        lines.append(
            f"  [{task['status'].upper():<10}] {tid:<20} deps=[{deps}]"
        )
    return "\n".join(lines)
