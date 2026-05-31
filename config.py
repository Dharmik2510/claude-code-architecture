"""
Shared configuration and production-resilience helpers.

The standalone pattern files (phase1_core_loop/agent.py, etc.) keep their
own constants inline so each one runs in isolation as a teaching example.
This module is the *production* counterpart: one place for the model name,
token budget, API-key resolution, retry/backoff, and cost logging — wired
into the end-to-end entry points (examples/, phase6_enterprise/combined_agent.py).

Import it after `pip install -e .`, or from any script that has the repo
root on its path.
"""
import os
import time
from typing import Callable, TypeVar

# ── Model + budget (single source of truth) ───────────────────────────────────
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", "8096"))

# ── Retry policy ───────────────────────────────────────────────────────────────
MAX_RETRIES = int(os.environ.get("CLAUDE_MAX_RETRIES", "5"))
BASE_DELAY_SECONDS = float(os.environ.get("CLAUDE_RETRY_BASE_DELAY", "1.0"))

T = TypeVar("T")


def get_api_key() -> str:
    """Resolve the API key, failing loudly with an actionable message."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Get one at "
            "https://console.anthropic.com/ and run:\n"
            "    export ANTHROPIC_API_KEY=sk-ant-..."
        )
    return key


def make_client():
    """Construct an Anthropic client with the resolved key."""
    from anthropic import Anthropic
    return Anthropic(api_key=get_api_key())


def with_retry(fn: Callable[[], T]) -> T:
    """
    Run `fn` with exponential backoff on transient API errors.

    The first thing that breaks a real agent is a rate limit or a dropped
    connection mid-task. A naive `while True` loop dies on the first 429.
    Wrap every model call in this.

        response = with_retry(lambda: client.messages.create(...))
    """
    # Import lazily so the module is usable without the SDK installed (tests).
    try:
        from anthropic import APIConnectionError, APIStatusError, RateLimitError
        transient = (APIConnectionError, RateLimitError)
    except Exception:  # pragma: no cover - SDK not installed
        transient = ()
        APIStatusError = ()  # type: ignore

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except transient as e:  # network blips, 429s
            last_error = e
        except APIStatusError as e:  # 5xx server errors are retryable; 4xx are not
            status = getattr(e, "status_code", None)
            if status is None or status < 500:
                raise
            last_error = e

        delay = BASE_DELAY_SECONDS * (2 ** attempt)
        print(f"  [retry] attempt {attempt + 1}/{MAX_RETRIES} failed; waiting {delay:.1f}s")
        time.sleep(delay)

    raise RuntimeError(f"Exceeded {MAX_RETRIES} retries") from last_error


def log_usage(response, label: str = "") -> None:
    """
    Print token usage from a response so cost is observable per turn.
    Production agents track this to a metrics backend; here we just print.
    """
    usage = getattr(response, "usage", None)
    if not usage:
        return
    parts = [
        f"in={getattr(usage, 'input_tokens', 0)}",
        f"out={getattr(usage, 'output_tokens', 0)}",
    ]
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    if cache_read or cache_write:
        parts.append(f"cache_read={cache_read}")
        parts.append(f"cache_write={cache_write}")
    prefix = f"[usage {label}] " if label else "[usage] "
    print("  " + prefix + " ".join(parts))
