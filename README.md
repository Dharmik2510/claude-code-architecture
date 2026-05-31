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

## Verified Context: Why Claude Code Matters

Public reporting (not audited financial statements) describes Claude Code's growth after its public launch in **May 2025**:

| Milestone | Reported figure | Source |
|---|---|---|
| ~6 months post-launch | **$1B annualized run-rate revenue** | [VentureBeat](https://venturebeat.com/technology/anthropic-says-it-hit-a-30-billion-revenue-run-rate-after-crazy-80x-growth), [SaaStr](https://www.saastr.com/anthropic-just-hit-14-billion-in-arr-up-from-1-billion-just-14-months-ago/) |
| February 2026 | **$2.5B+ annualized run-rate** for Claude Code specifically | [SaaStr](https://www.saastr.com/anthropic-just-hit-14-billion-in-arr-up-from-1-billion-just-14-months-ago/) |

**Important caveats (read these):**
- *Annualized run-rate* extrapolates recent performance over a full year — it is not the same as audited annual revenue.
- Anthropic has stated that Claude Code drives a large share of company growth, but exact product-level breakdowns come from press reporting, not public filings.
- This repository teaches the *engineering patterns* behind such products. It does not reproduce Anthropic's business results.

What *is* documented by Anthropic directly: Claude Code is an agentic tool that reads codebases, edits files, runs commands, supports [MCP integrations](https://docs.anthropic.com/en/docs/claude-code/mcp), uses project-level instructions (`CLAUDE.md`), supports [agent teams](https://docs.anthropic.com/en/docs/claude-code/overview), and exposes an [Agent SDK](https://docs.anthropic.com/en/docs/claude-code/overview). This curriculum is organized around those publicly described capabilities.

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

Each phase is self-contained. Phase 1 alone is a functional coding agent. Phase 6 wires everything together in `combined_agent.py`.

---

## For Non-Developers — The Idea in Plain Language

Imagine a skilled assistant that can:

- Read and edit files on your computer
- Run programs and verify they work
- Break large tasks into steps and track progress
- Delegate subtasks to specialized helpers working in parallel
- Undo mistakes and follow rules you define in advance

This repository shows *how software engineers build that kind of assistant* — not with magic, but with a loop, tools, and careful engineering around memory, safety, and coordination.

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

pip install anthropic aiofiles pyyaml redis

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
├── docs/
│   └── PATTERN_MAP.md        # Pattern → code → Anthropic doc links
│
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

## Requirements

| Dependency | Phases | Notes |
|---|---|---|
| Python 3.11+ | All | |
| [Anthropic API key](https://console.anthropic.com/) | 1–5 | Required for model calls |
| Redis 7+ | 6 | Optional; `docker run -p 6379:6379 redis` |
| Git 2.20+ | 3, 6, examples | Required for worktree patterns |

```bash
pip install anthropic aiofiles pyyaml redis
```

---

## Common Questions

**Do I need all 23 patterns?**  
No. Phase 1 is a working agent. Add phases as your use case requires them.

**Does this only work with Claude?**  
The patterns are model-agnostic. This repo uses Anthropic's tool-calling API; other models with tool support need adapter changes.

**Is it safe on a real codebase?**  
With Phase 4 (snapshots + YAML permissions), writes are reversible and tool calls are policy-governed. Earlier phases should be treated as learning sandboxes.

**How much does a task cost?**  
Cost depends on model, task length, and whether prompt caching is enabled. Run your own tasks and inspect `response.usage` — this repo does not publish cost guarantees.

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
