"""
Phase 1 — Pattern 4: Subagent Isolation
Run a focused subtask in a fresh context window. The parent agent
receives only the final summary — not intermediate tool noise.
"""
import os
from anthropic import Anthropic

from tools import TOOL_SCHEMAS, TOOL_HANDLERS

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"

SUBAGENT_PROMPT = """You are a focused subagent. Complete the assigned subtask
using the available tools. When finished, return a concise summary of what
you did and any important findings. Do not ask follow-up questions."""


def run_subagent(subtask: str, max_turns: int = 10) -> str:
    """
    Run an isolated agent loop on a single subtask.
    Returns a summary string for the parent agent to consume.
    """
    messages = [{"role": "user", "content": subtask}]

    for _ in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SUBAGENT_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if hasattr(b, "text")),
                "(subagent finished with no text output)",
            )

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            handler = TOOL_HANDLERS.get(block.name)
            try:
                result = handler(block.input) if handler else f"Unknown tool: {block.name}"
            except Exception as e:
                result = f"Error: {e}"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result),
            })
        messages.append({"role": "user", "content": tool_results})

    return "(subagent reached max turns without finishing)"


if __name__ == "__main__":
    summary = run_subagent(
        "List all .py files in phase1_core_loop/ and count them."
    )
    print("Subagent summary:", summary)
