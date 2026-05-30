"""
Phase 1 — Pattern 3: TodoWrite Planning
Structured pre-execution plans stored to disk so the model
tracks progress across many tool calls.
"""
import json
from pathlib import Path

TODO_FILE = Path(".agent_todo.json")


def tool_todo_write(args: dict) -> str:
    tasks = args["tasks"]
    TODO_FILE.write_text(json.dumps(tasks, indent=2))
    return f"Plan written: {len(tasks)} steps."


def tool_todo_update(args: dict) -> str:
    if not TODO_FILE.exists():
        return "Error: no active plan. Call todo_write first."
    tasks = json.loads(TODO_FILE.read_text())
    for task in tasks:
        if task["id"] == args["task_id"]:
            task["status"] = args["status"]
            break
    TODO_FILE.write_text(json.dumps(tasks, indent=2))
    pending = sum(1 for t in tasks if t["status"] == "pending")
    return f"Updated '{args['task_id']}' → {args['status']}. {pending} steps remaining."


def tool_todo_read(args: dict) -> str:
    if not TODO_FILE.exists():
        return "No active plan."
    tasks = json.loads(TODO_FILE.read_text())
    lines = [
        f"[{t['status'].upper():<12}] {t['id']}: {t['description']}"
        for t in tasks
    ]
    return "\n".join(lines)


TODO_HANDLERS = {
    "todo_write":  tool_todo_write,
    "todo_update": tool_todo_update,
    "todo_read":   tool_todo_read,
}

TODO_SCHEMAS = [
    {
        "name": "todo_write",
        "description": (
            "Record your step-by-step execution plan before starting any multi-step task. "
            "Each task must have an id, description, and status='pending'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":          {"type": "string"},
                            "description": {"type": "string"},
                            "status":      {"type": "string"},
                        },
                        "required": ["id", "description", "status"],
                    },
                }
            },
            "required": ["tasks"],
        },
    },
    {
        "name": "todo_update",
        "description": "Update the status of a plan step: 'in_progress', 'completed', or 'failed'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status":  {"type": "string"},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "todo_read",
        "description": "Read your current execution plan and check which steps remain.",
        "input_schema": {"type": "object", "properties": {}},
    },
]
