"""
Phase 4 — Pattern 16: Event Bus and Lifecycle Hooks
Every tool call emits before/after/error events.
Add logging, metrics, or alerts without touching tool code.
"""
import time
from dataclasses import dataclass, field
from typing import Any, Callable
from datetime import datetime

@dataclass
class ToolEvent:
    event_type:  str          # "before_call" | "after_call" | "error"
    tool_name:   str
    tool_args:   dict
    result:      Any   = None
    error:       str   = None
    duration_ms: float = 0.0
    timestamp:   float = field(default_factory=time.time)


_handlers: dict[str, list[Callable]] = {}


def subscribe(event_type: str, handler: Callable[[ToolEvent], None]) -> None:
    _handlers.setdefault(event_type, []).append(handler)


def publish(event: ToolEvent) -> None:
    for h in _handlers.get(event.event_type, []):
        try: h(event)
        except Exception: pass
    for h in _handlers.get("*", []):
        try: h(event)
        except Exception: pass


def instrumented_call(
    tool_name: str,
    tool_args: dict,
    tool_handlers: dict,
) -> str:
    publish(ToolEvent("before_call", tool_name, tool_args))
    start = time.time()
    try:
        result   = tool_handlers[tool_name](tool_args)
        duration = (time.time() - start) * 1000
        publish(ToolEvent("after_call", tool_name, tool_args,
                          result=result, duration_ms=duration))
        return result
    except Exception as e:
        duration = (time.time() - start) * 1000
        publish(ToolEvent("error", tool_name, tool_args,
                          error=str(e), duration_ms=duration))
        return f"Error: {e}"


# ── Built-in subscribers ──────────────────────────────────────────────────────

def log_all_calls(event: ToolEvent) -> None:
    if event.event_type == "after_call":
        print(f"  [{event.duration_ms:>6.1f}ms] {event.tool_name}")


def alert_slow_calls(event: ToolEvent, threshold_ms: float = 5000) -> None:
    if event.event_type == "after_call" and event.duration_ms > threshold_ms:
        print(f"  [SLOW] {event.tool_name} took {event.duration_ms:.0f}ms")


def audit_writes(event: ToolEvent) -> None:
    if event.tool_name == "write_file" and event.event_type == "after_call":
        with open("audit.log", "a") as f:
            f.write(
                f"{datetime.utcnow().isoformat()} WRITE "
                f"{event.tool_args.get('path','?')}\n"
            )
