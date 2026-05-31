<div align="center">

# Claude Code Architecture

### Learn the engineering patterns behind a production AI coding agent — by building each one yourself

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Anthropic SDK](https://img.shields.io/badge/anthropic--sdk-latest-orange)](https://github.com/anthropic/anthropic-sdk-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Patterns](https://img.shields.io/badge/patterns-23%20runnable-purple.svg)](#-the-23-patterns)

**6-part article series · 23 patterns · One Python file per pattern · [Pattern map](docs/PATTERN_MAP.md)**

[What This Is (and Isn't)](#-what-this-is-and-isnt) · [Article Series](#-article-series) · [Quick Start](#-quick-start) · [Pattern Map](docs/PATTERN_MAP.md) · [Patterns](#-the-23-patterns)

</div>

---

## What This Is (and Isn't)

**This is:** An open-source, educational reimplementation of the *architectural patterns* that make agentic coding tools work — written in plain Python, one concept per file, with runnable demos.

**This is not:** The Claude Code source code. Anthropic has not published Claude Code's internal implementation. Nothing in this repository claims to be a copy of proprietary software.

**How it was built:** Each pattern maps to something Anthropic documents publicly (product docs, API references, MCP specification) or to a well-known agent-engineering technique (tool dispatch, while-loops, Git worktrees). Every file in this repo is labeled with its pattern number and can be run independently.

If you want to understand *why* Claude Code feels different from a chatbot with file access — and how to build that difference yourself — start at Phase 1.

---

## Why These Patterns Matter

Agentic coding tools moved from demo to daily-driver fast — and the gap between "chatbot that can edit files" and "agent you trust on a real codebase" is almost entirely *engineering*: the loop, the safety rails, the coordination, the cost controls. This repo teaches that engineering.

What's documented by Anthropic directly: Claude Code reads codebases, edits files, runs commands, supports [MCP integrations](https://docs.anthropic.com/en/docs/claude-code/mcp), uses project-level instructions (`CLAUDE.md`), supports [agent teams](https://docs.anthropic.com/en/docs/claude-code/overview), and exposes an [Agent SDK](https://docs.anthropic.com/en/docs/claude-code/overview). This curriculum is organized around those publicly described capabilities. (Press has reported strong revenue for the product; those are run-rate estimates from reporting, not audited figures, and aren't what this repo is about.)

---

## For Developers — What You'll Build

Six phases, each adding one layer of capability:

```
Phase 1  →  Core agent loop (while True → model → tools → repeat)
Phase 2  →  Context management (skills, compression, task graphs)
Phase 3  →  Multi-agent coordination (mailboxes, worktrees, background tasks)
Phase 4  →  Production hardening (snapshots, permissions, streaming, sessions)
Phase 5  →  Performance (async parallelism, caching, interrupts, MCP)
Phase 6  →  Enterprise scale (Redis mailboxes, worktree lifecycle)
```

Each phase is self-contained. Phase 1 alone is a functional coding agent. `phase6_enterprise/combined_agent.py` invokes **all 23 patterns** and prints a coverage report — degrading gracefully (offline patterns always run; Git, Redis, and model-dependent patterns run when their prerequisites are present, and anything skipped is reported with the reason).

### The Minimum Production Baseline

The phases read like optional upgrades, but they aren't all optional. **If you put an agent anywhere near a real codebase, this is the non-negotiable floor:**

| Need | Pattern | File |
|---|---|---|
| The loop | 1–2 (loop + tool dispatch) | `phase1_core_loop/` |
| **Undo** — every write reversible | 14 (snapshots) | `phase4_production/snapshots.py` |
| **Guardrails** — deny dangerous calls | 15 (YAML permissions) | `phase4_production/permissions.py` |
| **Resilience** — survive rate limits / drops | `with_retry()` | [`config.py`](config.py) |
| **Cost visibility** — tokens per turn | `log_usage()` | [`config.py`](config.py) |
| **Resume** — crash-safe history | 17 (sessions) | `phase4_production/session_store.py` |

`phase6_enterprise/combined_agent.py` runs with all of these on. Everything else (multi-agent teams, async, Redis) is scale-up you add when the workload demands it. **Phases 1–3 on their own are learning sandboxes — don't point them at code you can't afford to lose.**

---

## For Non-Developers — The Idea in Plain Language

Imagine a skilled assistant that can:

- Read and edit files on your computer
- Run programs and verify they work
- Break large tasks into steps and track progress
- Delegate subtasks to specialized helpers working in parallel
- Undo mistakes and follow rules you define in advance

This repository shows *how software engineers build that kind of assistant* — not with magic, but with a loop, tools, and careful engineering around memory, safety, and coordination.

**Each phase, in one sentence:**

| Phase | Plain-language analogy |
|---|---|
| 1 — Core loop | A worker who reads the task, picks a tool, uses it, checks the result, and repeats until done. |
| 2 — Context | A worker with a notepad: they summarize old notes so they never run out of room, and only pull out the manuals they actually need. |
| 3 — Multi-agent | A project manager handing tasks to a team — each member works in their *own copy* of the office so nobody overwrites anyone else, and they leave notes in each other's mailboxes. |
| 4 — Production | Safety rails: every change can be undone, dangerous actions are blocked by written rules, and the work is saved so a crash doesn't lose progress. |
| 5 — Performance | Doing independent steps at the same time instead of one-by-one, and not re-reading the same manual every time (caching) to save money. |
| 6 — Enterprise | The same team, but spread across many machines, coordinating over a shared message bus. |

<details>
<summary><strong>Glossary (click to expand)</strong> — eight terms that unlock the rest of this repo</summary>

- **Agent** — a program that loops: think → use a tool → look at the result → repeat, until the task is done.
- **Tool** — a single capability the agent can invoke (read a file, run a command, write a file). The model *asks*; your code *does*.
- **Context window** — the model's short-term memory. It's finite, so long sessions must be compressed (Phase 2).
- **Token** — the unit models read and bill by (roughly ¾ of a word). Fewer tokens = lower cost.
- **Prompt caching** — reusing the unchanged parts of a request so you don't pay full price to re-send them every turn.
- **MCP (Model Context Protocol)** — a standard way to plug external tools into an agent without changing its code.
- **Worktree** — a Git feature that gives each agent its own working copy of the project, so parallel edits don't collide.
- **Subagent** — a fresh helper agent spun up for one focused subtask, with its own clean memory.

</details>

---

## Article Series

Six self-contained articles — read in order or jump to what you need. Each links to runnable code and, where applicable, Anthropic's public documentation.

| # | Article | Patterns | What you'll build |
|---|---|---|---|
| 1 | [The Core Agent Loop](articles/01-core-agent-loop.md) | 1–4 | While-loop agent, tools, planning, subagents |
| 2 | [Stop Bloating Your System Prompt](articles/02-knowledge-context.md) | 5–7 | Skills, compression, task dependency graph |
| 3 | [How Multi-Agent Teams Coordinate](articles/03-multi-agent-teams.md) | 8–12 | Background tasks, mailboxes, FSM, worktrees |
| 4 | [From Prototype to Production](articles/04-production-hardening.md) | 13–17 | Streaming, snapshots, permissions, sessions |
| 5 | [Async Performance and MCP](articles/05-async-performance.md) | 18–21 | Parallel tools, interrupts, caching, MCP |
| 6 | [Enterprise-Grade Agent Fleets](articles/06-enterprise.md) | 22–23 | Redis mailboxes, worktree lifecycle, full assembly |

**Visual reference:** [docs/PATTERN_MAP.md](docs/PATTERN_MAP.md) — diagram mapping all 23 patterns to code files and official Anthropic/MCP docs.

---

## Quick Start

```bash
git clone https://github.com/dhsoni2510/claude-code-architecture
cd claude-code-architecture

python -m venv .venv && source .venv/bin/activate
pip install -e .            # core deps, pinned in pyproject.toml
# pip install -e ".[redis]"  # add Phase 6 Redis support
# pip install -e ".[dev]"    # add pytest to run the test suite

cp .env.example .env        # then put your key in .env
export ANTHROPIC_API_KEY=your-key-here
# https://console.anthropic.com/

python phase1_core_loop/agent.py
```

The agent lists Python files, reads one, and writes a summary to `summary.txt`.

**Run any pattern in isolation:**

```bash
python phase1_core_loop/subagent.py          # Pattern 4
python phase2_context_management/compressor.py # Pattern 6 (importable module)
python phase4_production/streaming_agent.py    # Pattern 13
python phase5_async_runtime/caching.py         # Pattern 20
python phase6_enterprise/redis_mailbox.py      # Pattern 22 (needs Redis)
```

**End-to-end examples:**

```bash
python examples/run_code_review.py path/to/file.py
python examples/run_feature_build.py
python examples/run_refactor.py   # Git repo required; uses worktrees
```

---

## Repository Structure

Every pattern has exactly one primary file. If a file is listed here, it exists in the repo.

```
claude-code-architecture/
│
├── phase1_core_loop/
│   ├── agent.py              # Pattern 1 — minimal while-loop agent
│   ├── tools.py              # Pattern 2 — tool dispatch map
│   ├── todo_tools.py         # Pattern 3 — TodoWrite planning
│   └── subagent.py           # Pattern 4 — context-isolated subagent
│
├── phase2_context_management/
│   ├── skill_loader.py       # Pattern 5 — on-demand skill loading
│   ├── compressor.py         # Pattern 6 — three-layer context compression
│   ├── task_graph.py         # Pattern 7 — file-based dependency graph
│   └── skills/
│       ├── code_review.txt
│       ├── security_audit.txt
│       └── documentation.txt
│
├── phase3_multi_agent/
│   ├── background_tasks.py   # Pattern 8 — background execution + notifications
│   ├── mailbox.py            # Pattern 9 — JSONL agent mailboxes
│   ├── fsm_protocol.py       # Pattern 10 — FSM communication protocol
│   ├── self_assignment.py    # Pattern 11 — pull-based task claiming
│   └── worktree.py           # Pattern 12 — Git worktree isolation
│
├── phase4_production/
│   ├── streaming_agent.py    # Pattern 13 — real-time token streaming
│   ├── snapshots.py          # Pattern 14 — reversible file writes
│   ├── permissions.py        # Pattern 15 — YAML permission governance
│   ├── event_bus.py          # Pattern 16 — lifecycle event bus
│   ├── session_store.py      # Pattern 17 — session persistence + fork
│   └── permissions.yaml
│
├── phase5_async_runtime/
│   ├── async_agent.py        # Pattern 18 — parallel tool execution
│   ├── interrupt.py          # Pattern 19 — real-time interrupt injection
│   ├── caching.py            # Pattern 20 — prompt cache configuration
│   └── mcp_registry.py       # Pattern 21 — MCP tool registry
│
├── phase6_enterprise/
│   ├── redis_mailbox.py      # Pattern 22 — Redis Streams mailboxes
│   ├── worktree_lifecycle.py # Pattern 23 — worktree lifecycle manager
│   └── combined_agent.py     # All patterns wired together
│
├── examples/
│   ├── run_code_review.py
│   ├── run_feature_build.py
│   └── run_refactor.py
│
├── articles/                 # 6-part educational article series
│   ├── 01-core-agent-loop.md
│   ├── 02-knowledge-context.md
│   ├── 03-multi-agent-teams.md
│   ├── 04-production-hardening.md
│   ├── 05-async-performance.md
│   └── 06-enterprise.md
│
├── tests/                    # offline pytest suite (no API key needed)
│   ├── test_task_graph.py    # Pattern 7
│   ├── test_compressor.py    # Pattern 6
│   ├── test_fsm.py           # Pattern 10
│   ├── test_permissions.py   # Pattern 15
│   ├── test_snapshots.py     # Pattern 14
│   ├── test_mailbox.py       # Pattern 9
│   ├── test_tools.py         # Pattern 2
│   └── test_config.py        # resilience helpers
│
├── docs/
│   └── PATTERN_MAP.md        # Pattern → code → Anthropic doc links
│
├── config.py                 # shared model/retry/cost helpers (production baseline)
├── pyproject.toml            # pinned deps + pytest config
├── .env.example              # copy to .env, add your key
├── LICENSE
└── README.md
```

---

## Code Walkthrough

### Phase 1 — The Core Loop

The entire foundation is a `while True` loop: call the model, check if done, execute tools, repeat.

```python
# phase1_core_loop/agent.py
while True:
    response = client.messages.create(model=MODEL, tools=tools, messages=messages)
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        return

    tool_results = [dispatch(block) for block in response.content if block.type == "tool_use"]
    messages.append({"role": "user", "content": tool_results})
```

The model decides. The harness executes. Results feed back. Repeat until done.

### Phase 2 — Context That Scales

Long sessions hit context limits. The compressor applies three layers:

```python
# phase2_context_management/compressor.py
# Layer 1: Summarize old conversation clusters
# Layer 2: Truncate oversized tool outputs (head + tail)
# Layer 3: Replace duplicate file reads with delta references
messages = compress_messages(messages, client)
```

Skills load domain knowledge only when needed — the same idea behind Claude Code's [skills](https://docs.anthropic.com/en/docs/claude-code/overview) and project instruction files.

### Phase 3 — Agent Teams

Specialists run in parallel, each in an isolated Git worktree, communicating through mailboxes:

```python
# phase3_multi_agent/background_tasks.py
run_background_task("security-audit", "Check auth.py for vulnerabilities", tools, handlers)

for result in check_notifications():
    print(f"Background task '{result['task_id']}' done")
```

Anthropic documents [agent teams and background agents](https://docs.anthropic.com/en/docs/claude-code/overview) as first-class Claude Code features. This phase shows the coordination primitives those features require underneath.

### Phase 4 — Production Safety

Every file write can be reversed. Every tool call is governed by YAML policy. Actions emit events for observability:

```python
# phase4_production/snapshots.py
snapshot_before_write(args["path"])
Path(args["path"]).write_text(args["content"])
# → revert_file() undoes the write at any time
```

### Phase 5 — Speed and Extensibility

Tool calls in one model turn run concurrently. Stable context is cached. MCP servers extend the tool set without code changes:

```python
# phase5_async_runtime/async_agent.py
tool_results = await asyncio.gather(*[execute_tool(block) for block in tool_blocks])

# phase5_async_runtime/caching.py — uses Anthropic prompt caching API
# phase5_async_runtime/mcp_registry.py — loads tools from MCP exports
```

Anthropic's [prompt caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) describe the cost mechanism. Exact savings depend on your workload — this repo shows *how* to enable caching, not a guaranteed percentage.

### Phase 6 — Distributed Scale

Redis Streams replace local JSONL mailboxes when agents run across machines:

```python
# phase6_enterprise/redis_mailbox.py
await mailbox.send(to_agent="reviewer", from_agent="coordinator",
                   message={"type": "review_request", "file": "auth.py"})
```

---

## The 23 Patterns

Each row links a pattern to its implementation file and the problem it solves. "Public doc" indicates where Anthropic describes related product behavior.

| # | Pattern | File | Problem it solves | Public doc reference |
|---|---|---|---|---|
| 1 | Minimal while loop | `phase1_core_loop/agent.py` | Reasoning–execution cycle | Agent SDK / tool use |
| 2 | Tool dispatch map | `phase1_core_loop/tools.py` | Extensible tool routing | Tool use API |
| 3 | TodoWrite planning | `phase1_core_loop/todo_tools.py` | Structured multi-step plans | — |
| 4 | Subagent isolation | `phase1_core_loop/subagent.py` | Focused subtasks, smaller context | Agent teams |
| 5 | On-demand skill loading | `phase2_context_management/skill_loader.py` | Lean system prompts | Skills / CLAUDE.md |
| 6 | Context compression | `phase2_context_management/compressor.py` | Long sessions within limits | — |
| 7 | Task dependency graph | `phase2_context_management/task_graph.py` | Durable task state on disk | — |
| 8 | Background tasks | `phase3_multi_agent/background_tasks.py` | Non-blocking subtasks | Background agents |
| 9 | JSONL mailboxes | `phase3_multi_agent/mailbox.py` | Persistent agent messaging | — |
| 10 | FSM protocol | `phase3_multi_agent/fsm_protocol.py` | Structured state transitions | — |
| 11 | Self-assignment | `phase3_multi_agent/self_assignment.py` | Pull-based work claiming | Agent teams |
| 12 | Git worktree isolation | `phase3_multi_agent/worktree.py` | Parallel edits, no conflicts | — |
| 13 | Real-time streaming | `phase4_production/streaming_agent.py` | Visible model output | Messages streaming API |
| 14 | File snapshots | `phase4_production/snapshots.py` | Reversible writes | — |
| 15 | YAML permissions | `phase4_production/permissions.py` | Declarative tool policy | Permissions / hooks |
| 16 | Event bus | `phase4_production/event_bus.py` | Decoupled observability | Hooks |
| 17 | Session persistence | `phase4_production/session_store.py` | Crash-safe resume + fork | Session continuity |
| 18 | Parallel tool execution | `phase5_async_runtime/async_agent.py` | Faster multi-tool turns | — |
| 19 | Interrupt injection | `phase5_async_runtime/interrupt.py` | Mid-run user redirection | — |
| 20 | Prompt caching | `phase5_async_runtime/caching.py` | Lower cost for stable context | Prompt caching API |
| 21 | MCP integration | `phase5_async_runtime/mcp_registry.py` | External tool discovery | MCP docs |
| 22 | Redis mailboxes | `phase6_enterprise/redis_mailbox.py` | Cross-machine agent fleets | — |
| 23 | Worktree lifecycle | `phase6_enterprise/worktree_lifecycle.py` | Automated branch cleanup | — |

---

## Testing

The logic-heavy patterns (task graph, compression, FSM, permissions, mailboxes, snapshots, tools, and the `config.py` resilience helpers) are covered by a `pytest` suite that runs **without an API key** — no model calls, fully offline.

```bash
pip install -e ".[dev]"
pytest -q
```

This is what backs the "reversible writes" and "policy-governed calls" claims — the safety behavior is asserted, not just described.

---

## Requirements

| Dependency | Phases | Notes |
|---|---|---|
| Python 3.11+ | All | |
| [Anthropic API key](https://console.anthropic.com/) | 1–5 | Required for model calls |
| Redis 7+ | 6 | Optional; `docker run -p 6379:6379 redis` |
| Git 2.20+ | 3, 6, examples | Required for worktree patterns |

Dependencies are pinned in [`pyproject.toml`](pyproject.toml); install with `pip install -e .` (add `[redis]` or `[dev]` extras as needed).

---

## Common Questions

**Do I need all 23 patterns?**  
No. Phase 1 is a working agent. Add phases as your use case requires them.

**Does this only work with Claude?**  
The patterns are model-agnostic. This repo uses Anthropic's tool-calling API; other models with tool support need adapter changes.

**Is it safe on a real codebase?**  
With the [Minimum Production Baseline](#the-minimum-production-baseline) on (snapshots + YAML permissions + retries), writes are reversible and tool calls are policy-governed — and that behavior is covered by the test suite, not just asserted in prose. Earlier phases on their own should be treated as learning sandboxes.

**How much does a task cost?**  
Cost depends on model, task length, and whether prompt caching is enabled. `config.log_usage()` prints input/output/cache tokens per turn (wired into `combined_agent.py`) so you can measure your own workload — this repo does not publish cost guarantees.

---

## Further Reading

**In this repo:**
- [Pattern Map](docs/PATTERN_MAP.md) — all 23 patterns with code paths and doc links
- [Article Series](articles/01-core-agent-loop.md) — start at Article 1

**Official Anthropic documentation:**
- [Claude Code overview](https://docs.anthropic.com/en/docs/claude-code/overview)
- [Tool use / agentic loop](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Model Context Protocol](https://modelcontextprotocol.io)

---

## Contributing

- **Bug fixes** — open an issue with a minimal reproduction
- **New examples** — add a runnable script to `examples/`
- **Accuracy corrections** — if a claim here doesn't match the code or a public source, please open an issue with the reference

Keep examples self-contained. Phase 6 Redis examples may require a running Redis instance.

---

<div align="center">

**Built by [Dharmik Soni](https://github.com/dhsoni2510)**

*Educational reimplementation based on publicly documented agent-engineering patterns — not Anthropic proprietary code.*

</div>
