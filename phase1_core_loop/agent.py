"""
Phase 1 — The Core Agent Loop
Pattern 1: Minimal while loop (perceive → decide → act)
"""
import os
from pathlib import Path
from anthropic import Anthropic

from tools import TOOL_SCHEMAS, TOOL_HANDLERS
from todo_tools import TODO_SCHEMAS, TODO_HANDLERS

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"

SYSTEM_PROMPT = f"""You are a coding agent working in {Path.cwd()}.
Use the available tools to complete the user's task.

Before executing any multi-step task:
1. Call todo_write with a complete, ordered list of steps.
2. Call todo_update to mark each step in_progress before starting it.
3. Call todo_update to mark it completed when done.
4. If a step fails, mark it failed and adapt your plan.

When finished, say DONE."""

ALL_TOOLS    = TOOL_SCHEMAS + TODO_SCHEMAS
ALL_HANDLERS = {**TOOL_HANDLERS, **TODO_HANDLERS}


def run_agent(user_task: str) -> str:
    """Run the agent on a task and return the final response."""
    messages = [{"role": "user", "content": user_task}]

    print(f"\n[Agent] Starting task: {user_task}\n")

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=ALL_TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            print(f"\n[Agent] Done.\n")
            return final

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            print(f"  [Tool] {block.name}({list(block.input.keys())})")

            handler = ALL_HANDLERS.get(block.name)
            if handler is None:
                result = f"Error: unknown tool '{block.name}'"
            else:
                try:
                    result = handler(block.input)
                except Exception as e:
                    result = f"Error: {e}"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result),
            })

        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    task = (
        "List the Python files in the current directory, "
        "read the first one you find, and write a one-paragraph "
        "summary of what it does to summary.txt"
    )
    result = run_agent(task)
    print("Final output:", result)
