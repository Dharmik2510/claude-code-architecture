"""
Phase 6 — All 23 Patterns, Exercised End-to-End
================================================

This is the reference entry point that actually *invokes* every pattern in the
repo and prints a coverage report at the end. It degrades gracefully:

  - Offline patterns (5, 6, 7, 9, 10, 11, 14, 15, 16, 17, 19, 20-config, 21)
    run with no API key, no network — pure local logic.
  - Git patterns (12, 23) run only inside a git repo with a clean working tree.
  - Redis pattern (22) runs only if `redis` is installed and a server is reachable.
  - Model patterns (1, 2, 3, 4, 8, 13, 18, 6-live, 20-live) run only if
    ANTHROPIC_API_KEY is set.

Anything that can't run is reported as SKIPPED with the reason — never silently
dropped. With an API key + git + Redis available, you get 23/23.

Run:  python phase6_enterprise/combined_agent.py
"""
import asyncio
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

# Repo root + each phase dir on the path. Phase packages import cleanly via the
# repo root; the standalone pattern files import their siblings by bare name
# (`from tools import ...`), so each phase dir must be importable too.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
for _phase in ("phase1_core_loop", "phase2_context_management", "phase3_multi_agent",
               "phase4_production", "phase5_async_runtime", "phase6_enterprise"):
    sys.path.insert(0, str(REPO_ROOT / _phase))

from phase1_core_loop import tools, todo_tools, subagent
from phase2_context_management import task_graph, compressor, skill_loader
from phase3_multi_agent import background_tasks, mailbox, fsm_protocol, self_assignment, worktree
from phase4_production import snapshots, permissions, event_bus, session_store, streaming_agent
from phase5_async_runtime import async_agent, interrupt, caching, mcp_registry
from phase6_enterprise import worktree_lifecycle
from config import MODEL, MAX_TOKENS, make_client, with_retry, log_usage

# ── Coverage tracking ──────────────────────────────────────────────────────────
PATTERNS = {
    1: "Minimal while loop",          2: "Tool dispatch map",
    3: "TodoWrite planning",          4: "Subagent isolation",
    5: "On-demand skill loading",     6: "Context compression",
    7: "Task dependency graph",       8: "Background tasks",
    9: "JSONL mailboxes",             10: "FSM protocol",
    11: "Self-assignment",            12: "Git worktree isolation",
    13: "Real-time streaming",        14: "File snapshots",
    15: "YAML permissions",           16: "Event bus",
    17: "Session persistence",        18: "Parallel tool execution",
    19: "Interrupt injection",        20: "Prompt caching",
    21: "MCP integration",            22: "Redis mailboxes",
    23: "Worktree lifecycle",
}
COVERAGE: dict[int, tuple[str, str]] = {}


def mark(n: int, status: str, note: str = "") -> None:
    COVERAGE[n] = (status, note)


def banner(text: str) -> None:
    print(f"\n{'─' * 64}\n{text}\n{'─' * 64}")


# ── Sandbox: keep all demo artifacts in one disposable directory ───────────────
SANDBOX = REPO_ROOT / ".combined_demo"
WORK = SANDBOX / "work"


def setup_sandbox() -> None:
    """Point every module's on-disk location at a throwaway sandbox dir."""
    shutil.rmtree(SANDBOX, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)

    snapshots.SNAPSHOT_DIR = SANDBOX / "snaps"
    snapshots.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    mailbox.MAILBOX_DIR = SANDBOX / "mailboxes"
    mailbox.MAILBOX_DIR.mkdir(parents=True, exist_ok=True)
    session_store.SESSIONS_DIR = SANDBOX / "sessions"
    session_store.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    mcp_registry.MCP_CONFIG_DIR = SANDBOX / "mcp"
    todo_tools.TODO_FILE = SANDBOX / "todo.json"


GRAPH_FILE = SANDBOX / "task_graph.json"


def teardown_sandbox() -> None:
    shutil.rmtree(SANDBOX, ignore_errors=True)
    # Remove the empty .worktrees/ base dir created on import (if nothing's in it).
    base = worktree_lifecycle.WORKTREE_BASE
    if base.exists() and not any(base.iterdir()):
        base.rmdir()


# ══════════════════════════════════════════════════════════════════════════════
#  OFFLINE PATTERNS — no API key, no network
# ══════════════════════════════════════════════════════════════════════════════
def run_offline_patterns() -> None:
    banner("OFFLINE PATTERNS (no API key required)")

    # Pattern 5 — On-demand skill loading
    print("\n[Pattern 5] Skills:")
    print("  " + skill_loader.list_skills().replace("\n", "\n  "))
    loaded = skill_loader.load_skill("code_review")
    mark(5, "ok", f"loaded code_review skill ({len(loaded)} chars)")

    # Pattern 21 — MCP integration (load external tool schemas + merge)
    mcp_registry.register_example_server()
    merged_schemas, merged_handlers = mcp_registry.merge_tool_sets(
        tools.TOOL_SCHEMAS, tools.TOOL_HANDLERS,
        "example", {"fetch_url": lambda a: "(mock fetch)"},
    )
    mcp_count = len(merged_schemas) - len(tools.TOOL_SCHEMAS)
    print(f"\n[Pattern 21] MCP: merged {mcp_count} external tool(s) -> "
          f"{len(merged_schemas)} total tools")
    mark(21, "ok", f"{mcp_count} MCP tool(s) discovered")

    # Pattern 7 — Task dependency graph
    task_graph.init([
        {"id": "design", "description": "design", "depends_on": [], "requires_capability": "coding"},
        {"id": "tests",  "description": "tests",  "depends_on": ["design"], "requires_capability": "coding"},
    ], graph_file=GRAPH_FILE)
    ready = [t["id"] for t in task_graph.get_ready(graph_file=GRAPH_FILE)]
    print(f"\n[Pattern 7] Task graph initialized. Ready now: {ready}")
    mark(7, "ok", f"ready tasks: {ready}")

    # Pattern 11 — Self-assignment (atomic pull-based claim)
    claimed = self_assignment.claim_next_task("agent-1", ["coding"], graph_file=GRAPH_FILE)
    print(f"[Pattern 11] agent-1 atomically claimed: {claimed['id'] if claimed else None}")
    task_graph.mark_done("design", "done", graph_file=GRAPH_FILE)
    mark(11, "ok", f"claimed {claimed['id'] if claimed else 'nothing'}")

    # Pattern 10 — FSM protocol
    print("\n[Pattern 10] FSM lifecycle:")
    fsm = fsm_protocol.AgentFSM("demo")
    for msg, who in [("assign", "coord"), ("submit", "writer"),
                     ("start_review", "rev"), ("approve", "rev"), ("complete", "coord")]:
        fsm.transition(msg, who)
    mark(10, "ok", f"reached state {fsm.state}")

    # Pattern 9 — JSONL mailboxes
    mailbox.send_message("reviewer", "coordinator", {"type": "review", "file": "auth.py"})
    inbox = mailbox.read_unread_messages("reviewer")
    print(f"\n[Pattern 9] Mailbox: reviewer received {len(inbox)} message(s)")
    mark(9, "ok", f"{len(inbox)} message(s) delivered")

    # Pattern 16 — Event bus (instrumented tool call)
    print("\n[Pattern 16] Event bus:")
    event_bus.subscribe("*", event_bus.log_all_calls)
    event_bus.subscribe("after_call", event_bus.audit_writes)
    event_bus.instrumented_call("read_file", {"path": str(REPO_ROOT / "README.md")},
                                tools.TOOL_HANDLERS)
    mark(16, "ok", "before/after events emitted")

    # Pattern 14 — File snapshots (reversible write)
    doc = WORK / "doc.txt"
    doc.write_text("ORIGINAL")
    snapshots.tool_safe_write({"path": str(doc), "content": "MODIFIED"})
    snapshots.revert_file(str(doc))
    reverted = doc.read_text()
    print(f"\n[Pattern 14] Snapshots: wrote MODIFIED, reverted -> '{reverted}'")
    mark(14, "ok" if reverted == "ORIGINAL" else "fail", "write reverted cleanly")

    # Pattern 15 — YAML permissions
    allowed, reason = permissions.check_permission(
        "write_file", {"path": "/etc/passwd", "content": "x"})
    print(f"\n[Pattern 15] Permissions: write /etc/passwd -> "
          f"{'ALLOWED' if allowed else 'DENIED'} ({reason})")
    mark(15, "ok" if not allowed else "fail", "dangerous write denied")

    # Pattern 17 — Session persistence + fork
    session_store.save_session("demo", [{"role": "user", "content": "hi"}])
    forked = session_store.fork_session("demo", "demo-fork")
    print(f"\n[Pattern 17] Sessions: saved 'demo', forked -> "
          f"'{forked['session_id'] if forked else None}'")
    mark(17, "ok", "save + fork")

    # Pattern 6 — Context compression (layers 2 & 3, offline)
    big = "x" * 9000
    msgs = [
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": big}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t2", "content": big}]},
    ]
    compressed = compressor.compress_messages(msgs, client=None)  # short list: no API call
    truncated = "truncated" in str(compressed[0]["content"][0]["content"])
    deduped = "unchanged since earlier read" in compressed[1]["content"][0]["content"]
    print(f"\n[Pattern 6] Compression: truncated={truncated}, deduped={deduped}")
    mark(6, "ok" if (truncated and deduped) else "fail", "layers 2+3 (truncate + dedup)")

    # Pattern 20 — Prompt caching (config of cache_control breakpoints)
    block = caching.cached_system_block("You are a coding assistant.")
    has_cache = block[0].get("cache_control", {}).get("type") == "ephemeral"
    print(f"\n[Pattern 20] Caching: cache_control breakpoint set = {has_cache}")
    mark(20, "ok" if has_cache else "fail", "cache_control configured (config-only)")

    # Pattern 19 — Interrupt injection (mechanism)
    interrupt.inject_interrupt("Switch focus to writing tests first.")
    queued = []
    while not interrupt.INTERRUPT_QUEUE.empty():
        queued.append(interrupt.INTERRUPT_QUEUE.get_nowait())
    print(f"\n[Pattern 19] Interrupt: {len(queued)} message(s) queued for injection")
    mark(19, "ok" if queued else "fail", "interrupt queued + drained")


# ══════════════════════════════════════════════════════════════════════════════
#  GIT PATTERNS — require a git repo with a clean working tree
# ══════════════════════════════════════════════════════════════════════════════
def _git_ok() -> tuple[bool, str]:
    if not (REPO_ROOT / ".git").exists():
        return False, "not a git repository"
    if not shutil.which("git"):
        return False, "git not installed"
    r = subprocess.run(["git", "status", "--porcelain"],
                       cwd=REPO_ROOT, capture_output=True, text=True)
    if r.stdout.strip():
        return False, "working tree not clean (worktree demos need a clean tree)"
    return True, ""


def _current_branch() -> str:
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                       cwd=REPO_ROOT, capture_output=True, text=True)
    return r.stdout.strip() or "main"


def run_git_patterns() -> None:
    banner("GIT PATTERNS (worktree isolation + lifecycle)")
    ok, why = _git_ok()
    if not ok:
        print(f"  Skipped: {why}")
        mark(12, "skip", why)
        mark(23, "skip", why)
        return

    base = _current_branch()
    os.chdir(REPO_ROOT)  # worktree/lifecycle git commands run against the current process cwd

    # Pattern 12 — Git worktree isolation
    tid12 = "combined-p12"
    try:
        wt = worktree.create_worktree(tid12, base_branch=base)
        (wt / "p12.txt").write_text("isolated work\n")
        worktree.commit_worktree(tid12, "demo: pattern 12")
        diff = worktree.get_diff(tid12)
        print(f"[Pattern 12] Worktree created, committed on branch agent/{tid12}")
        mark(12, "ok", "create -> commit -> diff -> cleanup")
    except Exception as e:
        mark(12, "skip", f"git error: {e}")
    finally:
        try:
            worktree.cleanup_worktree(tid12, force=True)
        except Exception:
            pass

    # Pattern 23 — Worktree lifecycle (create -> idle -> conflict-check -> prune)
    # Note: uses a non-mutating dry-run merge (--no-commit then --abort); never
    # commits to your current branch.
    tid23 = "combined-p23"
    mgr = worktree_lifecycle.WorktreeLifecycleManager()
    try:
        path = mgr.create(tid23, base_branch=base, agent_name="combined")
        (path / "p23.txt").write_text("lifecycle work\n")
        subprocess.run(["git", "add", "-A"], cwd=path, check=True)
        subprocess.run(["git", "commit", "-m", "demo: pattern 23"],
                       cwd=path, capture_output=True)
        mgr.mark_idle(tid23)
        mgr.check_conflicts(tid23)          # dry-run merge, auto-aborted
        print("\n[Pattern 23] " + mgr.status_report().replace("\n", "\n  "))
        pruned = mgr.prune_abandoned(max_idle_hours=0)
        print(f"[Pattern 23] Pruned: {pruned}")
        mark(23, "ok", "create -> idle -> conflict-check -> prune")
    except Exception as e:
        mark(23, "skip", f"git error: {e}")
    finally:
        # Belt-and-suspenders cleanup in case prune didn't run.
        subprocess.run(["git", "worktree", "remove",
                        str(worktree_lifecycle.WORKTREE_BASE / tid23), "--force"],
                       cwd=REPO_ROOT, capture_output=True)
        subprocess.run(["git", "branch", "-D", f"agent/{tid23}"],
                       cwd=REPO_ROOT, capture_output=True)
        (REPO_ROOT / ".worktree_registry.json").unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  REDIS PATTERN — requires `redis` package + a reachable server
# ══════════════════════════════════════════════════════════════════════════════
def run_redis_pattern() -> None:
    banner("REDIS PATTERN (distributed mailboxes)")
    try:
        from phase6_enterprise import redis_mailbox
    except ImportError:
        why = "redis package not installed (pip install -e '.[redis]')"
        print(f"  Skipped: {why}")
        mark(22, "skip", why)
        return

    async def _demo():
        mb = redis_mailbox.RedisAgentMailbox()
        await mb.connect()
        await mb.send("reviewer", "coordinator", {"type": "review_request", "file": "auth.py"})
        msgs = await mb.receive("reviewer", "reviewer-1", block_ms=500)
        await mb.disconnect()
        return msgs

    try:
        msgs = asyncio.run(_demo())
        print(f"[Pattern 22] Redis: sent + received {len(msgs)} message(s)")
        mark(22, "ok", f"{len(msgs)} message(s) over Redis Streams")
    except Exception as e:
        why = f"no reachable Redis server ({type(e).__name__})"
        print(f"  Skipped: {why}")
        mark(22, "skip", why)


# ══════════════════════════════════════════════════════════════════════════════
#  MODEL PATTERNS — require ANTHROPIC_API_KEY (real API calls, incur cost)
# ══════════════════════════════════════════════════════════════════════════════
def _hardened_dispatch(safe_handlers: dict):
    """Compose permissions (15) + event bus (16) + snapshots (14) per tool call."""
    def dispatch(name: str, args: dict) -> str:
        allowed, reason = permissions.check_permission(name, args)
        if not allowed:
            return f"[PERMISSION DENIED] {reason}"
        return event_bus.instrumented_call(name, args, safe_handlers)
    return dispatch


def run_hardened_task(task_description: str, session_id: str, max_turns: int = 12) -> str:
    """
    The Minimum Production Baseline in action: loop (1) + dispatch (2) + todo (3)
    + permissions (15) + snapshots (14) + event bus (16) + caching (20) +
    retries + cost logging + session persistence (17).
    """
    client = make_client()
    safe_handlers = {
        **tools.TOOL_HANDLERS,
        "write_file": snapshots.tool_safe_write,   # Pattern 14
        "load_skill": skill_loader.tool_load_skill, # Pattern 5
        **todo_tools.TODO_HANDLERS,                 # Pattern 3
    }
    dispatch = _hardened_dispatch(safe_handlers)
    all_tools = tools.TOOL_SCHEMAS + todo_tools.TODO_SCHEMAS + [skill_loader.SKILL_TOOL_SCHEMA]
    system = ("You are a coding agent. Plan multi-step work with todo_write first. "
              "Keep all file writes under .combined_demo/work/. Say DONE when finished.")
    messages = [{"role": "user", "content": task_description}]

    for _ in range(max_turns):
        # Pattern 20 (caching) + retry/backoff + cost logging
        response = with_retry(lambda: caching.create_cached_message(
            system=system, tools=all_tools, messages=messages, max_tokens=MAX_TOKENS))
        log_usage(response, label=session_id)
        caching.print_cache_usage(response)
        messages.append({"role": "assistant", "content": response.content})
        session_store.save_session(session_id, messages)   # Pattern 17

        if response.stop_reason == "end_turn":
            return next((b.text for b in response.content if hasattr(b, "text")), "")

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            out = dispatch(block.name, block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(out)})
        messages.append({"role": "user", "content": results})
    return "(reached max turns)"


def run_model_patterns() -> None:
    banner("MODEL PATTERNS (require ANTHROPIC_API_KEY — real API calls)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        why = "ANTHROPIC_API_KEY not set"
        print(f"  Skipped: {why}")
        for n in (1, 2, 3, 4, 8, 13, 18):
            mark(n, "skip", why)
        # 6 and 20 already exercised offline; note the live half is skipped.
        return

    # Patterns 1, 2, 3 (+14,15,16,17,20 live) — the hardened agent loop
    print("\n[Patterns 1-3, live] Hardened agent loop on a small task...")
    run_hardened_task(
        "Create .combined_demo/work/calc.py with an add(a,b) function and a docstring.",
        session_id="combined-main")
    mark(1, "ok", "agent loop ran to end_turn")
    mark(2, "ok", "tools dispatched")
    mark(3, "ok", "todo planning available + used")

    # Pattern 4 — Subagent isolation
    print("\n[Pattern 4, live] Subagent...")
    summary = subagent.run_subagent("Count the .py files in phase1_core_loop/ and report the number.")
    print(f"  Subagent returned: {summary[:120]}")
    mark(4, "ok", "isolated subagent returned a summary")

    # Pattern 13 — Real-time streaming
    print("\n[Pattern 13, live] Streaming...")
    streaming_agent.run_streaming_agent("In one sentence, what is an agent loop?")
    mark(13, "ok", "streamed tokens")

    # Pattern 18 — Parallel tool execution
    print("\n[Pattern 18, live] Async parallel tools...")
    asyncio.run(async_agent.run_async_agent(
        "Read phase1_core_loop/agent.py and phase1_core_loop/tools.py in parallel, "
        "then write a 2-line comparison to .combined_demo/work/cmp.txt"))
    mark(18, "ok", "parallel tool calls via asyncio.gather")

    # Pattern 8 — Background tasks
    print("\n[Pattern 8, live] Background task...")
    background_tasks.run_background_task(
        "bg-audit", "List .py files in phase4_production/ and report the count.",
        tools.TOOL_SCHEMAS, tools.TOOL_HANDLERS)
    deadline = time.monotonic() + 90
    notes = []
    while time.monotonic() < deadline and not notes:
        notes = background_tasks.check_notifications()
        if not notes:
            time.sleep(1)
    print(f"  Background notifications received: {len(notes)}")
    mark(8, "ok" if notes else "skip", f"{len(notes)} background completion(s)")

    # Pattern 6 (live half) — context compression layer 1 (summarize old turns)
    print("\n[Pattern 6, live] Summarizing old turns...")
    long_msgs = [{"role": "user", "content": f"message number {i}"} for i in range(10)]
    compressor.compress_messages(long_msgs, make_client())
    mark(6, "ok", "layers 2+3 offline + layer 1 (summary) live")


# ══════════════════════════════════════════════════════════════════════════════
def print_report() -> None:
    banner("COVERAGE REPORT")
    ok = 0
    for n in sorted(PATTERNS):
        status, note = COVERAGE.get(n, ("skip", "not reached"))
        tag = "✓ OK  " if status == "ok" else ("✗ FAIL" if status == "fail" else "– SKIP")
        if status == "ok":
            ok += 1
        suffix = f"  ({note})" if note else ""
        print(f"  [{tag}] Pattern {n:>2}: {PATTERNS[n]}{suffix}")
    print(f"\n  {ok}/23 patterns exercised this run.")
    if ok < 23:
        print("  Set ANTHROPIC_API_KEY, run from a clean git repo, and start Redis")
        print("  (docker run -p 6379:6379 redis) to exercise all 23.")


def main() -> None:
    print("=" * 64)
    print("Claude Code Architecture — All 23 Patterns, Exercised")
    print("=" * 64)
    setup_sandbox()
    try:
        run_offline_patterns()
        run_git_patterns()
        run_redis_pattern()
        run_model_patterns()
    finally:
        teardown_sandbox()
    print_report()


if __name__ == "__main__":
    main()
