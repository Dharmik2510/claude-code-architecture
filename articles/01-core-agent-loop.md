# Article 1: The Core Agent Loop That Powers Agentic Coding

**Phase 1 · Patterns 1–4 · ~15 min read**

[← Back to README](../README.md) · [Pattern Map](../docs/PATTERN_MAP.md) · [Next: Article 2 →](./02-knowledge-context.md)

---

## What you'll learn

- How Anthropic's public docs describe the **agentic tool-use loop**
- How to implement that loop in ~80 lines of Python
- Three patterns that make the loop practical: tool dispatch, planning, and subagents

---

## What Anthropic documents publicly

Anthropic's [Tool use overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) describes **client tools**: Claude returns `stop_reason: "tool_use"` with one or more `tool_use` blocks. Your application executes the operation and sends back `tool_result` blocks. The model then continues.

That cycle — call model → execute tools → feed results back — is the foundation of Claude Code and every similar coding agent. Anthropic does not publish Claude Code's internal source, but this loop is documented API behavior you can implement yourself.

---

## Pattern 1: The minimal while loop

**File:** `phase1_core_loop/agent.py`

The entire agent is a `while True` loop with three steps:

1. Call the Messages API with tools and conversation history
2. If `stop_reason == "end_turn"`, return — the task is done
3. Otherwise, execute each `tool_use` block and append results to messages

```python
while True:
    response = client.messages.create(
        model=MODEL, max_tokens=8096,
        system=SYSTEM_PROMPT, tools=ALL_TOOLS, messages=messages,
    )
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        return final_text

    tool_results = []
    for block in response.content:
        if block.type != "tool_use":
            continue
        result = ALL_HANDLERS[block.name](block.input)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(result),
        })
    messages.append({"role": "user", "content": tool_results})
```

**Why this works:** The model decides *what* to do. Your harness decides *how* to execute it safely. The loop repeats until the model has enough information to answer.

---

## Pattern 2: Tool dispatch map

**File:** `phase1_core_loop/tools.py`

Instead of a long `if/elif` chain, tools are registered in two parallel structures:

- `TOOL_SCHEMAS` — JSON schemas sent to the API (what the model sees)
- `TOOL_HANDLERS` — Python functions keyed by tool name (what your code runs)

```python
TOOL_HANDLERS = {
    "read_file":  tool_read_file,
    "write_file": tool_write_file,
    "run_shell":  tool_run_shell,
}
```

Adding a new tool means adding one schema entry and one handler. The agent loop never changes.

This matches Anthropic's tool-use model: you define tools, the model chooses among them.

---

## Pattern 3: TodoWrite planning

**File:** `phase1_core_loop/todo_tools.py`

Complex tasks fail when the model loses track of progress. The TodoWrite pattern gives the model structured planning tools:

- `todo_write` — create an ordered list of steps before starting
- `todo_update` — mark steps `in_progress`, `completed`, or `failed`

The system prompt in `agent.py` instructs the model to plan first. The todo state lives in a JSON file on disk, so it survives within a session even if the model's attention drifts.

This is a general agent-engineering pattern — not unique to Anthropic — but it mirrors how production agents keep multi-step work organized.

---

## Pattern 4: Subagent isolation

**File:** `phase1_core_loop/subagent.py`

When a parent agent delegates a subtask, running it in the *same* message history wastes tokens on intermediate tool noise. A subagent runs in a **fresh context** and returns only a summary:

```python
def run_subagent(subtask: str, max_turns: int = 10) -> str:
    messages = [{"role": "user", "content": subtask}]
    # ... same loop, separate messages list ...
    return summary_text  # parent sees only this
```

Anthropic's [Claude Code overview](https://docs.anthropic.com/en/docs/claude-code/overview) documents **agent teams** and delegation at the product level. Subagent isolation is the harness primitive that makes delegation cost-efficient.

---

## Try it yourself

```bash
export ANTHROPIC_API_KEY=your-key
python phase1_core_loop/agent.py
python phase1_core_loop/subagent.py
```

The default task lists Python files, reads one, and writes a summary to `summary.txt`.

---

## Key takeaway

> The model is the planner. The loop is the executor. Tools are the hands.

Everything in Phases 2–6 builds on this loop — adding memory, teams, safety, speed, and scale without replacing the core cycle.

**Next:** [Article 2 — Stop Bloating Your System Prompt →](./02-knowledge-context.md)
