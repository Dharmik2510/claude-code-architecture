<div align="center">

# 🤖 Claude Code Architecture

### The 23 Engineering Patterns Behind a $1B AI Coding Agent — Fully Reproduced

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Anthropic SDK](https://img.shields.io/badge/anthropic--sdk-latest-orange)](https://github.com/anthropic/anthropic-sdk-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/dhsoni2510/claude-code-architecture?style=social)](https://github.com/dhsoni2510/claude-code-architecture)

**6-part article series · 23 patterns · Runnable code for every concept**

[Quick Start](#-quick-start) · [What You'll Learn](#-what-youll-learn) · [Article Series](#-article-series) · [Code Walkthrough](#-code-walkthrough) · [Contributing](#-contributing)

</div>

---

## 🌟 Why This Repository Exists

Claude Code crossed **$1 billion in annualized revenue** six months after launch. The reason isn't a secret model or a proprietary framework. It's a specific set of engineering decisions around how an AI model is wrapped, constrained, and given tools.

This repository reproduces every one of those decisions from scratch — 23 patterns across 6 architectural layers — with real, runnable Python code and plain-English explanations for every line.

**You don't need to be an AI researcher to benefit from this.** If you're a developer who has ever wanted to build an AI agent that actually works in production, this is the engineering blueprint.

---

## 🧑‍💻 For Developers — What This Is

A step-by-step implementation of Claude Code's architecture, organized by complexity:

```
Phase 1  →  A minimal agent that runs in a while loop
Phase 2  →  An agent that manages its own memory and knowledge
Phase 3  →  A team of agents that work in parallel
Phase 4  →  A production-grade agent with audit trails and undo
Phase 5  →  A high-performance agent using async and caching
Phase 6  →  An enterprise agent fleet backed by Redis and Git
```

Each phase builds on the last. You can stop at Phase 1 and already have something more capable than most LLM demos. By Phase 6 you have the architecture of a commercial product.

---

## 🙋 For Non-Developers — What This Actually Does

Imagine you hire a very smart assistant. That assistant can:
- Read and edit files on your computer
- Run programs and check whether they work
- Break a big problem into smaller steps and track their progress
- Bring in specialized helpers when the task needs expertise
- Save progress so nothing is lost if the computer restarts

This repository shows exactly how to build that kind of assistant, and explains why each piece is designed the way it is.

---

## 📚 Article Series

Each article in this series is self-contained. Start anywhere based on what you need.

| # | Title | What You'll Build |
|---|---|---|
| 1 | [The 4-Line Loop That Powers Claude Code](../article-1-core-agent-loop.md) | The core agent loop, tool dispatch, planning |
| 2 | [Stop Bloating Your System Prompt](../article-2-knowledge-context.md) | Skill loading, context compression, task graphs |
| 3 | [How Claude Code Runs a Whole AI Team](../article-3-multi-agent-teams.md) | Multi-agent coordination, mailboxes, Git worktrees |
| 4 | [From Prototype to Production](../article-4-production-hardening.md) | Streaming, snapshots, permissions, event hooks |
| 5 | [Near-Zero Latency with asyncio and Caching](../article-5-async-performance.md) | Async execution, interrupts, prompt caching, MCP |
| 6 | [Enterprise-Grade AI Agents](../article-6-enterprise.md) | Redis mailboxes, worktree lifecycle, full assembly |

---

## ⚡ Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/dhsoni2510/claude-code-architecture
cd claude-code-architecture

# 2. Install dependencies
pip install anthropic aiofiles pyyaml redis

# 3. Set your API key
export ANTHROPIC_API_KEY=your-key-here
# Get one at: https://console.anthropic.com/

# 4. Run the minimal agent (Phase 1)
python phase1_core_loop/agent.py
```

You should see the agent start, write a plan, execute tool calls step by step, and complete the task — all in your terminal.

---

## 📁 Repository Structure

```
claude-code-architecture/
│
├── phase1_core_loop/
│   ├── agent.py              # The minimal while-loop agent
│   ├── tools.py              # Tool implementations + dispatch map
│   ├── todo_tools.py         # TodoWrite planning pattern
│   └── subagent.py           # Context-isolated subagent runner
│
├── phase2_context_management/
│   ├── skill_loader.py       # On-demand skill loading
│   ├── compressor.py         # Three-layer context compression
│   ├── task_graph.py         # File-based dependency graph
│   └── skills/               # Example skill files
│       ├── code_review.txt
│       ├── security_audit.txt
│       └── documentation.txt
│
├── phase3_multi_agent/
│   ├── background_tasks.py   # Background execution + notifications
│   ├── mailbox.py            # JSONL agent mailboxes
│   ├── fsm_protocol.py       # FSM communication protocol
│   ├── self_assignment.py    # Pull-based task claiming
│   └── worktree.py           # Git worktree isolation
│
├── phase4_production/
│   ├── streaming_agent.py    # Real-time token streaming
│   ├── snapshots.py          # File snapshot + revert system
│   ├── permissions.py        # YAML permission governance
│   ├── event_bus.py          # Lifecycle event bus
│   ├── session_store.py      # Session persistence + fork
│   └── permissions.yaml      # Example permission policy
│
├── phase5_async_runtime/
│   ├── async_agent.py        # Parallel tool execution
│   ├── interrupt.py          # Real-time interrupt injection
│   ├── caching.py            # Prompt cache configuration
│   └── mcp_registry.py       # MCP tool registry
│
├── phase6_enterprise/
│   ├── redis_mailbox.py      # Redis Streams mailbox
│   ├── worktree_lifecycle.py # Full worktree lifecycle manager
│   └── combined_agent.py     # All 23 patterns in one entry point
│
├── examples/
│   ├── run_code_review.py    # End-to-end: multi-agent code review
│   ├── run_feature_build.py  # End-to-end: build a feature with tests
│   └── run_refactor.py       # End-to-end: parallel codebase refactor
│
└── README.md
```

---

## 🔍 Code Walkthrough

### Phase 1: The Core Loop (Start Here)

The entire foundation is a `while True` loop with three steps: call the model, check if it's done, execute any tools it requested.

```python
# phase1_core_loop/agent.py
while True:
    response = client.messages.create(model=MODEL, tools=tools, messages=messages)
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        return  # Task complete

    # Execute each tool the model called
    tool_results = [dispatch(block) for block in response.content if block.type == "tool_use"]
    messages.append({"role": "user", "content": tool_results})
```

**Why it works:** The model decides what to do. The harness executes it. The result goes back to the model. Repeat until done.

### Phase 2: Smart Context Management

Every long session eventually runs out of context. The compressor continuously trims old content without losing active state:

```python
# phase2_context_management/compressor.py
# Layer 1: Summarize old conversation clusters
# Layer 2: Truncate giant tool outputs (keep head + tail)  
# Layer 3: Keep only deltas — what changed, not what stayed the same
messages = compress_messages(messages, client)
```

### Phase 3: Agent Teams

Multiple specialists run in parallel, each in an isolated Git worktree, communicating through mailboxes:

```python
# phase3_multi_agent/background_tasks.py
# Spawn a background agent for a subtask
run_background_task("security-audit", "Check auth.py for vulnerabilities", tools, handlers)

# The master agent checks for completions on each turn
for result in check_notifications():
    print(f"Background task '{result['task_id']}' done: {result['result']}")
```

### Phase 4: Production Safety

Every file write is reversible. Every tool call is governed by a YAML policy. Every action is observable through the event bus:

```python
# phase4_production/snapshots.py
def tool_safe_write(args):
    snapshot_before_write(args["path"])   # automatic backup
    Path(args["path"]).write_text(args["content"])
    # → call revert_file() at any point to undo

# phase4_production/permissions.yaml  
rules:
  - tool: run_shell
    command_pattern: "rm|del"
    path_pattern: ".*(prod|production).*"
    action: deny
    reason: "No destructive commands in production paths"
```

### Phase 5: Async Performance

Run all tool calls in a single turn concurrently instead of sequentially:

```python
# phase5_async_runtime/async_agent.py
# OLD: 5 tool calls × 3 seconds each = 15 seconds
# NEW: 5 tool calls running in parallel = 3 seconds

tool_results = await asyncio.gather(
    *[execute_tool(block) for block in tool_blocks]
)
```

### Phase 6: Enterprise Scale

Redis streams replace local file mailboxes for distributed agent fleets:

```python
# phase6_enterprise/redis_mailbox.py
await mailbox.send(to_agent="reviewer", from_agent="coordinator", 
                   message={"type": "review_request", "file": "auth.py"})

# Reviewer picks it up on any machine in the cluster
async for msg_id, envelope in mailbox.receive("reviewer", "worker-1"):
    await process_review(envelope)
    await mailbox.acknowledge("reviewer", msg_id)
```

---

## 🗺️ The 23 Patterns at a Glance

| # | Pattern | Phase | What Problem It Solves |
|---|---|---|---|
| 1 | Minimal while loop | 1 | Gives the model a reasoning-execution cycle |
| 2 | Tool dispatch map | 1 | Extensible tool routing without if/elif chains |
| 3 | TodoWrite planning | 1 | Structured pre-execution plans for complex tasks |
| 4 | Subagent isolation | 1 | Focused, cost-efficient subtask execution |
| 5 | On-demand skill loading | 2 | Lean system prompts that don't waste tokens |
| 6 | Context compression | 2 | Long sessions without hitting the context limit |
| 7 | Task dependency graph | 2 | Task state that survives restarts and context resets |
| 8 | Background tasks | 3 | Non-blocking execution of long-running subtasks |
| 9 | JSONL mailboxes | 3 | Persistent async communication between agents |
| 10 | FSM protocol | 3 | Structured multi-agent state transitions |
| 11 | Autonomous self-assignment | 3 | Agents claim work without a central coordinator |
| 12 | Git worktree isolation | 3 | Parallel agents on the same codebase, no conflicts |
| 13 | Real-time streaming | 4 | Visibility into model reasoning as it happens |
| 14 | File snapshots | 4 | Every write is reversible — no accidental data loss |
| 15 | YAML permissions | 4 | Declarative policy without hard-coded guards |
| 16 | Event bus | 4 | Observability without coupling to tool implementations |
| 17 | Session persistence | 4 | Long-running agents survive crashes and restarts |
| 18 | Parallel tool execution | 5 | 3–10x faster per-turn execution |
| 19 | Interrupt injection | 5 | Real-time user control over running agents |
| 20 | Prompt caching | 5 | 60–90% cost reduction for stable context |
| 21 | MCP integration | 5 | Zero-code tool discovery via open standard |
| 22 | Redis mailboxes | 6 | Distributed agents across multiple machines |
| 23 | Worktree lifecycle | 6 | Automatic cleanup of parallel branches at scale |

---

## 🔗 What You Need

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) (Phases 1–5 only need this)
- Redis 7+ (Phase 6 only — for distributed mailboxes)
- Git 2.20+ (Phase 3+ — for worktree support)

Optional but recommended:
```bash
pip install aiofiles pyyaml redis rich   # async files, YAML, Redis, pretty output
```

---

## 💡 Common Questions

**Q: Do I need all 23 patterns for a useful agent?**  
No. Phase 1 alone gives you a functional coding agent. Add phases as your use case demands them.

**Q: Does this only work with Claude?**  
The patterns are model-agnostic. The tool-calling API shapes are specific to Anthropic's SDK, but the architecture applies to any model that supports tool use (GPT-4, Gemini, etc.) with minor adapter changes.

**Q: Is this safe to run on my actual codebase?**  
By Phase 4 (with snapshots and YAML permissions), yes — every file write is reversible and the agent is constrained by the policy you declare. Before Phase 4, treat it as a sandbox.

**Q: How much does it cost per task?**  
With Phase 5 prompt caching enabled, a medium-complexity task (10–30 tool calls) typically costs $0.02–$0.15 using Claude Sonnet. Without caching, expect 3–5x higher.

---

## 🤝 Contributing

Contributions are welcome:

- **Bug fixes** — open an issue with a minimal repro
- **New examples** — add a runnable script to `examples/`
- **New patterns** — if you've found an architectural pattern that extends Phase 6, open a discussion

Please keep code examples self-contained and runnable without external services (except Phase 6 Redis examples).

---

## 📖 Further Reading

- [Anthropic API documentation](https://docs.anthropic.com)
- [Model Context Protocol (MCP) specification](https://modelcontextprotocol.io)
- [Claude Code documentation](https://docs.anthropic.com/claude-code)

---

## ⭐ If This Helped You

Star the repo. It takes 2 seconds and helps other developers find this when they're searching for "how to build a production AI agent."

Share the article series. Each article is standalone — if one phase is what someone needs, that's enough.

---

<div align="center">

**Built by [Dharmik Soni](https://github.com/dhsoni2510) · Based on analysis of Claude Code's public architecture**

*"The architecture is the moat, not the model."*

</div>
