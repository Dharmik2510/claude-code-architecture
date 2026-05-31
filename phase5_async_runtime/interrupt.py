"""
Phase 5 — Pattern 19: Real-Time Interrupt Injection
Allow a user (or supervisor agent) to inject new instructions into a
running agent loop without restarting the session.
"""
import asyncio
import os
import queue
import threading
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"

INTERRUPT_QUEUE: queue.Queue[str] = queue.Queue()


def inject_interrupt(message: str) -> None:
    """Queue a user message to be injected before the next model call."""
    INTERRUPT_QUEUE.put(message)


def _stdin_listener() -> None:
    """Background thread: type a line + Enter to interrupt the running agent."""
    while True:
        try:
            line = input()
        except EOFError:
            return
        if line.strip():
            inject_interrupt(line.strip())
            print(f"[Interrupt] Queued: {line.strip()!r}")


async def run_interruptible_agent(task: str, max_turns: int = 20) -> str:
    messages = [{"role": "user", "content": task}]

    listener = threading.Thread(target=_stdin_listener, daemon=True)
    listener.start()
    print("[Interrupt] Type a message and press Enter to redirect the agent.\n")

    for _ in range(max_turns):
        while not INTERRUPT_QUEUE.empty():
            interrupt = INTERRUPT_QUEUE.get_nowait()
            messages.append({"role": "user", "content": f"[INTERRUPT] {interrupt}"})
            print(f"[Interrupt] Injected into context: {interrupt!r}")

        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if hasattr(b, "text")),
                "",
            )

    return "(agent reached max turns)"


if __name__ == "__main__":
    result = asyncio.run(run_interruptible_agent(
        "Describe three ways to build a coding agent. After each point, pause briefly."
    ))
    print("\nFinal:", result[:500])
