"""
Phase 4 — Pattern 13: Real-Time Token Streaming
Stream model output token-by-token so users see reasoning as it happens.
"""
import os
import sys
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"


def run_streaming_agent(task: str) -> str:
    """Run one agent turn with streaming enabled. Returns the full response text."""
    messages = [{"role": "user", "content": task}]
    collected: list[str] = []

    print("\n[Streaming] ", end="", flush=True)

    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            collected.append(text)

    print("\n")
    return "".join(collected)


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else (
        "Explain in two paragraphs what an agent loop is and why tool use matters."
    )
    result = run_streaming_agent(task)
    print(f"\n[Done] {len(result)} characters streamed.")
