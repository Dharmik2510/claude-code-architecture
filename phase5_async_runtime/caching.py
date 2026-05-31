"""
Phase 5 — Pattern 20: Prompt Cache Configuration
Mark stable context blocks (system prompt, tool schemas) as cacheable
so repeated turns pay reduced input-token costs.

Uses Anthropic's prompt caching API (cache_control breakpoints).
See: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
"""
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"


def cached_system_block(text: str) -> list[dict]:
    """Wrap a system prompt in a cacheable content block."""
    return [{
        "type": "text",
        "text": text,
        "cache_control": {"type": "ephemeral"},
    }]


def create_cached_message(
    *,
    system: str,
    tools: list[dict],
    messages: list[dict],
    max_tokens: int = 4096,
):
    """
    Call the Messages API with prompt caching enabled on system + tools.
    Tool definitions are stable across turns — ideal cache candidates.
    """
    cached_tools = []
    for i, tool in enumerate(tools):
        entry = {**tool}
        if i == len(tools) - 1:
            entry["cache_control"] = {"type": "ephemeral"}
        cached_tools.append(entry)

    return client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=cached_system_block(system),
        tools=cached_tools,
        messages=messages,
    )


def print_cache_usage(response) -> None:
    """Print cache read/write token counts from a response (if present)."""
    usage = getattr(response, "usage", None)
    if not usage:
        return
    read  = getattr(usage, "cache_read_input_tokens", 0) or 0
    write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    if read or write:
        print(f"  [Cache] read={read} tokens, write={write} tokens")


if __name__ == "__main__":
    SYSTEM = "You are a concise coding assistant. Answer in one paragraph."
    msgs   = [{"role": "user", "content": "What is a tool dispatch map?"}]

    r1 = create_cached_message(system=SYSTEM, tools=[], messages=msgs)
    print_cache_usage(r1)
    print("Turn 1:", next(b.text for b in r1.content if hasattr(b, "text")))

    msgs.append({"role": "assistant", "content": r1.content})
    msgs.append({"role": "user", "content": "Give one Python example."})

    r2 = create_cached_message(system=SYSTEM, tools=[], messages=msgs)
    print_cache_usage(r2)
    print("Turn 2:", next(b.text for b in r2.content if hasattr(b, "text")))
