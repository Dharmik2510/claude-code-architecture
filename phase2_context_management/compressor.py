"""
Phase 2 — Pattern 6: Three-Layer Context Compression
Keeps long sessions within the context window without losing active state.

Layer 1 — Summarize old conversation clusters (keep recent turns verbatim)
Layer 2 — Truncate oversized tool outputs (head + tail preserved)
Layer 3 — Replace repeated file contents with delta references
"""
from anthropic import Anthropic

MAX_TOOL_CHARS   = 4000
KEEP_RECENT_TURNS = 6
HEAD_TAIL_CHARS   = 1500


def _truncate_output(text: str, limit: int = MAX_TOOL_CHARS) -> str:
    """Layer 2: keep head and tail when a tool result exceeds the limit."""
    if len(text) <= limit:
        return text
    half = HEAD_TAIL_CHARS
    omitted = len(text) - (half * 2)
    return (
        text[:half]
        + f"\n\n[... truncated {omitted} characters ...]\n\n"
        + text[-half:]
    )


def _compress_tool_results(content: list | str) -> list | str:
    """Apply Layer 2 truncation to tool_result blocks."""
    if not isinstance(content, list):
        return content
    out = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            block = {**block, "content": _truncate_output(str(block.get("content", "")))}
        out.append(block)
    return out


def _summarize_old_turns(messages: list[dict], client: Anthropic) -> list[dict]:
    """Layer 1: replace the oldest user/assistant pair with a summary."""
    if len(messages) <= KEEP_RECENT_TURNS + 2:
        return messages

    old = messages[:2]
    rest = messages[2:]

    summary_prompt = (
        "Summarize this conversation excerpt in 3-5 bullet points. "
        "Preserve task goals, decisions, and file paths mentioned.\n\n"
        + str(old)
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": summary_prompt}],
    )
    summary_text = next(
        (b.text for b in response.content if hasattr(b, "text")),
        "(summary unavailable)",
    )
    return [
        {"role": "user", "content": f"[COMPRESSED HISTORY]\n{summary_text}"},
        *rest,
    ]


def compress_messages(messages: list[dict], client: Anthropic) -> list[dict]:
    """
    Apply all three compression layers to a message list.
    Layer 3 (delta references) is applied inline: identical consecutive
    read_file outputs are replaced with a pointer to the earlier version.
    """
    compressed = []
    seen_reads: dict[str, str] = {}

    for msg in messages:
        msg = {**msg}
        msg["content"] = _compress_tool_results(msg.get("content", ""))

        # Layer 3: deduplicate repeated file reads in tool results
        if isinstance(msg["content"], list):
            new_blocks = []
            for block in msg["content"]:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    new_blocks.append(block)
                    continue
                text = str(block.get("content", ""))
                if text in seen_reads:
                    block = {
                        **block,
                        "content": f"[unchanged since earlier read — see turn referencing {seen_reads[text]}]",
                    }
                else:
                    seen_reads[text] = block.get("tool_use_id", "prior")
                new_blocks.append(block)
            msg["content"] = new_blocks

        compressed.append(msg)

    return _summarize_old_turns(compressed, client)
