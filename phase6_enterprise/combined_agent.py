"""
Phase 6 — All 23 Patterns Combined
Reference entry point that wires every component together.

Run:  python phase6_enterprise/combined_agent.py
Requires: ANTHROPIC_API_KEY set in environment
Optional: Redis running on localhost:6379 for Phase 6 mailboxes
"""
import asyncio
import os
import sys
import json
import threading
import time
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phase1_core_loop.tools       import TOOL_SCHEMAS, TOOL_HANDLERS
from phase1_core_loop.todo_tools  import TODO_SCHEMAS, TODO_HANDLERS
from phase2_context_management.task_graph   import init as init_graph, get_ready, mark_done, mark_failed, status_report
from phase2_context_management.skill_loader import SkillLoader
from phase3_multi_agent.background_tasks    import run_background_task, check_notifications
from phase3_multi_agent.mailbox             import send_message, read_unread_messages
from phase4_production.snapshots            import tool_safe_write
from phase4_production.permissions          import governed_tool_call
from phase4_production.event_bus            import subscribe, log_all_calls, audit_writes
from phase4_production.session_store        import save_session, load_session
from phase5_async_runtime.async_agent       import run_async_agent


DEMO_TASKS = [
    {
        "id": "design",
        "description": "Create a simple Python calculator module at src/calculator.py with add, subtract, multiply, divide functions. Include docstrings.",
        "depends_on": [],
        "requires_capability": "coding",
    },
    {
        "id": "tests",
        "description": "Read src/calculator.py and write pytest tests for all four functions at tests/test_calculator.py. Cover edge cases like division by zero.",
        "depends_on": ["design"],
        "requires_capability": "coding",
    },
    {
        "id": "run_tests",
        "description": "Run 'python -m pytest tests/test_calculator.py -v' and report the results. If tests fail, fix src/calculator.py.",
        "depends_on": ["tests"],
        "requires_capability": "coding",
    },
    {
        "id": "document",
        "description": "Read src/calculator.py and write a README section about the calculator module to docs/calculator.md.",
        "depends_on": ["run_tests"],
        "requires_capability": "writing",
    },
]


def setup_event_bus():
    """Wire up observability subscribers."""
    subscribe("*",          log_all_calls)
    subscribe("after_call", audit_writes)


def run_agent_on_task(task: dict) -> str:
    """Run a single agent turn on a task description, with all hardening layers."""
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Governed + snapshotting tool handlers
    safe_handlers = {
        **TOOL_HANDLERS,
        "write_file": tool_safe_write,        # Phase 4: snapshots
        **TODO_HANDLERS,
    }

    def dispatch(tool_name, tool_args):
        return governed_tool_call(tool_name, tool_args, safe_handlers)  # Phase 4: permissions

    all_tools = TOOL_SCHEMAS + TODO_SCHEMAS
    messages  = [{"role": "user", "content": task["description"]}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            tools=all_tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            result = next((b.text for b in response.content if hasattr(b, "text")), "")
            save_session(f"task-{task['id']}", messages)  # Phase 4: persistence
            return result

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                out = dispatch(block.name, block.input)
            except Exception as e:
                out = f"Error: {e}"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(out),
            })
        messages.append({"role": "user", "content": tool_results})


def main():
    print("=" * 60)
    print("Claude Code Architecture — All 23 Patterns")
    print("=" * 60)

    # Phase 4: event bus
    setup_event_bus()

    # Phase 2: task dependency graph
    print("\n[Phase 2] Initializing task graph...")
    init_graph(DEMO_TASKS)

    # Phase 3: parallel agents (background threads, pull-based)
    completed = set()

    def agent_worker(agent_id: str, capabilities: list[str]):
        while True:
            ready = get_ready()
            available = [
                t for t in ready
                if t["id"] not in completed
                and (not t.get("requires_capability") or t["requires_capability"] in capabilities)
            ]
            if not available:
                # Check if all done
                graph = json.loads(Path(".task_graph.json").read_text())
                if all(t["status"] in ("done", "failed") for t in graph.values()):
                    return
                time.sleep(1)
                continue

            task = available[0]
            completed.add(task["id"])
            print(f"\n[{agent_id}] Starting task: {task['id']}")

            try:
                result = run_agent_on_task(task)
                mark_done(task["id"], result)
                print(f"[{agent_id}] Done: {task['id']}")
            except Exception as e:
                mark_failed(task["id"], str(e))
                print(f"[{agent_id}] Failed: {task['id']} — {e}")

    agents = [
        threading.Thread(target=agent_worker, args=(f"agent-{i}", ["coding", "writing"]), daemon=True)
        for i in range(2)
    ]
    for a in agents:
        a.start()
    for a in agents:
        a.join(timeout=300)

    print("\n" + status_report())
    print("\nDone. Session states saved to .sessions/")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)
    main()
