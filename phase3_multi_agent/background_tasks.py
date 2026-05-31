"""
Phase 3 — Pattern 8: Background Task Execution with Notifications
Long-running subtasks run in a thread; master loop gets notified when done.
"""
import threading
import queue
import time
import os
from anthropic import Anthropic

# Shared queue — background agents post results here
NOTIFICATION_QUEUE: queue.Queue = queue.Queue()


def run_background_task(
    task_id: str,
    task_description: str,
    tools: list,
    tool_handlers: dict,
    model: str = "claude-sonnet-4-6",
) -> None:
    """
    Spawn a complete agent loop in a background thread.
    Posts a notification dict to NOTIFICATION_QUEUE when finished.
    """
    def _run():
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        messages = [{"role": "user", "content": task_description}]

        while True:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                tools=tools,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                result = next(
                    (b.text for b in response.content if hasattr(b, "text")),
                    "Task completed with no text output.",
                )
                NOTIFICATION_QUEUE.put({
                    "task_id":   task_id,
                    "status":    "done",
                    "result":    result,
                    "timestamp": time.time(),
                })
                return

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                handler = tool_handlers.get(block.name)
                try:
                    out = handler(block.input) if handler else f"Unknown tool: {block.name}"
                except Exception as e:
                    out = f"Error: {e}"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(out),
                })
            messages.append({"role": "user", "content": tool_results})

    thread = threading.Thread(target=_run, daemon=True, name=f"agent-{task_id}")
    thread.start()
    print(f"[Background] Task '{task_id}' started in thread {thread.name}")


def check_notifications() -> list[dict]:
    """Drain the notification queue and return all pending results."""
    results = []
    while not NOTIFICATION_QUEUE.empty():
        try:
            results.append(NOTIFICATION_QUEUE.get_nowait())
        except queue.Empty:
            break
    return results


def run_master_loop_with_background(
    task: str,
    master_tools: list,
    master_handlers: dict,
    model: str = "claude-sonnet-4-6",
) -> str:
    """
    Master agent loop that checks for background task completions
    and injects them into its context on each turn.
    """
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": task}]

    while True:
        # Inject any completed background task results
        notifications = check_notifications()
        if notifications:
            note_text = "\n".join(
                f"[DONE] Background task '{n['task_id']}': {n['result'][:300]}"
                for n in notifications
            )
            messages.append({"role": "user", "content": f"[BACKGROUND UPDATES]\n{note_text}"})
            print(f"[Master] Received {len(notifications)} background completion(s)")

        response = client.messages.create(
            model=model,
            max_tokens=8096,
            tools=master_tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            handler = master_handlers.get(block.name)
            try:
                out = handler(block.input) if handler else f"Unknown tool: {block.name}"
            except Exception as e:
                out = f"Error: {e}"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(out),
            })
        messages.append({"role": "user", "content": tool_results})
