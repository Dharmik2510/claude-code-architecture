"""Pattern 6 — three-layer context compression (no API call needed)."""
import compressor as c


def test_truncate_keeps_head_and_tail():
    text = "A" * 100 + "B" * 5000 + "Z" * 100
    out = c._truncate_output(text)
    assert out.startswith("A")
    assert out.endswith("Z")
    assert "truncated" in out
    assert len(out) < len(text)


def test_short_output_is_untouched():
    text = "small output"
    assert c._truncate_output(text) == text


def test_tool_results_over_limit_are_truncated():
    big = "x" * 9000
    content = [{"type": "tool_result", "tool_use_id": "t1", "content": big}]
    out = c._compress_tool_results(content)
    assert "truncated" in out[0]["content"]


def test_duplicate_reads_are_deduplicated():
    # Two messages with the same tool_result content -> second becomes a pointer.
    dup = "file contents that repeat"
    messages = [
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": dup}]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t2", "content": dup}]},
    ]
    # Short list -> _summarize_old_turns returns early, so client is never used.
    out = c.compress_messages(messages, client=None)
    assert dup in str(out[0]["content"][0]["content"])
    assert "unchanged since earlier read" in out[1]["content"][0]["content"]
