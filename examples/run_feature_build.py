"""
Example: Build a Feature with a Task Dependency Graph
======================================================
Demonstrates Phase 2 (task graph) + Phase 1 (agent loop).

Creates a task graph for a feature build, then runs the agent
on each task in dependency order.

Usage:
    python examples/run_feature_build.py
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase1_core_loop.agent import run_agent

GRAPH_FILE = Path(".task_graph.json")

FEATURE_TASKS = [
    {
        "id": "design",
        "description": "Create a simple Python function that validates an email address using regex. Write it to src/validators.py with docstring.",
        "depends_on": [],
    },
    {
        "id": "tests",
        "description": "Read src/validators.py, then write pytest tests covering valid emails, invalid emails, and edge cases to tests/test_validators.py.",
        "depends_on": ["design"],
    },
    {
        "id": "run_tests",
        "description": "Run 'python -m pytest tests/test_validators.py -v' and report results. If tests fail, fix src/validators.py.",
        "depends_on": ["tests"],
    },
    {
        "id": "document",
        "description": "Read src/validators.py and write a README section about the email validator to docs/validators.md.",
        "depends_on": ["run_tests"],
    },
]


def init_graph():
    graph = {
        t["id"]: {**t, "status": "pending", "result": None}
        for t in FEATURE_TASKS
    }
    GRAPH_FILE.write_text(json.dumps(graph, indent=2))
    return graph


def get_ready(graph):
    done = {tid for tid, t in graph.items() if t["status"] == "done"}
    return [
        t for tid, t in graph.items()
        if t["status"] == "pending"
        and all(d in done for d in t.get("depends_on", []))
    ]


def mark_done(graph, task_id, result):
    graph[task_id]["status"] = "done"
    graph[task_id]["result"] = result[:200]
    GRAPH_FILE.write_text(json.dumps(graph, indent=2))


if __name__ == "__main__":
    print("Initializing task graph...")
    graph = init_graph()

    while True:
        ready = get_ready(graph)
        if not ready:
            all_done = all(t["status"] == "done" for t in graph.values())
            if all_done:
                print("\nAll tasks complete!")
            else:
                print("\nNo tasks ready (check for failed dependencies).")
            break

        for task in ready:
            print(f"\n[Graph] Running task: {task['id']}")
            graph[task["id"]]["status"] = "running"

            result = run_agent(task["description"])
            mark_done(graph, task["id"], result)
            print(f"[Graph] Task '{task['id']}' done.")

    print("\nFinal graph state:")
    for tid, t in graph.items():
        print(f"  [{t['status'].upper():<8}] {tid}")
