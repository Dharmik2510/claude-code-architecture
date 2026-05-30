"""
Example: End-to-End Multi-Agent Code Review
============================================
Demonstrates Phases 1-3:
- Master coordinator spawns a background reviewer agent
- Reviewer uses JSONL mailbox to send findings back
- Coordinator waits for notification then summarizes

Usage:
    python examples/run_code_review.py path/to/file.py
"""
import sys
import os
import threading
import queue
import time
from pathlib import Path
from anthropic import Anthropic

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

NOTIFICATION_QUEUE: queue.Queue = queue.Queue()

# ── Minimal tool set for the reviewer ────────────────────────────────────────
def read_file(args):
    p = Path(args["path"])
    return p.read_text(errors="replace") if p.exists() else f"Not found: {p}"

REVIEWER_TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file for review.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    }
]
REVIEWER_HANDLERS = {"read_file": read_file}


# ── Background reviewer agent ─────────────────────────────────────────────────
def run_reviewer(filepath: str) -> None:
    def _work():
        messages = [{
            "role": "user",
            "content": (
                f"Review {filepath} for: (1) bugs, (2) security issues, "
                f"(3) code quality problems. Be concise and specific."
            ),
        }]

        while True:
            resp = client.messages.create(
                model=MODEL, max_tokens=2048,
                tools=REVIEWER_TOOLS, messages=messages,
            )
            messages.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason == "end_turn":
                final = next((b.text for b in resp.content if hasattr(b, "text")), "")
                NOTIFICATION_QUEUE.put({"task": "review", "result": final})
                return

            results = []
            for block in resp.content:
                if block.type != "tool_use":
                    continue
                handler = REVIEWER_HANDLERS.get(block.name)
                out = handler(block.input) if handler else "Unknown tool"
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(out)})
            messages.append({"role": "user", "content": results})

    thread = threading.Thread(target=_work, daemon=True)
    thread.start()


# ── Coordinator ────────────────────────────────────────────────────────────────
def coordinate_review(filepath: str) -> None:
    print(f"\n[Coordinator] Dispatching review of {filepath}...")
    run_reviewer(filepath)

    print("[Coordinator] Review running in background. Waiting for results...")

    # Poll for notification
    while True:
        time.sleep(1)
        try:
            notification = NOTIFICATION_QUEUE.get_nowait()
        except queue.Empty:
            continue

        print("\n" + "=" * 60)
        print("CODE REVIEW FINDINGS")
        print("=" * 60)
        print(notification["result"])
        print("=" * 60)
        break


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "phase1_core_loop/agent.py"
    coordinate_review(target)
